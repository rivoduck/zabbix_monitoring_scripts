import subprocess
import json
import sys

def get_containers():
    result = subprocess.run(['docker', 'ps', '-a', '-q'], capture_output=True, text=True)
    return result.stdout.strip().splitlines()

def inspect_container(container_id):
    result = subprocess.run(['docker', 'inspect', container_id], capture_output=True, text=True)
    return json.loads(result.stdout)[0]

def main(project):
    found = False
    running = 0
    exited = 0
    other = 0

    for container_id in get_containers():
        container = inspect_container(container_id)
        labels = container.get('Config', {}).get('Labels', {})
        proj = labels.get('com.docker.compose.project', 'no-docker-compose-project')
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
