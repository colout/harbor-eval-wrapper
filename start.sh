#!/usr/bin/env bash
TASK_PATH="${1:?Usage: ./start.sh <task-path>}"

set -a
source .env
set +a

docker build -t harbor-runner .

docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$PWD:$PWD" \
  -w "$PWD" \
  -e OPENAI_API_KEY \
  -e OPENAI_BASE_URL \
  harbor-runner run \
    -p "$PWD/$TASK_PATH" \
    --agent-import-path agents.opencode_litellm:OpenCodeLiteLLM \
    -m "$MODEL" \
    -n 1 \
    -k 1 \
    -o "$PWD/jobs"
