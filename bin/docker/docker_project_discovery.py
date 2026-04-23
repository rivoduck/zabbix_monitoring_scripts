import subprocess
import json
from collections import defaultdict

from project_grouping import resolve_project, resolve_runtime, inspect_container


def get_container_ids():
    result = subprocess.run(['docker', 'ps', '-a', '--format', '{{.ID}}'],
                            capture_output=True, text=True)
    return result.stdout.strip().splitlines()

def main():
    project_states = defaultdict(list)
    project_runtime = {}

    for container_id in get_container_ids():
        container_data = inspect_container(container_id)
        if container_data is None:
            continue
        labels = container_data['Config'].get('Labels', {})
        project = resolve_project(labels)
        state = container_data['State']['Status']
        project_states[project].append(state)
        if project not in project_runtime:
            project_runtime[project] = resolve_runtime(labels)

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
            "{#STATUS}": status,
            "{#RUNTIME}": project_runtime[project]
        })

    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
