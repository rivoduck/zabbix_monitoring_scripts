#!/bin/bash

docker ps -a --format '{{.ID}}' | while read -r id; do
  inspect=$(docker inspect "$id")
  name=$(echo "$inspect" | jq -r '.[0].Name' | sed 's/^\/\(.*\)/\1/')
  project=$(echo "$inspect" | jq -r '.[0].Config.Labels["com.docker.compose.project"] // "no-docker-compose-project"')
  state=$(echo "$inspect" | jq -r '.[0].State.Status')

  if [ -n "$project" ]; then
    echo "{\"{#PROJECT}\":\"$project\",\"{#CONTAINER}\":\"$name\",\"{#STATE}\":\"$state\"}"
  fi
done | jq -s '{data: .}'
