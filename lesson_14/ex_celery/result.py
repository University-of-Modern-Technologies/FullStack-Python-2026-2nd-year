import json
from pathlib import Path
from typing import Any

from my_task import celery

RESULTS_FILE = Path(__file__).with_name("task_results.json")


def main() -> None:
    if not RESULTS_FILE.exists():
        print(f"File not found: {RESULTS_FILE}")
        print("Run app.py first to create tasks.")
        return

    tasks: list[dict[str, Any]] = json.loads(RESULTS_FILE.read_text(encoding="utf-8"))

    for task in tasks:
        result = celery.AsyncResult(task["task_id"])
        task["state"] = result.state

        if result.ready():
            task["result"] = result.result
        else:
            task["result"] = None

        print(f"{task['name']} | {task['task_id']} | {task['state']} | {task['result']}")

    RESULTS_FILE.write_text(json.dumps(tasks, indent=2), encoding="utf-8")
    print(f"Results were written to {RESULTS_FILE}")


if __name__ == "__main__":
    main()
