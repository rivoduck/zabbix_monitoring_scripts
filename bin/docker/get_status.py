#!/usr/bin/env python3
import subprocess
import json
import sys

def get_container_status(container_name):
    result = subprocess.run(
        ['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{json .}}'],
        capture_output=True, text=True
    )
    if not result.stdout.strip():
        return "not found"

    container_info = json.loads(result.stdout.strip())
    status_str = container_info['Status'].lower()

    if 'up' in status_str:
        if 'healthy' in status_str:
            return 'healthy'
        elif 'unhealthy' in status_str:
            return 'unhealthy'
        else:
            return 'running'
    elif 'exited' in status_str:
        return 'exited'
    elif 'created' in status_str:
        return 'created'
    elif 'restarting' in status_str:
        return 'restarting'
    else:
        return 'unknown'

if __name__ == "__main__":
    container_name = sys.argv[1]
    print(get_container_status(container_name))
