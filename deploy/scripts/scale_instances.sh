#!/bin/bash
# ================================================================================
# Scale Instances Script
# =======================
# 
# Manual instance scaling operations for the CFBC Django application.
# Works with both Docker Compose and Systemd deployments.
#
# Usage:
#   # Docker deployment
#   ./deploy/scripts/scale_instances.sh docker
#
#   # Systemd deployment
#   ./deploy/scripts/scale_instances.sh systemd
#
# Commands within each mode:
#   up        - Scale up by 1 instance
#   down      - Scale down by 1 instance
#   set N     - Scale to exactly N instances
#   status    - Show current instance status
#   restart   - Rolling restart of all instances
# ================================================================================

set -euo pipefail

# ── Constants ──────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
DOCKER_COMPOSE_FILE="$PROJECT_DIR/deploy/docker-compose.prod.yml"
NGINX_CONF="$PROJECT_DIR/deploy/nginx/nginx.conf"
UPSTREAM_NAME="django_backend"
MIN_INSTANCES=2
MAX_INSTANCES=8
BASE_PORT=8001
HEALTH_CHECK_RETRIES=10
HEALTH_CHECK_INTERVAL=5

# ── Colors ──────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ── Helper Functions ────────────────────────────────────────────────────────────

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ── Docker Operations ───────────────────────────────────────────────────────────

docker_get_current_instances() {
    docker ps --filter "name=cfbc-app" --format "{{.Names}}" 2>/dev/null | wc -l
}

docker_get_instance_ports() {
    docker ps --filter "name=cfbc-app" --format "{{.Names}}" 2>/dev/null | sort
}

docker_scale_instances() {
    local target=$1
    log_info "Scaling Docker Compose to $target instances..."

    docker compose -f "$DOCKER_COMPOSE_FILE" up -d --scale "app=$target" --no-recreate app

    if [ $? -ne 0 ]; then
        log_error "Docker scale command failed"
        return 1
    fi

    # Wait for all instances to become healthy
    log_info "Waiting for instances to become healthy..."
    for i in $(seq 1 "$target"); do
        local container="cfbc-app-$i"
        docker_await_healthy "$container"
    done

    docker_reload_nginx
    return 0
}

docker_await_healthy() {
    local container=$1
    for attempt in $(seq 1 $HEALTH_CHECK_RETRIES); do
        local status=$(docker inspect --format '{{.State.Health.Status}}' "$container" 2>/dev/null || echo "not_found")
        if [ "$status" = "healthy" ]; then
            log_success "$container is healthy"
            return 0
        elif [ "$status" = "not_found" ] && [ $attempt -gt 3 ]; then
            log_warn "$container not found yet (attempt $attempt)..."
        elif [ "$status" != "healthy" ] && [ $attempt -gt 3 ]; then
            log_warn "$container status: $status (attempt $attempt)..."
        fi
        sleep "$HEALTH_CHECK_INTERVAL"
    done
    log_warn "$container did not become healthy within $HEALTH_CHECK_RETRIES attempts"
    return 1
}

docker_reload_nginx() {
    log_info "Reloading Nginx..."
    if docker compose -f "$DOCKER_COMPOSE_FILE" exec -T nginx nginx -s reload 2>/dev/null; then
        log_success "Nginx reloaded"
    else
        log_warn "Nginx reload failed, you may need to reload manually"
    fi
}

docker_status() {
    echo ""
    log_info "Docker Compose Instance Status:"
    echo "========================================"
    docker compose -f "$DOCKER_COMPOSE_FILE" ps app
    echo ""
    log_info "Instance health details:"
    for i in $(seq 1 $MAX_INSTANCES); do
        local container="cfbc-app-$i"
        local status=$(docker inspect --format '{{.State.Health.Status}}' "$container" 2>/dev/null || echo "not_found")
        local created=$(docker inspect --format '{{.State.StartedAt}}' "$container" 2>/dev/null || echo "")
        if [ "$status" != "not_found" ]; then
            echo "  $container: $status (since $created)"
        fi
    done
    echo ""
    log_info "Instance count: $(docker_get_current_instances)"
}

docker_rolling_restart() {
    log_info "Starting rolling restart of Docker instances..."
    local current=$(docker_get_current_instances)
    for i in $(seq 1 "$current"); do
        local container="cfbc-app-$i"
        log_info "Restarting $container..."
        docker compose -f "$DOCKER_COMPOSE_FILE" up -d --force-recreate "app-$i" || true
        docker_await_healthy "$container"
        log_success "$container restarted"
    done
    log_success "Rolling restart complete"
}

