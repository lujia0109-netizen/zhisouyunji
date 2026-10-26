"""Public, offline example. No real app automation, device access or signing keys."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from threading import Lock
import time
from typing import Protocol
from uuid import uuid4

@dataclass(frozen=True)
class Task:
    question: str
    platform: str
    device_id: str  # Logical demo identifier, never an ADB address.

class Adapter(Protocol):
    def collect(self, task: Task) -> dict: ...

class MockAdapter:
    def collect(self, task: Task) -> dict:
        time.sleep(0.05)  # Synthetic delay, not a measured platform response time.
        return {
            "answer": "演示回答：企业可对比多平台的品牌描述，并核查公开信息来源。",
            "conversation_url": "https://example.com/demo/conversation",
            "sources": [{"title": "演示来源（占位）", "url": "https://example.com/demo/source"}],
            "screenshots": [],  # This mock does not capture a phone screen.
        }

class LocalDispatcher:
    """Same-process serialization only; not a distributed queue or device lease."""
    def __init__(self, device_ids: list[str], adapter: Adapter):
        self.locks = {name: Lock() for name in device_ids}
        self.adapter = adapter

    def run(self, task: Task) -> dict:
        submitted = time.monotonic()
        with self.locks[task.device_id]:
            started = time.monotonic()
            result = {
                "task_id": uuid4().hex,
                "mock": True,
                "task": asdict(task),
                "queue_seconds": round(started - submitted, 4),
            }
            try:
                result.update(self.adapter.collect(task))
                result["status"] = "demo_completed"
            except Exception as exc:
                result.update(status="demo_failed", error=str(exc))
            result["execution_seconds"] = round(time.monotonic() - started, 4)
            return result

def main():
    dispatcher = LocalDispatcher(["demo-phone-01"], MockAdapter())
    tasks = [Task("示例品牌怎么样？", name, "demo-phone-01")
             for name in ("deepseek", "yuanbao", "wenxin", "doubao")]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(dispatcher.run, tasks))
    output = Path("demo-output") / uuid4().hex
    output.mkdir(parents=True)
    (output / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Offline mock only. Results: {output / 'results.json'}")

if __name__ == "__main__":
    main()
