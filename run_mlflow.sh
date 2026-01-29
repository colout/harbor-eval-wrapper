#!/usr/bin/env bash

set -a
source .env
set +a

usage() { echo "Usage: ./run_mlflow.sh -t <task-path> -m <model> [-k <attempts>]" >&2; exit 1; }

while getopts "t:m:k:" opt; do
  case $opt in
    t) TASK_PATH="$OPTARG" ;;
    m) MODEL="$OPTARG" ;;
    k) ATTEMPTS="$OPTARG" ;;
    *) usage ;;
  esac
done

[[ -z "$TASK_PATH" || -z "$MODEL" ]] && usage

docker build -t harbor-runner .

docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$PWD:$PWD" \
  -w "$PWD" \
  -e OPENAI_API_KEY \
  -e OPENAI_BASE_URL \
  --entrypoint python \
  harbor-runner \
  run_eval.py "$TASK_PATH" "$MODEL" "${ATTEMPTS:-1}"
