import json
import os
import shlex
from harbor.agents.installed.opencode import OpenCode
from harbor.agents.installed.base import ExecInput


class OpenCodeLiteLLM(OpenCode):
    @staticmethod
    def name() -> str:
        return "opencode-litellm"

    def create_run_agent_commands(self, instruction: str) -> list[ExecInput]:
        provider, model_id = self.model_name.split("/", 1)

        if provider != "litellm":
            return super().create_run_agent_commands(instruction)

        escaped_instruction = shlex.quote(instruction)
        env = {"OPENCODE_FAKE_VCS": "git"}

        for key in ["OPENAI_API_KEY", "OPENAI_BASE_URL"]:
            if key in os.environ:
                env[key] = os.environ[key]

        config = {
            "provider": {
                "litellm": {
                    "npm": "@ai-sdk/openai-compatible",
                    "name": "LiteLLM",
                    "options": {
                        "baseURL": env.get("OPENAI_BASE_URL", "http://localhost:4000/v1"),
                        "apiKey": env.get("OPENAI_API_KEY", ""),
                    },
                    "models": {
                        model_id: {"name": model_id}
                    }
                }
            }
        }
        config_json = json.dumps(config)
        setup_cmd = f"mkdir -p ~/.config/opencode && echo '{config_json}' > ~/.config/opencode/config.json"

        return [ExecInput(
            command=f"{setup_cmd} && opencode --model {self.model_name} run {escaped_instruction} 2>&1 | tee /logs/agent/opencode.txt",
            env=env,
        )]
