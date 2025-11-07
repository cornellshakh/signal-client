import asyncio
import json
import random
import time
import uuid

import pytest

from signal_client.bot import SignalClient
from signal_client.command import command
from signal_client.context import Context
from signal_client.services.models import QueuedMessage

# Configuration for the stress test
NUM_MESSAGES = 400
WORKER_POOL_SIZE = 10
QUEUE_SIZE = 100  # Intentionally smaller than NUM_MESSAGES to test backpressure
MIN_MESSAGES_PER_SECOND = 50
SEED = 123


@command("!fast")
async def fast_command(_: Context) -> None:
    """A mock command that completes quickly."""
    await asyncio.sleep(0)


@command("!slow")
async def slow_command(_: Context) -> None:
    """A mock command that simulates a long-running operation."""
    await asyncio.sleep(0.05)


@pytest.mark.timeout(0)
@pytest.mark.asyncio
@pytest.mark.usefixtures("mock_env_vars")
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

    config = {
        "worker_pool_size": WORKER_POOL_SIZE,
        "queue_size": QUEUE_SIZE,
        "phone_number": "+1234567890",
        "base_url": "http://mock-server",
        "signal_service": "ws://mock-server",
    }
    client = SignalClient(config=config)
    container = client.container

    worker_pool_manager = container.services_container.worker_pool_manager()
    worker_pool_manager.register(fast_command)
    worker_pool_manager.register(slow_command)
    worker_pool_manager.start()

    queue = container.services_container.message_queue()

    messages = []
    random.seed(SEED)
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
    for message in messages:
        await queue.put(
            QueuedMessage(raw=json.dumps(message), enqueued_at=time.perf_counter())
        )

    await queue.join()
    end_time = time.monotonic()

    worker_pool_manager.stop()
    await worker_pool_manager.join()

    session = container.api_client_container.session()
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
