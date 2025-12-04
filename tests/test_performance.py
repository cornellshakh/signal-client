"""Opt-in performance benchmarks; set RUN_PERFORMANCE_TESTS=1 and run with `pytest -m performance`."""

import asyncio
import json
import os
import random
import time
import uuid

import pytest

from signal_client.bot import SignalClient
from signal_client.command import command
from signal_client.context import Context
from signal_client.runtime.models import QueuedMessage

pytestmark = [
    pytest.mark.performance,
    pytest.mark.skipif(
        bool(os.environ.get("CI")),
        reason="Performance benchmark is disabled on CI runners.",
    ),
    pytest.mark.skipif(
        not bool(os.environ.get("RUN_PERFORMANCE_TESTS")),
        reason="Performance benchmark is opt-in; set RUN_PERFORMANCE_TESTS=1 to enable.",
    ),
]

MIN_THROUGHPUT = 100
NUM_MESSAGES = 300
WORKER_POOL_SIZE = 10
SEED = 42


@command("!test")
async def mock_command(_context: Context) -> None:
    await asyncio.sleep(0)


@pytest.mark.asyncio
@pytest.mark.usefixtures("mock_env_vars")
async def test_message_throughput() -> None:
    """
    Measures the number of messages the bot can process per second.
    """
    config = {
        "phone_number": "+1234567890",
        "signal_service": "http://localhost:8080",
        "base_url": "http://localhost:8080",
        "worker_pool_size": WORKER_POOL_SIZE,
    }
    client = SignalClient(config)
    await client.app.initialize()
    client.register(mock_command)

    queue = client.queue
    worker_pool_manager = client.worker_pool

    start_time = time.monotonic()

    # Start the worker pool
    worker_pool_manager.start()

    # Simulate incoming messages by putting them directly into the queue
    random.seed(SEED)
    for _ in range(NUM_MESSAGES):
        timestamp = int(time.time() * 1000)
        raw_message = {
            "envelope": {
                "source": "test",
                "timestamp": timestamp,
                "dataMessage": {
                    "message": "!test",
                    "id": str(uuid.uuid4()),
                },
            }
        }
        await queue.put(
            QueuedMessage(
                raw=json.dumps(raw_message),
                enqueued_at=time.perf_counter(),
            )
        )

    # Wait for all messages to be processed
    await queue.join()

    end_time = time.monotonic()

    # Stop the worker pool
    worker_pool_manager.stop()
    await worker_pool_manager.join()
    await client.shutdown()

    duration = end_time - start_time
    throughput = NUM_MESSAGES / duration
    print(f"Processed {NUM_MESSAGES} messages in {duration:.2f} seconds.")
    print(f"Throughput: {throughput:.2f} messages/sec")

    # The bot should be able to process at least 100 messages per second
    assert throughput > MIN_THROUGHPUT
