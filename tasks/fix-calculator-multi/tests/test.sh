#!/bin/bash

# Compare current workspace to initial state
CURRENT=$(find /workspace -type f -exec sha256sum {} \; | sort | sha256sum | cut -d' ' -f1)
INITIAL=$(cat /var/lib/sha-hash.sha256)

if [ "$CURRENT" = "$INITIAL" ]; then
    ATTEMPTED=0
else
    ATTEMPTED=1
fi

REWARD=1

for f in /usr/local/lib/.phase*.pyc; do
    [ -f "$f" ] || continue
    if ! python3 "$f"; then
        REWARD=0
        break
    fi
done

echo $REWARD > /logs/verifier/reward.txt
echo "{\"attempted\": $ATTEMPTED}" > /logs/verifier/metrics.json
cp -r /workspace /logs/verifier/workspace
