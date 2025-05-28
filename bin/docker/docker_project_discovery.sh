#!/bin/bash

declare -A project_containers
declare -A project_states

while read -r id; do
  inspect=$(docker inspect "$id")
  name=$(echo "$inspect" | jq -r '.[0].Name' | sed 's/^\/\(.*\)/\1/')
  project=$(echo "$inspect" | jq -r '.[0].Config.Labels["com.docker.compose.project"] // "no-docker-compose-project"')
  state=$(echo "$inspect" | jq -r '.[0].State.Status')

  project_containers["$project"]+="{\"container\":\"$name\",\"state\":\"$state\"},"
  project_states["$project"]+="$state "
done < <(docker ps -a --format '{{.ID}}')

echo "["

first=true
for project in "${!project_containers[@]}"; do
  containers="[${project_containers[$project]}]"
  containers=$(echo "$containers" | sed 's/,\]$/\]/')

  states=(${project_states[$project]})
  all_running=true
  all_stopped=true

  for s in "${states[@]}"; do
    if [ "$s" != "running" ]; then
      all_running=false
    fi
    if [ "$s" == "running" ]; then
      all_stopped=false
    fi
  done

  if $all_running; then
    summary="running"
  elif $all_stopped; then
    summary="stopped"
  else
    summary="partial"
  fi

  if ! $first; then
    echo ","
  fi
  echo -n "{\"{#PROJECT}\":\"$project\",\"{#STATUS}\":\"$summary\"}"
  first=false
done

echo "]"
