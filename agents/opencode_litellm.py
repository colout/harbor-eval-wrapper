import json
import os
from agents.opencode_multi_turn import OpenCodeMultiTurn
from harbor.environments.base import BaseEnvironment


class OpenCodeLiteLLM(OpenCodeMultiTurn):
    @staticmethod
    def name() -> str:
        return "opencode-litellm"

    def _is_litellm(self) -> bool:
        if not self.model_name or "/" not in self.model_name:
            return False
        provider, _ = self.model_name.split("/", 1)
        return provider == "litellm"

    def _get_litellm_env(self) -> dict[str, str]:
        env = {"OPENCODE_FAKE_VCS": "git"}
        for key in ["OPENAI_API_KEY", "OPENAI_BASE_URL"]:
            if key in os.environ:
                env[key] = os.environ[key]
        return env

    def _get_litellm_config(self) -> dict:
        _, model_id = self.model_name.split("/", 1)
        env = self._get_litellm_env()
        return {
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

    def get_run_env(self) -> dict[str, str]:
        if self._is_litellm():
            return self._get_litellm_env()
        return super().get_run_env()

    async def setup_for_run(self, environment: BaseEnvironment) -> None:
        if not self._is_litellm():
            return

        config_json = json.dumps(self._get_litellm_config())
        setup_cmd = f"mkdir -p ~/.config/opencode && echo '{config_json}' > ~/.config/opencode/config.json"
        await environment.exec(command=setup_cmd, env=self._get_litellm_env())
