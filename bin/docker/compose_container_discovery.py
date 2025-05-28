import subprocess
import json

def get_container_ids():
    result = subprocess.run(['docker', 'ps', '-a', '--format', '{{.ID}}'],
                            capture_output=True, text=True)
    return result.stdout.strip().splitlines()

def inspect_container(container_id):
    result = subprocess.run(['docker', 'inspect', container_id],
                            capture_output=True, text=True)
    return json.loads(result.stdout)[0]

def extract_info(container_data):
    name = container_data['Name'].lstrip('/')
    labels = container_data['Config'].get('Labels', {})
    project = labels.get('com.docker.compose.project', 'No project')

    state = container_data['State']['Status']
    health_info = container_data['State'].get('Health', {})
    health_status = health_info.get('Status')


    if state == "running" and health_status:
        state = health_status

    return {
        "{#PROJECT}": project,
        "{#CONTAINER}": name,
        "{#STATE}": state
    }

def main():
    containers_info = []
    for container_id in get_container_ids():
        container_data = inspect_container(container_id)
        info = extract_info(container_data)
        containers_info.append(info)

    print(json.dumps({"data": containers_info}, indent=2))

if __name__ == "__main__":
    main()
