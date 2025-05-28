import subprocess
import json
from collections import defaultdict

def get_container_ids():
    result = subprocess.run(['docker', 'ps', '-a', '--format', '{{.ID}}'],
                            capture_output=True, text=True)
    return result.stdout.strip().splitlines()

def inspect_container(container_id):
    result = subprocess.run(['docker', 'inspect', container_id],
                            capture_output=True, text=True)
    return json.loads(result.stdout)[0]

def main():
    project_states = defaultdict(list)

    for container_id in get_container_ids():
        container_data = inspect_container(container_id)
        name = container_data['Name'].lstrip('/')
        labels = container_data['Config'].get('Labels', {})
        project = labels.get('com.docker.compose.project', 'no-docker-compose-project')
        state = container_data['State']['Status']
        project_states[project].append(state)

    summary = []

    for project, states in project_states.items():
        all_running = all(state == 'running' for state in states)
        all_stopped = all(state != 'running' for state in states)

        if all_running:
            status = 'running'
        elif all_stopped:
            status = 'stopped'
        else:
            status = 'partial'

        summary.append({
            "{#PROJECT}": project,
            "{#STATUS}": status
        })

    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
