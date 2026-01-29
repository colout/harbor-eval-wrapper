#!/usr/bin/env bash
TASK_PATH="${1:?Usage: ./test-task.sh <task-path>}"

docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$PWD:$PWD" \
  -w "$PWD" \
  harbor-runner run \
    -p "$PWD/$TASK_PATH" \
    -a oracle \
    -n 1 \
    -o "$PWD/jobs"
