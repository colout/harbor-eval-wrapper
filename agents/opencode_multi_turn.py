import shlex
import yaml
from harbor.agents.installed.opencode import OpenCode
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class OpenCodeMultiTurn(OpenCode):
    @staticmethod
    def name() -> str:
        return "opencode-multi-turn"

    def parse_turns(self, instruction: str) -> list[dict]:
        if not instruction.strip().startswith("turns:"):
            return [{"prompt": instruction}]

        parsed = yaml.safe_load(instruction)
        if not isinstance(parsed, dict) or "turns" not in parsed:
            raise ValueError("Invalid multi-turn YAML: missing 'turns' key")

        turns = parsed["turns"]
        if not isinstance(turns, list) or len(turns) == 0:
            raise ValueError("Invalid multi-turn YAML: 'turns' must be a non-empty list")

        for i, turn in enumerate(turns):
            if not isinstance(turn, dict) or "prompt" not in turn:
                raise ValueError(f"Invalid turn {i}: must have 'prompt' key")

        return turns

    def create_opencode_command(self, prompt: str, is_continuation: bool) -> str:
        escaped = shlex.quote(prompt)
        continue_flag = " --continue" if is_continuation else ""
        return f"opencode --model {self.model_name} run{continue_flag} {escaped}"

    def get_run_env(self) -> dict[str, str]:
        return self.create_run_agent_commands("")[0].env

    async def setup_for_run(self, environment: BaseEnvironment) -> None:
        pass

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        turns = self.parse_turns(instruction)
        env = self.get_run_env()

        await self.setup_for_run(environment)

        for i, turn in enumerate(turns):
            turn_num = i + 1
            self.logger.info(f"Starting turn {turn_num}/{len(turns)}")

            cmd = self.create_opencode_command(turn["prompt"], is_continuation=(i > 0))
            full_cmd = f"{cmd} 2>&1 | tee /logs/agent/opencode-turn-{turn_num}.txt"

            command_dir = self.logs_dir / f"turn-{turn_num}"
            command_dir.mkdir(parents=True, exist_ok=True)
            (command_dir / "command.txt").write_text(full_cmd)

            result = await environment.exec(command=full_cmd, env=env)

            (command_dir / "return-code.txt").write_text(str(result.return_code))
            if result.stdout:
                (command_dir / "stdout.txt").write_text(result.stdout)
            if result.stderr:
                (command_dir / "stderr.txt").write_text(result.stderr)

            is_last_turn = i == len(turns) - 1
            if is_last_turn:
                self.logger.info(f"Turn {turn_num} complete (final turn, skipping tests)")
                continue

            self.logger.info(f"Turn {turn_num} complete, running phases 1-{turn_num}")

            passed = True
            for phase in range(1, turn_num + 1):
                phase_file = f"/usr/local/lib/.phase{phase}.pyc"
                result = await environment.exec(command=f"python3 {phase_file}")
                (command_dir / f"phase{phase}-return-code.txt").write_text(str(result.return_code))
                if result.stdout:
                    (command_dir / f"phase{phase}-stdout.txt").write_text(result.stdout)
                if result.return_code != 0:
                    passed = False
                    break

            if not passed:
                self.logger.info(f"Turn {turn_num} failed at phase {phase}, stopping")
                break

            self.logger.info(f"Turn {turn_num} passed")

        self.populate_context_post_run(context)
