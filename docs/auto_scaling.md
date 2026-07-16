# Auto-Scaling Configuration

## Overview

This document describes the auto-scaling system for the CFBC Django application.
The system monitors application and system metrics to automatically adjust the
number of application instances based on demand.

### How It Works

```
                          ┌─────────────────────────────┐
                          │      Auto-Scaler (60s)      │
                          │                             │
     ┌────────────────────┤  ┌─────────┐  ┌──────────┐  ├──────────────────┐
     │                    │  │Metrics  │  │Policy    │  │                  │
     │                    │  │Collector│─▶│Engine    │─▶│                  │
     │                    │  └─────────┘  └────┬─────┘  │                  │
     │                    │                    │         │                  │
     │                    │           ┌────────▼──────┐  │                  │
     │                    │           │  Scale Event  │  │                  │
     │                    │           │  Logger       │  │                  │
     │                    │           └───────────────┘  │                  │
     │                    └─────────────────────────────┘                  │
     │                                                                     │
     ▼                                                                     ▼
┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐     ┌───────────┐
│Instance 1 │  │Instance 2 │  │Instance 3 │  │Instance 4 │ ... │Instance N │
│  :8001    │  │  :8002    │  │  :8003    │  │  :8004    │     │  :800N    │
└───────────┘  └───────────┘  └───────────┘  └───────────┘     └───────────┘
      │              │              │              │                │
      └──────────────┴──────────────┴──────────────┴────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │   Nginx Load        │
                          │   Balancer          │
                          │   (ip_hash)         │
                          └─────────────────────┘
```

### Scaling Architecture

The auto-scaling system consists of four main components:

1. **Metrics Collector** - Collects system and application metrics
2. **Policy Engine** - Evaluates metrics against configured thresholds
3. **Instance Manager** - Executes scaling actions (add/remove instances)
4. **Event Logger** - Records all scaling events for analysis

## Components

### 1. Auto-Scaler Module

**File**: `cfbc/autoscaler.py`

The core auto-scaling module provides:

| Class | Purpose |
|---|---|
| `MetricsCollector` | Collects CPU, memory, request rate, response times, queue depths |
| `ScalingPolicyEngine` | Evaluates metrics and determines scaling actions |
| `InstanceManager` | Manages Docker/Systemd instance lifecycle |
| `ScalingEventLogger` | Logs and persists scaling events |
| `AutoScaler` | Main orchestrator that ties everything together |

### 2. Management Command

**File**: `cfbc/management/commands/autoscale.py`

Run the auto-scaler via Django management command:

```bash
# Run a single evaluation
python manage.py autoscale --once

# Run continuously (every 60 seconds)
python manage.py autoscale --interval 60

# Check status
python manage.py autoscale --status

# Dry run (no actual scaling)
python manage.py autoscale --once --dry-run
```

### 3. Instance Scaling Script

**File**: `deploy/scripts/scale_instances.sh`

Manual instance management shell script:

```bash
# Docker deployment
./deploy/scripts/scale_instances.sh docker status
./deploy/scripts/scale_instances.sh docker up
./deploy/scripts/scale_instances.sh docker down
./deploy/scripts/scale_instances.sh docker set 6
./deploy/scripts/scale_instances.sh docker restart

# Systemd deployment
./deploy/scripts/scale_instances.sh systemd status
./deploy/scripts/scale_instances.sh systemd up
./deploy/scripts/scale_instances.sh systemd set 4
```

### 4. Nginx Upstream Updater

**File**: `deploy/scripts/update_nginx_upstream.py`

Python script to dynamically update Nginx upstream configuration:

```bash
# Update to 6 instances (Docker)
python deploy/scripts/update_nginx_upstream.py --count 6 --mode docker --reload

# Auto-detect and update
python deploy/scripts/update_nginx_upstream.py --auto --mode systemd --reload

# Dry run (preview changes)
python deploy/scripts/update_nginx_upstream.py --count 6 --dry-run
```

## Auto-Scaling Metrics

The system monitors the following metrics to make scaling decisions:

| Metric | Source | Scale Up Trigger | Scale Down Trigger |
|---|---|---|---|
| CPU Usage | `/proc/stat` or psutil | > 70% | < 30% |
| Memory Usage | `/proc/meminfo` or psutil | > 75% | < 40% |
| Request Rate | Nginx stub_status | > 50 req/s per instance | < 10 req/s per instance |
| P95 Response Time | Django middleware cache | > 1 second | < 0.3 seconds |
| Nginx Queue Depth | Nginx stub_status | > 10 waiting requests | < 3 waiting requests |
| Connection Pool | PostgreSQL `pg_stat_activity` | (Advisory) | (Advisory) |
| Celery Queue | Celery inspect | (Advisory) | (Advisory) |

### Decision Algorithm

