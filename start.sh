#!/usr/bin/env bash

usage() { echo "Usage: ./start.sh -t <task-path> [-m <model1,model2,...>]" >&2; exit 1; }

while getopts "t:m:" opt; do
  case $opt in
    t) TASK_PATH="$OPTARG" ;;
    m) MODELS_ARG="$OPTARG" ;;
    *) usage ;;
  esac
done

[[ -z "$TASK_PATH" ]] && usage

set -a
source .env
set +a

docker build -t harbor-runner .

IFS=',' read -ra MODELS <<< "${MODELS_ARG:-$MODEL}"

for model in "${MODELS[@]}"; do
  echo "Running with model: $model"
  docker run --rm \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$PWD:$PWD" \
    -w "$PWD" \
    -e OPENAI_API_KEY \
    -e OPENAI_BASE_URL \
    harbor-runner run \
      -p "$PWD/$TASK_PATH" \
      --agent-import-path agents.opencode_litellm:OpenCodeLiteLLM \
      -m "$model" \
      -n 1 \
      -k 1 \
      -o "$PWD/jobs"
done
