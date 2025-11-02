# Services Layer

The `services` layer contains the core application logic of the `signal-client` library. These services are responsible for orchestrating the flow of data and coordinating the interactions between the low-level infrastructure and the high-level command processing.

### `worker_pool_manager.py`

- **Purpose:** This is the heart of the message processing engine. It creates and manages a pool of `Worker` tasks. This provides bounded concurrency, ensuring the system remains stable under heavy load. The manager is also responsible for registering commands and distributing them to the workers.

### `message_service.py`

- **Purpose:** This service is responsible for the "listening" part of the bot. It uses the `WebSocketClient` from the infrastructure layer to listen for incoming messages from the Signal service. When a new message is received, the `MessageService`'s job is to place it into the `MessageQueue`, where it can be picked up by a `Worker` for processing.

### `lock_manager.py`

- **Purpose:** This service provides a mechanism for creating and managing `asyncio.Lock` objects. This allows developers to write thread-safe commands and prevent race conditions when dealing with shared resources.

### `storage_service.py`

- **Purpose:** This service provides an abstraction for persistent storage. It allows the bot to store and retrieve data, which can be used for various purposes such as remembering user preferences, storing session information, or caching data. The actual storage mechanism (e.g., Redis, SQLite) is managed in the `infrastructure/storage` directory, allowing the service to remain agnostic to the implementation details.