# ── Systemd Operations ──────────────────────────────────────────────────────────

systemd_get_current_instances() {
    systemctl list-units --type=service --state=running 'cfbc@*' --no-legend 2>/dev/null | grep -c "cfbc@" || echo 0
}

systemd_scale_instances() {
    local target=$1
    local current=$(systemd_get_current_instances)

    log_info "Scaling Systemd to $target instances (currently $current)..."

    # Get running instance ports
    local running_ports=()
    for p in $(seq "$BASE_PORT" $((BASE_PORT + MAX_INSTANCES - 1))); do
        local svc="cfbc@$p"
        if systemctl is-active --quiet "$svc" 2>/dev/null; then
            running_ports+=("$p")
        fi
    done

    # Stop excess instances
    for port in "${running_ports[@]}"; do
        local port_num=$((port))
        if [ "$port_num" -gt $((BASE_PORT + target - 1)) ]; then
            log_info "Stopping cfbc@$port_num..."
            sudo systemctl stop "cfbc@$port_num" 2>/dev/null || true
            sudo systemctl disable "cfbc@$port_num" 2>/dev/null || true
            log_success "cfbc@$port_num stopped"
        fi
    done

    # Start missing instances
    for port_num in $(seq "$BASE_PORT" $((BASE_PORT + target - 1))); do
        local svc="cfbc@$port_num"
        if ! systemctl is-active --quiet "$svc" 2>/dev/null; then
            log_info "Starting $svc..."
            sudo systemctl enable "$svc" 2>/dev/null || true
            sudo systemctl start "$svc" 2>/dev/null || true
            systemd_await_healthy "$port_num"
            log_success "$svc started"
        fi
    done

    # Update Nginx upstream
    systemd_update_nginx_upstream "$target"

    return 0
}

systemd_await_healthy() {
    local port=$1
    for attempt in $(seq 1 $((HEALTH_CHECK_RETRIES * 2))); do
        local status=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$port/health/" 2>/dev/null || echo "000")
        if [ "$status" = "200" ]; then
            log_success "cfbc@$port is healthy"
            return 0
        fi
        sleep 3
    done
    log_warn "cfbc@$port did not become healthy within timeout"
    return 1
}

systemd_update_nginx_upstream() {
    local count=$1
    log_info "Updating Nginx upstream configuration for $count instances..."

    # Build new upstream block
    local upstream="    upstream $UPSTREAM_NAME {\n"
    upstream+="        ip_hash;\n"
    for i in $(seq 0 $((count - 1))); do
        local port=$((BASE_PORT + i))
        upstream+="        server 127.0.0.1:$port max_fails=3 fail_timeout=30s weight=1;\n"
    done
    upstream+="        keepalive 32;\n    }"

    # Replace upstream block in nginx.conf
    if [ -f "$NGINX_CONF" ]; then
        # Use sed to replace the upstream block
        sed -i "/^    upstream $UPSTREAM_NAME {/,/^    }/c\\$(echo -e "$upstream")" "$NGINX_CONF"

        # Test and reload nginx
        if sudo nginx -t 2>/dev/null; then
            sudo nginx -s reload 2>/dev/null || true
            log_success "Nginx configuration updated and reloaded"
        else
            log_error "Nginx configuration test failed"
            return 1
        fi
    fi
}

systemd_status() {
    echo ""
    log_info "Systemd Instance Status:"
    echo "========================================"
    echo ""
    printf "  %-20s %-12s %-12s %s\n" "SERVICE" "STATUS" "HEALTH" "PORT"
    printf "  %-20s %-12s %-12s %s\n" "-------" "------" "------" "----"
    for port in $(seq "$BASE_PORT" $((BASE_PORT + MAX_INSTANCES - 1))); do
        local svc="cfbc@$port"
        local active="inactive"
        if systemctl is-active --quiet "$svc" 2>/dev/null; then
            active="active"
        fi
        local health="unknown"
        if [ "$active" = "active" ]; then
            local status_code=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$port/health/" 2>/dev/null || echo "000")
            if [ "$status_code" = "200" ]; then
                health="healthy"
            else
                health="unhealthy ($status_code)"
            fi
        fi
        printf "  %-20s %-12s %-12s %s\n" "$svc" "$active" "$health" "$port"
    done
    echo ""
    log_info "Instance count: $(systemd_get_current_instances)"
}

