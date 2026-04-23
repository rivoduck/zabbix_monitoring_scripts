"""Shared helpers for Docker container discovery scripts.

Used by docker_project_discovery.py, compose_status.py and
compose_container_discovery.py so common logic is defined in a single place.
"""

import subprocess
import json


def inspect_container(container_id):
    result = subprocess.run(['docker', 'inspect', container_id],
                            capture_output=True, text=True)
    # Docker CLI itself can fail to inspect the container.
    # Prevent crashing in case of empty container data (e.g. a dead container).
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)[0]


def resolve_project(labels):
    """Resolve the project bucket a container belongs to.

    Priority order (first non-empty match wins):
      1. zabbix.docker.project      - opt-in custom label for explicit grouping
      2. com.docker.compose.project - Docker Compose default label
      3. com.docker.stack.namespace - Docker Swarm default label (stack name)
      4. 'no-docker-compose-project' - fallback bucket for unlabeled containers

    The custom label lets users override the auto-detected grouping,
    which is useful to split a project into logical sub-projects or
    to merge standalone containers under a shared bucket.

    Including the Swarm namespace makes the discovery work out of the
    box on Swarm nodes, where containers carry com.docker.stack.namespace
    instead of com.docker.compose.project.
    """
    return (
        labels.get('zabbix.docker.project')
        or labels.get('com.docker.compose.project')
        or labels.get('com.docker.stack.namespace')
        or 'no-docker-compose-project'
    )


def resolve_runtime(labels):
    """Detect the container runtime environment.

    Returns 'swarm', 'compose', or 'standalone'.
    Independent of resolve_project: runtime is about infrastructure,
    project is about grouping.
    """
    if labels.get('com.docker.stack.namespace'):
        return 'swarm'
    if labels.get('com.docker.compose.project'):
        return 'compose'
    return 'standalone'