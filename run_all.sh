#!/usr/bin/env bash

set -a
source .env
set +a

MODELS=$(curl -s "$OPENAI_BASE_URL/models" -H "Authorization: Bearer $OPENAI_API_KEY" | python3 -c "import sys,json; print(','.join('litellm/' + m['id'] for m in json.load(sys.stdin)['data'] if m['id'].startswith('llama-cpp/') and m['id'] != 'llama-cpp/*'))")

./start.sh "$@" -m "${MODELS%,}"