systemd_rolling_restart() {
    local current=$(systemd_get_current_instances)
    log_info "Starting rolling restart of Systemd instances..."

    for port in $(seq "$BASE_PORT" $((BASE_PORT + current - 1))); do
        local svc="cfbc@$port"
        log_info "Restarting $svc..."
        sudo systemctl restart "$svc" 2>/dev/null || true
        systemd_await_healthy "$port"
        log_success "$svc restarted"
        sleep 3
    done
    log_success "Rolling restart complete"
}

# ── Main ────────────────────────────────────────────────────────────────────────

print_usage() {
    echo ""
    echo "Usage: $0 {docker|systemd} {up|down|set N|status|restart}"
    echo ""
    echo "Modes:"
    echo "  docker    - Docker Compose deployment"
    echo "  systemd   - Systemd deployment"
    echo ""
    echo "Commands:"
    echo "  up        - Scale up by 1 instance"
    echo "  down      - Scale down by 1 instance"
    echo "  set N     - Scale to exactly N instances"
    echo "  status    - Show current instance status"
    echo "  restart   - Rolling restart of all instances"
    echo ""
    echo "Examples:"
    echo "  $0 docker status"
    echo "  $0 docker up"
    echo "  $0 docker set 6"
    echo "  $0 systemd restart"
    echo ""
}

if [ $# -lt 2 ]; then
    print_usage
    exit 1
fi

MODE=$1
COMMAND=$2
TARGET=${3:-}

case $MODE in
    docker)
        case $COMMAND in
            status)
                docker_status
                ;;
            up)
                current=$(docker_get_current_instances)
                target=$((current + 1))
                if [ "$target" -gt "$MAX_INSTANCES" ]; then
                    log_warn "Cannot scale above $MAX_INSTANCES instances (currently $current)"
                    exit 1
                fi
                docker_scale_instances "$target"
                ;;
            down)
                current=$(docker_get_current_instances)
                target=$((current - 1))
                if [ "$target" -lt "$MIN_INSTANCES" ]; then
                    log_warn "Cannot scale below $MIN_INSTANCES instances (currently $current)"
                    exit 1
                fi
                docker_scale_instances "$target"
                ;;
            set)
                if [ -z "$TARGET" ]; then
                    log_error "Target number required. Usage: $0 docker set N"
                    exit 1
                fi
                if [ "$TARGET" -lt "$MIN_INSTANCES" ] || [ "$TARGET" -gt "$MAX_INSTANCES" ]; then
                    log_error "Target must be between $MIN_INSTANCES and $MAX_INSTANCES"
                    exit 1
                fi
                docker_scale_instances "$TARGET"
                ;;
            restart)
                docker_rolling_restart
                ;;
            *)
                log_error "Unknown command: $COMMAND"
                print_usage
                exit 1
                ;;
        esac
        ;;
    systemd)
        case $COMMAND in
            status)
                systemd_status
                ;;
            up)
                current=$(systemd_get_current_instances)
                target=$((current + 1))
                if [ "$target" -gt "$MAX_INSTANCES" ]; then
                    log_warn "Cannot scale above $MAX_INSTANCES instances (currently $current)"
                    exit 1
                fi
                systemd_scale_instances "$target"
                ;;
            down)
                current=$(systemd_get_current_instances)
                target=$((current - 1))
                if [ "$target" -lt "$MIN_INSTANCES" ]; then
                    log_warn "Cannot scale below $MIN_INSTANCES instances (currently $current)"
                    exit 1
                fi
                systemd_scale_instances "$target"
                ;;
            set)
                if [ -z "$TARGET" ]; then
                    log_error "Target number required. Usage: $0 systemd set N"
                    exit 1
                fi
                if [ "$TARGET" -lt "$MIN_INSTANCES" ] || [ "$TARGET" -gt "$MAX_INSTANCES" ]; then
                    log_error "Target must be between $MIN_INSTANCES and $MAX_INSTANCES"
                    exit 1
                fi
                systemd_scale_instances "$TARGET"
                ;;
            restart)
                systemd_rolling_restart
                ;;
            *)
                log_error "Unknown command: $COMMAND"
                print_usage
                exit 1
                ;;
        esac
        ;;
    *)
        log_error "Unknown mode: $MODE. Use 'docker' or 'systemd'."
        print_usage
        exit 1
        ;;
esac
