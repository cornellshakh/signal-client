# Infrastructure Layer

The `infrastructure` layer is responsible for all communication with external systems. It handles the low-level details of interacting with the Signal REST API, managing the WebSocket connection, and persisting data. This layer effectively isolates the core application logic from the specifics of external services, making the library more robust and adaptable.

### `websocket_client.py`

- **Purpose:** This client manages the persistent WebSocket connection to the Signal service. It is responsible for authenticating the connection and listening for real-time events, primarily incoming messages. The `MessageService` uses this client to receive messages.

### `api_clients/` (Directory)

- **Purpose:** This directory contains specialized, modular clients for different parts of the Signal REST API. For example, `messages_client.py` handles sending messages, while `groups_client.py` manages group-related operations. This separation of concerns keeps the API interaction logic organized and maintainable.
- **`base_client.py`:** A shared base class that manages the `aiohttp.ClientSession`, authentication, base URL, and common error handling. This enforces the DRY principle.

### `schemas/` (Directory)

- **Purpose:** This directory contains all the Pydantic models for API requests and responses (DTOs). This keeps the `domain` layer pure and ensures that all API communication is type-safe.

### `storage/` (Directory)

- **Purpose:** This directory contains the concrete implementations for different storage backends, such as Redis (`redis.py`) or SQLite (`sqlite.py`). The `StorageService` uses a class from this directory to perform the actual data persistence, allowing the library to be configured with different storage options.
  - `base.py`: Defines the abstract base class (ABC) for storage implementations. This ensures that all storage providers adhere to a common interface.
