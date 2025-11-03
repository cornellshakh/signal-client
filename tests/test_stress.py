import asyncio
import json
import time
import uuid
from typing import ClassVar

import pytest
from tqdm import tqdm

from signal_client.command import Command
from signal_client.container import Container
from signal_client.context import Context

# Configuration for the stress test
NUM_MESSAGES = 1000
WORKER_POOL_SIZE = 4
QUEUE_SIZE = 100  # Intentionally smaller than NUM_MESSAGES to test backpressure
MIN_MESSAGES_PER_SECOND = 50


class FastCommand(Command):
    """A mock command that completes quickly."""

    triggers: ClassVar[list[str]] = ["!fast"]
    whitelisted: ClassVar[list[str]] = []
    case_sensitive = False

    async def handle(self, _: Context) -> None:
        await asyncio.sleep(0.01)


class SlowCommand(Command):
    """A mock command that simulates a long-running operation."""

    triggers: ClassVar[list[str]] = ["!slow"]
    whitelisted: ClassVar[list[str]] = []
    case_sensitive = False

    async def handle(self, _: Context) -> None:
        await asyncio.sleep(1)


@pytest.mark.timeout(0)
@pytest.mark.asyncio
async def test_thundering_herd_and_slow_commands(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A stress test to measure performance under a sudden burst of messages,
    including a mix of fast and slow commands.
    """
    # Mock the websocket client
    monkeypatch.setattr(
        "signal_client.container.WebSocketClient.__init__", lambda *_, **__: None
    )

    container = Container()
    container.config.from_dict(
        {
            "worker_pool_size": WORKER_POOL_SIZE,
            "queue_size": QUEUE_SIZE,
            "phone_number": "+1234567890",
            "base_url": "http://mock-server",
            "signal_service": "ws://mock-server",
        }
    )

    worker_pool_manager = container.worker_pool_manager()
    worker_pool_manager.register(FastCommand())
    worker_pool_manager.register(SlowCommand())
    worker_pool_manager.start()

    queue = container.message_queue()

    messages = []
    for i in range(NUM_MESSAGES):
        command = "!slow" if i % 10 == 0 else "!fast"  # 10% of commands are slow
        messages.append(
            {
                "envelope": {
                    "source": f"+1000000{i % 100}",
                    "sourceDevice": 1,
                    "timestamp": int(time.time() * 1000),
                    "dataMessage": {
                        "message": command,
                        "timestamp": int(time.time() * 1000),
                    },
                },
                "syncMessage": {},
                "type": "SYNC_MESSAGE",
                "id": str(uuid.uuid4()),
            }
        )

    start_time = time.monotonic()

    # This will fill the queue and block until workers start processing
    for message in tqdm(messages, desc="Queueing messages"):
        await queue.put(json.dumps(message))

    await queue.join()
    end_time = time.monotonic()

    worker_pool_manager.stop()
    await worker_pool_manager.join()

    session = container.session()
    await session.close()

    duration = end_time - start_time
    messages_per_second = NUM_MESSAGES / duration

    print("\n--- Stress Test Results ---")
    print(f"Processed {NUM_MESSAGES} messages in {duration:.2f} seconds.")
    print(f"Messages per second: {messages_per_second:.2f}")
    print(f"Worker pool size: {WORKER_POOL_SIZE}")
    print(f"Queue size: {QUEUE_SIZE}")
    print("-------------------------")

    # The assertion is lowered because of the slow commands
    assert messages_per_second > MIN_MESSAGES_PER_SECOND
