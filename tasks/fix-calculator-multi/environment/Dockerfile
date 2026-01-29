FROM python:3.12-slim

WORKDIR /workspace
COPY workspace/ .

RUN find . -type f -exec sha256sum {} \; | sort | sha256sum | cut -d' ' -f1 > /var/lib/sha-hash.sha256

COPY tests/ /tmp/tests/
RUN for f in /tmp/tests/_phase*.py; do \
      [ -f "$f" ] || continue; \
      python3 -m py_compile "$f" && \
      name=$(basename "$f" .py) && \
      mv /tmp/tests/__pycache__/${name}.cpython-*.pyc /usr/local/lib/.${name#_}.pyc; \
    done && \
    rm -rf /tmp/tests/