The policy engine uses a weighted majority voting system:

1. Each metric is checked against its threshold
2. If the majority of metrics indicate a need to scale, the action is taken
3. Required: at least 3 out of 5 metrics must exceed their thresholds

This prevents flapping due to transient spikes in a single metric.

## Configuration

### Default Configuration

Auto-scaling configuration is defined in `DEFAULT_CONFIG` in `cfbc/autoscaler.py`:

```python
DEFAULT_CONFIG = {
    'min_instances': 2,
    'max_instances': 8,
    'scale_up_threshold_cpu': 70.0,           # CPU percentage
    'scale_down_threshold_cpu': 30.0,         # CPU percentage
    'scale_up_threshold_memory': 75.0,        # Memory percentage
    'scale_down_threshold_memory': 40.0,      # Memory percentage
    'scale_up_threshold_request_rate': 50.0,  # Request rate per instance
    'scale_down_threshold_request_rate': 10.0, # Request rate per instance
    'scale_up_threshold_response_time': 1.0,  # P95 response time (s)
    'scale_down_threshold_response_time': 0.3, # P95 response time (s)
    'scale_up_threshold_queue_depth': 10,     # Nginx queue depth
    'scale_down_threshold_queue_depth': 3,    # Nginx queue depth
    'cooldown_period_scale_up': 120,          # 2 minutes
    'cooldown_period_scale_down': 300,        # 5 minutes
    'scale_up_step': 1,                        # Instances per action
    'scale_down_step': 1,                      # Instances per action
    'deployment_mode': 'docker',               # 'docker' or 'systemd'
}
```

### Override in Django Settings

You can override any configuration in `cfbc/settings.py`:

```python
AUTOSCALER_CONFIG = {
    'min_instances': 4,
    'max_instances': 12,
    'scale_up_threshold_cpu': 80.0,
    'scale_up_threshold_memory': 80.0,
    'deployment_mode': 'docker',
    'cooldown_period_scale_up': 180,
    'cooldown_period_scale_down': 300,
    'docker_compose_file': 'deploy/docker-compose.prod.yml',
}
```

### CLI Override (Management Command)

```bash
python manage.py autoscale --interval 30 \
    --min-instances 2 \
    --max-instances 10 \
    --mode docker
```

## Cooldown Periods

Cooldown periods prevent the system from oscillating between scale-up and
scale-down actions:

| Action | Duration | Purpose |
|---|---|---|
| Scale Up Cooldown | 120 seconds | Wait for new instances to be healthy |
| Scale Down Cooldown | 300 seconds | Ensure sustained low load before removing instances |

The scale-down cooldown is intentionally longer than the scale-up cooldown to
prioritize availability over cost savings.

## Instance Lifecycle

### Docker Compose

```
Scale Up:                     Scale Down:
  1. docker compose scale       1. docker compose scale app=N-1
     app=N+1                    2. Wait for health checks
  2. Wait for health checks     3. Reload Nginx
  3. Reload Nginx
```

### Systemd

```
Scale Up:                     Scale Down:
  1. systemctl start cfbc@N    1. systemctl stop cfbc@N
  2. Wait for health check     2. systemctl disable cfbc@N
  3. Update Nginx upstream     3. Update Nginx upstream
  4. Reload Nginx              4. Reload Nginx
```

## Monitoring

### View Auto-Scaling Events

```bash
# Check auto-scaler status
python manage.py autoscale --status

# View event log file
tail -f logs/autoscale.log

# View metric history (via Django shell)
python manage.py shell -c "
from cfbc.autoscaler import create_default_scaler
scaler = create_default_scaler()
print(scaler.get_status())
"
```

### Cache Metrics

The auto-scaler stores metrics in Redis for monitoring dashboards:

- `autoscale:request_rate` - Current request rate
- `autoscale:avg_response_time` - Average response time
- `autoscale:p95_response_time` - P95 response time
- `autoscale:events:{YYYYMMDD}` - Daily event log

### Prometheus Integration

To add Prometheus metrics for auto-scaling:

1. Add a Prometheus exporter endpoint that reads from cache
2. Configure Grafana dashboard to display:
   - Instance count over time
   - Scaling events
   - Current metric values
   - Cooldown state

## Runbooks

### RB-AS-001: Auto-Scaler Not Running

**Symptoms**: Application performance is degrading but no scaling actions
are being taken.

**Verification**:
```bash
# Check if auto-scaler is running
python manage.py autoscale --status
```

**Resolution**:
```bash
# Start the auto-scaler
python manage.py autoscale --interval 60 &

# Or run as a systemd service (if configured)
sudo systemctl start cfbc-autoscaler
```

### RB-AS-002: Manual Override Needed

**Situation**: You need to manually adjust capacity (e.g., for a scheduled event).

