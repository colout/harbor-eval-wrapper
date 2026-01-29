#!/usr/bin/env python3
"""Harbor + MLflow integration using native Python API."""

import asyncio
import json
import subprocess
from datetime import datetime
from pathlib import Path

import mlflow
from dotenv import load_dotenv

from harbor import Job
from harbor.models.job.config import JobConfig

load_dotenv()

mlflow.set_tracking_uri("http://192.168.10.172:5001")

JOBS_DIR = Path("./jobs")


def compute_workspace_diff(original: Path, modified: Path) -> str:
    if not original.exists() or not modified.exists():
        return ""
    result = subprocess.run(
        ["diff", "-ruN", str(original), str(modified)],
        capture_output=True,
        text=True,
    )
    return result.stdout


def log_trial_artifacts(task_name: str, trial_dir: Path, trial_index: int):
    prefix = f"{task_name}/trial_{trial_index}"

    for name in ["trial.log", "config.json", "result.json"]:
        if (trial_dir / name).exists():
            mlflow.log_artifact(str(trial_dir / name), prefix)

    for subdir in ["agent", "verifier"]:
        subdir_path = trial_dir / subdir
        if subdir_path.exists():
            mlflow.log_artifacts(str(subdir_path), f"{prefix}/{subdir}")


def is_task_dir(path: Path) -> bool:
    return (path / "instruction.md").exists() or (path / "task.toml").exists()


def find_tasks(path: Path) -> list[Path]:
    if is_task_dir(path):
        return [path]
    return sorted([d for d in path.iterdir() if d.is_dir() and is_task_dir(d)])


def load_trial_results(job_dir: Path) -> list[dict]:
    results = []
    for subdir in job_dir.iterdir():
        if subdir.is_dir():
            result_file = subdir / "result.json"
            if result_file.exists():
                results.append(json.loads(result_file.read_text()))
    return results


async def run_single_task(task_path: Path, model: str, n_attempts: int = 1):
    task_name = task_path.name
    agent_model = f"litellm/llama-cpp/{model}"

    with mlflow.start_span(name=task_name) as task_span:
        task_span.set_inputs({"task": task_name, "model": model, "n_attempts": n_attempts})

        config = JobConfig(
            jobs_dir=JOBS_DIR,
            n_attempts=n_attempts,
            orchestrator={
                "type": "local",
                "n_concurrent_trials": 1,
                "retry": {"max_retries": 0},
            },
            environment={"type": "docker"},
            verifier={},
            agents=[
                {
                    "import_path": "agents.opencode_litellm:OpenCodeLiteLLM",
                    "model_name": agent_model,
                }
            ],
            tasks=[{"path": task_path.resolve()}],
        )

        job = Job(config)
        result = await job.run()

        job_dir = JOBS_DIR / config.job_name
        trial_results = load_trial_results(job_dir)

        task_rewards = []
        task_durations = []
        task_attempted = []

        for i, trial in enumerate(trial_results):
            with mlflow.start_span(name=f"trial_{i}") as trial_span:
                verifier_result = trial.get("verifier_result") or {}
                rewards_dict = verifier_result.get("rewards") or {}
                reward = rewards_dict.get("reward", 0.0)
                task_rewards.append(reward)

                trial_uri = trial.get("trial_uri", "")
                trial_dir = Path(trial_uri.replace("file://", ""))
                metrics_file = trial_dir / "verifier" / "metrics.json"
                attempted = 1
                if metrics_file.exists():
                    metrics = json.loads(metrics_file.read_text())
                    attempted = metrics.get("attempted", 1)
                task_attempted.append(attempted)

                agent_exec = trial.get("agent_execution") or {}
                duration = None
                if agent_exec.get("started_at") and agent_exec.get("finished_at"):
                    start = datetime.fromisoformat(agent_exec["started_at"])
                    end = datetime.fromisoformat(agent_exec["finished_at"])
                    duration = (end - start).total_seconds()
                    task_durations.append(duration)

                trial_span.set_inputs({"trial_index": i})
                trial_span.set_outputs({"reward": reward, "attempted": attempted, "duration_sec": duration})
                trial_span.set_attributes({
                    "verifier_stdout": verifier_result.get("stdout", ""),
                    "verifier_stderr": verifier_result.get("stderr", ""),
                    "agent_exit_code": agent_exec.get("exit_code"),
                })

                if trial_dir.exists():
                    log_trial_artifacts(task_name, trial_dir, i)

                    original = task_path / "environment" / "workspace"
                    modified = trial_dir / "verifier" / "workspace"
                    diff_output = compute_workspace_diff(original, modified)
                    if diff_output:
                        diff_file = trial_dir / "workspace.diff.txt"
                        diff_file.write_text(diff_output)
                        mlflow.log_artifact(str(diff_file), f"{task_name}/trial_{i}")

        task_span.set_outputs({
            "mean_reward": sum(task_rewards) / len(task_rewards) if task_rewards else 0,
            "pass_rate": sum(1 for r in task_rewards if r == 1.0) / len(task_rewards) if task_rewards else 0,
            "attempt_rate": sum(task_attempted) / len(task_attempted) if task_attempted else 0,
            "mean_duration_sec": sum(task_durations) / len(task_durations) if task_durations else 0,
        })

    return {"rewards": task_rewards, "durations": task_durations, "attempted": task_attempted, "n_trials": result.n_total_trials}


