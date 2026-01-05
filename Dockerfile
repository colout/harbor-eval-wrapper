# ---- stage 1: get a known-good docker CLI ----
FROM docker:27-cli AS dockercli

# ---- stage 2: build harbor into an isolated venv ----
FROM python:3.12-slim AS builder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir harbor

# ---- stage 3: runtime: python + harbor venv + docker cli ----
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      git ca-certificates bash \
 && rm -rf /var/lib/apt/lists/*

COPY --from=dockercli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=dockercli /usr/local/libexec/docker/cli-plugins /usr/local/libexec/docker/cli-plugins

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:/usr/local/bin:${PATH}"

# Add OpenCode config - litellm provider with openai-compatible SDK
RUN printf '\nmkdir -p ~/.config/opencode\ncat > ~/.config/opencode/config.json << EOF\n{"provider":{"litellm":{"npm":"@ai-sdk/openai-compatible","name":"LiteLLM","options":{"baseURL":"http://192.168.10.172:4000/v1","apiKey":"{env:OPENAI_API_KEY}"},"models":{"llama-cpp/model":{}}}}}\nEOF\n' \
    >> /opt/venv/lib/python3.12/site-packages/harbor/agents/installed/install-opencode.sh.j2

WORKDIR /work
ENTRYPOINT ["harbor"]
