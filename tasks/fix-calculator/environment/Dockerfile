FROM python:3.12-slim

WORKDIR /workspace
COPY workspace/ .

# Store initial workspace checksum for verifier to detect if agent modified files.
# Generic name makes it less discoverable by LLM.
RUN find . -type f -exec sha256sum {} \; | sort | sha256sum | cut -d' ' -f1 > /var/lib/sha-hash.sha256
