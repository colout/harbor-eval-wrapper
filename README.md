# Harbor Eval Runner

Dockerized wrapper for running [Harbor](https://harborframework.com/) agent evaluations.

I run NixOS and don't want to fuss with host dependencies every time I try something new. Docker handles all Harbor deps so I can focus on writing evals.

## Setup

```bash
cp .env.example .env
# Edit .env with your OpenAI-compatible proxy settings
```

## Usage

```bash
./start.sh tasks/fix-calculator
```

Builds the `harbor-runner` image and runs the task.

## Structure

```
.
├── start.sh                  # Docker wrapper
├── Dockerfile                # Harbor + docker CLI
├── agents/
│   └── opencode_litellm.py   # Custom agent for OpenAI-compatible proxies
├── tasks/                    # Eval tasks (git-ignored)
└── jobs/                     # Results (git-ignored)
```

## Custom Agent

The built-in OpenCode agent uses OpenAI's `/requests` endpoint for tracking. This doesn't work with OpenAI-compatible proxies like LiteLLM, llama.cpp, or vLLM since they don't implement that endpoint.

`OpenCodeLiteLLM` works around this by using the `litellm` provider with `@ai-sdk/openai-compatible`. Model names use the format `litellm/<model-id>`.

## Harbor Task Format Primer

Harbor is the framework behind [Terminal-Bench 2.0](https://www.tbench.ai/news/announcement-2-0) for evaluating AI agents. Tasks follow this structure:

```
my-task/
├── task.toml           # Config: timeouts, resources, metadata
├── instruction.md      # What the agent sees
├── environment/
│   └── Dockerfile      # Container setup
├── tests/
│   └── test.sh         # Verifier - MUST write reward.txt
└── solution/
    └── solve.sh        # Oracle solution (optional)
```

The verifier script writes pass/fail to `/logs/verifier/reward.txt`:

```bash
if [ $? -eq 0 ]; then echo 1 > /logs/verifier/reward.txt; else echo 0 > /logs/verifier/reward.txt; fi
```

See the [official docs](https://harborframework.com/docs/task-format) for full spec.

## Tasks

Tasks are git-ignored to prevent contamination (ending up in future training sets). See `tasks/fix-calculator` for an example.

Results go to `./jobs/` (also git-ignored).
