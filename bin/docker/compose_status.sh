#!/bin/bash

project="$1"

docker inspect $(docker ps -a --format '{{.Names}}') |
  jq --arg project "$project" '
    map(select(.Config.Labels["com.docker.compose.project"] == $project))
    | map(.State.Status)
    | if length == 0 then
        "unknown"
      elif all(. == "running") then
        "running"
      elif all(. == "exited") then
        "stopped"
      else
        "partial"
      end'