**Actions**:
```bash
# Scale up manually before the event
./deploy/scripts/scale_instances.sh docker set 8

# Verify all instances are healthy
./deploy/scripts/scale_instances.sh docker status

# After the event, let auto-scaler return to normal
# or scale down manually
./deploy/scripts/scale_instances.sh docker set 4
```

### RB-AS-003: Throttling (Scaling Events Not Working)

**Symptoms**: System is under load but scaling actions are not being taken.

**Verification**:
```bash
# Check if cooldown is preventing scaling
python manage.py autoscale --status
# Look for: "Can scale up: False"
```

**Resolution**: Wait for cooldown to expire, or force scale manually:
```bash
# Force scale manually
./deploy/scripts/scale_instances.sh docker up
```

### RB-AS-004: Instance Health Check Failure

**Symptoms**: New instances are added but they don't become healthy.

**Verification**:
```bash
# Check individual instance health
docker ps --filter "name=cfbc-app" --format "table {{.Names}}\t{{.Status}}"

# Check health endpoint directly
curl -f http://127.0.0.1:8001/health/
```

**Resolution**:
```bash
# Restart the unhealthy instance
docker compose -f deploy/docker-compose.prod.yml restart app-1

# Or force-recreate
docker compose -f deploy/docker-compose.prod.yml up -d --force-recreate app-1
```

### RB-AS-005: Nginx Reload Failure After Scaling

**Symptoms**: Scale action reports success but new instances aren't receiving traffic.

**Verification**:
```bash
# Check Nginx upstream
curl http://127.0.0.1:8080/nginx_status

# Check Nginx error log
docker compose -f deploy/docker-compose.prod.yml logs nginx
```

**Resolution**:
```bash
# Reload Nginx manually
docker compose -f deploy/docker-compose.prod.yml exec nginx nginx -s reload

# Or restart Nginx entirely
docker compose -f deploy/docker-compose.prod.yml restart nginx
```

## Testing Auto-Scaling

### Test 1: Manual Scale Up/Down

```bash
# Verify current state
./deploy/scripts/scale_instances.sh docker status

# Scale up
./deploy/scripts/scale_instances.sh docker up

# Verify new instance is healthy
./deploy/scripts/scale_instances.sh docker status

# Scale down
./deploy/scripts/scale_instances.sh docker down

# Verify instance removed
./deploy/scripts/scale_instances.sh docker status
```

### Test 2: Auto-Scaler Evaluation (Dry Run)

```bash
# Run a single evaluation in dry-run mode
python manage.py autoscale --once --dry-run

# Review what would be done
```

### Test 3: Auto-Scaler Continuous Mode

```bash
# Run for a few minutes
timeout 300 python manage.py autoscale --interval 30

# Check what happened
python manage.py autoscale --status
```

### Test 4: Load Testing with Simulated Load

```bash
# Install wrk for load testing
sudo apt-get install wrk

# Generate load on the application
wrk -t4 -c100 -d60s http://localhost/

# While the load test is running, check auto-scaler decisions
python manage.py autoscale --once

# Or watch the auto-scaler in action
python manage.py autoscale --interval 30
```

## Operation Procedures

### Starting the Auto-Scaler

```bash
# Option 1: Run in foreground (screen/tmux)
screen -S autoscaler
python manage.py autoscale --interval 60

# Option 2: Run as background process
nohup python manage.py autoscale --interval 60 > logs/autoscale-daemon.log 2>&1 &

# Option 3: Run as Celery periodic task (recommended for production)
# 1. Add a periodic task via django-celery-beat admin
# 2. Task: cfbc.autoscaler.evaluate_and_scale
# 3. Interval: Every 60 seconds
```

### Stopping the Auto-Scaler

```bash
# If running in foreground, press Ctrl+C

# If running as background process
kill $(pgrep -f "manage.py autoscale")

# Systemd service
sudo systemctl stop cfbc-autoscaler
```

### Maintenance Mode

Before performing maintenance that might affect instance health:

```bash
# 1. Stop the auto-scaler
pkill -f "manage.py autoscale"

# 2. Perform maintenance...

# 3. Restart auto-scaler
python manage.py autoscale --interval 60 &
```

## Verification Checklist

After configuring auto-scaling, verify:

- [ ] Auto-scaler can be started via management command
- [ ] `python manage.py autoscale --status` shows correct configuration
- [ ] Manual scaling works (`scale_instances.sh docker set N`)
- [ ] Nginx upstream updates correctly after scaling
- [ ] New instances pass health checks
- [ ] Auto-scaler dry run shows correct decisions
- [ ] Events are logged to `logs/autoscale.log`
- [ ] Cooldown periods are enforced
- [ ] `scale_instances.sh docker restart` performs rolling restart
- [ ] Scale back to minimum and verify application still works
