import json
from pathlib import Path
from typing import Any, cast

from my_task import add, sub

RESULTS_FILE = Path(__file__).with_name("task_results.json")

if __name__ == "__main__":
    add_result = cast(Any, add).delay(1, 1)
    print(f"Add task id: {add_result.id}")

    sub_result = cast(Any, sub).delay(5, 3)
    print(f"Sub task id: {sub_result.id}")

    tasks = [
        {"name": "add", "task_id": add_result.id},
        {"name": "sub", "task_id": sub_result.id},
    ]

    RESULTS_FILE.write_text(json.dumps(tasks, indent=2), encoding="utf-8")
    print(f"Task ids were written to {RESULTS_FILE}")
