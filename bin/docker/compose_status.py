import subprocess
import json
import sys

from project_grouping import resolve_project, inspect_container


def get_containers():
    result = subprocess.run(['docker', 'ps', '-a', '-q'], capture_output=True, text=True)
    return result.stdout.strip().splitlines()

def main(project):
    found = False
    running = 0
    exited = 0
    other = 0

    for container_id in get_containers():
        container = inspect_container(container_id)
        if container is None:
            continue
        labels = container.get('Config', {}).get('Labels', {})
        # Use priority chain: custom label > compose project > fallback bucket.
        proj = resolve_project(labels)
        state = container.get('State', {}).get('Status', 'unknown')

        if proj == project:
            found = True
            if state == 'running':
                running += 1
            elif state == 'exited':
                exited += 1
            else:
                other += 1

    if not found:
        print("unknown")
    elif running > 0 and exited == 0 and other == 0:
        print("running")
    elif exited > 0 and running == 0 and other == 0:
        print("stopped")
    else:
        print("partial")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 compose_status.py <project_name>")
        sys.exit(1)
    main(sys.argv[1])
