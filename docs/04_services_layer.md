# Services Layer

The `services` layer contains the core application logic of the `signal-client` library. These services are responsible for orchestrating the flow of data and coordinating the interactions between the low-level infrastructure and the high-level command processing.

### `worker_pool_manager.py`

- **Purpose:** This is the heart of the message processing engine. It creates and manages a pool of `Worker` tasks. This provides bounded concurrency, ensuring the system remains stable under heavy load. The manager is also responsible for registering commands and distributing them to the workers.

### `message_service.py`

- **Purpose:** This service is responsible for the "listening" part of the bot. It uses the `WebSocketClient` from the infrastructure layer to listen for incoming messages from the Signal service. When a new message is received, the `MessageService`'s job is to place the raw JSON message into the `MessageQueue`, where it can be picked up by a `Worker` for processing.

### `message_parser.py`

- **Purpose:** This service is responsible for parsing the raw JSON messages from the `MessageQueue` into structured `Message` objects. This keeps the `Worker` clean and focused on its primary responsibility of executing commands.

### `rate_limiter.py`

- **Purpose:** This service ensures that the bot does not exceed the API rate limits of the Signal service. It provides a simple `acquire` method that can be used to control the rate of outgoing requests.

### `lock_manager.py`

- **Purpose:** This service provides `asyncio.Lock` objects to commands via the `Context`. This allows developers to easily write thread-safe code and prevent race conditions when dealing with shared resources.
