"""Shared helper to resolve the project bucket a container belongs to.

Used by both docker_project_discovery.py and compose_status.py so the
priority chain is defined in a single place.
"""


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