async def run_eval(task_path: str, model: str, n_attempts: int = 1):
    tasks = find_tasks(Path(task_path))
    if not tasks:
        print(f"No tasks found in {task_path}")
        return

    print(f"Found {len(tasks)} task(s): {[t.name for t in tasks]}")

    experiment = mlflow.get_experiment_by_name(model)
    if experiment is None:
        mlflow.create_experiment(model, tags={"mlflow.experimentType": "LLMOPS"})
    mlflow.set_experiment(model)

    with mlflow.start_run(run_name=f"{datetime.now():%Y%m%d_%H%M%S}"):
        mlflow.log_param("model", model)
        mlflow.log_param("n_attempts", n_attempts)
        mlflow.log_param("tasks", [t.name for t in tasks])

        all_rewards = []
        all_durations = []
        all_attempted = []
        total_trials = 0

        for task in tasks:
            print(f"\n{'='*60}\nRunning: {task.name}\n{'='*60}")
            result = await run_single_task(task, model, n_attempts)
            all_rewards.extend(result["rewards"])
            all_durations.extend(result["durations"])
            all_attempted.extend(result["attempted"])
            total_trials += result["n_trials"]

        mlflow.log_metric("system/n_trials", total_trials)
        mlflow.log_metric("system/n_tasks", len(tasks))

        if all_rewards:
            mlflow.log_metric("model/mean_reward", sum(all_rewards) / len(all_rewards))
            mlflow.log_metric("model/max_reward", max(all_rewards))
            mlflow.log_metric("model/min_reward", min(all_rewards))
            mlflow.log_metric("model/pass_rate", sum(1 for r in all_rewards if r == 1.0) / len(all_rewards))

        if all_attempted:
            mlflow.log_metric("model/attempt_rate", sum(all_attempted) / len(all_attempted))
            mlflow.log_metric("model/refusal_rate", 1 - sum(all_attempted) / len(all_attempted))

        if all_durations:
            mlflow.log_metric("system/mean_duration_sec", sum(all_durations) / len(all_durations))
            mlflow.log_metric("system/total_duration_sec", sum(all_durations))
            mlflow.log_metric("system/max_duration_sec", max(all_durations))
            mlflow.log_metric("system/min_duration_sec", min(all_durations))


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python run_eval.py <task_path> <model> [n_attempts]")
        sys.exit(1)

    task = sys.argv[1]
    model = sys.argv[2]
    attempts = int(sys.argv[3]) if len(sys.argv) > 3 else 1

    asyncio.run(run_eval(task, model, attempts))
