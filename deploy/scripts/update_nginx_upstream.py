#!/usr/bin/env python3
"""
Update Nginx Upstream Configuration
=====================================

Dynamically updates the Nginx upstream block to include the specified
number of application instances. Supports both Docker Compose and
Systemd deployment modes.

Usage:
    # Update to 6 instances
    python deploy/scripts/update_nginx_upstream.py --count 6 --mode docker

    # Update to 4 instances (systemd)
    python deploy/scripts/update_nginx_upstream.py --count 4 --mode systemd

    # Test mode (show changes without applying)
    python deploy/scripts/update_nginx_upstream.py --count 6 --dry-run

    # Auto-detect current instances and update config
    python deploy/scripts/update_nginx_upstream.py --auto
"""

import os
import re
import sys
import argparse
import subprocess
from pathlib import Path


# ── Constants ──────────────────────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
NGINX_CONF = PROJECT_DIR / 'deploy' / 'nginx' / 'nginx.conf'
UPSTREAM_NAME = 'django_backend'
BASE_PORT = 8001


# ── Nginx Config Manipulation ──────────────────────────────────────────────────

def read_nginx_config() -> str:
    """Read the current Nginx configuration."""
    with open(NGINX_CONF, 'r') as f:
        return f.read()


def write_nginx_config(content: str):
    """Write the Nginx configuration."""
    with open(NGINX_CONF, 'w') as f:
        f.write(content)


def build_upstream_block(instance_count: int, mode: str = 'docker') -> str:
    """
    Build an Nginx upstream block with the specified number of instances.

    Args:
        instance_count: Number of application instances
        mode: 'docker' or 'systemd'

    Returns:
        Nginx upstream block as a string
    """
    lines = [f'    upstream {UPSTREAM_NAME} {{']
    lines.append('        ip_hash;')

    if mode == 'docker':
        # Docker Compose: instances are named cfbc-app-1, cfbc-app-2, etc.
        for i in range(1, instance_count + 1):
            lines.append(
                f'        server app-{i}:8000 '
                f'max_fails=3 fail_timeout=30s weight=1;'
            )
    else:
        # Systemd: instances are on localhost with ports 8001, 8002, etc.
        for i in range(instance_count):
            port = BASE_PORT + i
            lines.append(
                f'        server 127.0.0.1:{port} '
                f'max_fails=3 fail_timeout=30s weight=1;'
            )

    lines.append('        keepalive 32;')
    lines.append('    }')
    return '\n'.join(lines) + '\n'


def update_upstream_block(content: str, upstream_block: str) -> str:
    """
    Replace the existing upstream block in the Nginx config.

    Args:
        content: Current Nginx config content
        upstream_block: New upstream block

    Returns:
        Updated Nginx config content
    """
    pattern = rf'    upstream {re.escape(UPSTREAM_NAME)} \{{.*?\n    \}}'
    replacement = upstream_block.rstrip('\n')
    new_content = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)

    if new_content == content:
        raise ValueError(f"Could not find upstream block '{UPSTREAM_NAME}' in {NGINX_CONF}")

    return new_content


def get_current_instance_count_from_config(content: str) -> int:
    """Parse the current instance count from the Nginx config."""
    pattern = rf'upstream {re.escape(UPSTREAM_NAME)} \{{(.*?)\}}'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        # Count lines with 'server' directive
        server_lines = re.findall(r'server\s+\S+', match.group(1))
        return len(server_lines)
    return 0


def get_current_instance_count_from_docker() -> int:
    """Get current instance count from Docker."""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=cfbc-app', '--format', '{{.Names}}'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            names = [n for n in result.stdout.strip().split('\n') if n]
            return len(names)
    except Exception:
        pass
    return 0


def get_current_instance_count_from_systemd() -> int:
    """Get current instance count from Systemd."""
    try:
        result = subprocess.run(
            ['systemctl', 'list-units', '--type=service', '--state=running',
             'cfbc@*', '--no-legend'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            services = [l for l in result.stdout.strip().split('\n') if l]
            return len(services)
    except Exception:
        pass
    return 0


def reload_nginx(mode: str = 'systemd') -> bool:
    """Reload Nginx configuration."""
    try:
        if mode == 'docker':
            compose_file = PROJECT_DIR / 'deploy' / 'docker-compose.prod.yml'
            result = subprocess.run(
                ['docker', 'compose', '-f', str(compose_file),
                 'exec', '-T', 'nginx', 'nginx', '-s', 'reload'],
                capture_output=True, text=True, timeout=15
            )
        else:
            result = subprocess.run(
                ['sudo', 'nginx', '-s', 'reload'],
                capture_output=True, text=True, timeout=10
            )
        return result.returncode == 0
    except Exception as e:
        print(f"  Error reloading Nginx: {e}", file=sys.stderr)
        return False


def test_nginx_config() -> bool:
    """Test Nginx configuration."""
    try:
        result = subprocess.run(
            ['sudo', 'nginx', '-t'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return True
        else:
            print(f"  Nginx test failed: {result.stderr}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"  Error testing Nginx: {e}", file=sys.stderr)
        return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Update Nginx upstream configuration for CFBC app instances'
    )
    parser.add_argument(
        '--count', '-c',
        type=int,
        help='Number of application instances'
    )
    parser.add_argument(
        '--mode', '-m',
        choices=['docker', 'systemd'],
        default='systemd',
        help='Deployment mode (default: systemd)'
    )
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Auto-detect current instance count'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show changes without applying'
    )
    parser.add_argument(
        '--reload',
        action='store_true',
        help='Reload Nginx after update'
    )

    args = parser.parse_args()

    # Determine instance count
    if args.auto:
        if args.mode == 'docker':
            count = get_current_instance_count_from_docker()
        else:
            count = get_current_instance_count_from_systemd()
        if count == 0:
            print("Could not auto-detect instance count. Is the application running?")
            sys.exit(1)
        print(f"Auto-detected {count} running instances")
    elif args.count:
        count = args.count
    else:
        print("Error: --count or --auto is required")
        sys.exit(1)

    # Read current config
    content = read_nginx_config()
    current_count = get_current_instance_count_from_config(content)
    
    print(f"Current instances in Nginx config: {current_count}")
    print(f"Target instances: {count}")

    if current_count == count:
        print(f"Nginx config already has {count} instances. No changes needed.")
        # Still offer to reload
        if args.reload:
            if reload_nginx(args.mode):
                print("Nginx reloaded successfully.")
            else:
                print("Nginx reload failed.")
        return

    # Build new upstream block
    new_block = build_upstream_block(count, args.mode)

    if args.dry_run:
        print("\n[DRY RUN] Would replace upstream block with:")
        print("-" * 50)
        print(new_block)
        print("-" * 50)
        print("No changes applied.")
        return

    # Update config
    try:
        new_content = update_upstream_block(content, new_block)
        write_nginx_config(new_content)
        print(f"Nginx config updated: {current_count} → {count} instances")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Test configuration
    print("Testing Nginx configuration...")
    if not test_nginx_config():
        print("Configuration test FAILED! Rolling back...")
        write_nginx_config(content)
        sys.exit(1)

    # Reload if requested
    if args.reload:
        if reload_nginx(args.mode):
            print("Nginx reloaded successfully.")
        else:
            print("Failed to reload Nginx. You may need to reload manually:")
            if args.mode == 'docker':
                print(f"  docker compose -f deploy/docker-compose.prod.yml exec nginx nginx -s reload")
            else:
                print("  sudo nginx -s reload")

    print("Done.")


if __name__ == '__main__':
    main()
