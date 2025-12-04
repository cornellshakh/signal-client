# Advanced Usage: Custom Middleware and Beyond

This guide delves into advanced usage patterns for the Signal Client, focusing on how to extend its functionality and tailor it to specific needs through custom middleware, request/response modification, and deeper integration points.

---

## 1. Understanding Middleware

Middleware functions are powerful hooks that allow you to intercept and process requests and responses. In the Signal Client, middleware can be applied to the underlying HTTP client (`httpx` or similar) to:

-   **Modify Headers:** Add custom headers for authentication, tracking, or specific API requirements.
-   **Logging:** Implement detailed logging of requests and responses.
-   **Error Handling:** Pre-process or transform API errors before they reach your application logic.
-   **Caching:** Implement custom caching strategies.
-   **Request/Response Transformation:** Alter the payload of outgoing requests or incoming responses.

### How Middleware Works (Conceptual)

Middleware typically forms a chain. A request passes through each middleware function before reaching the core client logic. The response then travels back through the middleware chain in reverse order.

```mermaid
graph LR
    A[Your Application] --> M1[Middleware 1]
    M1 --> M2[Middleware 2]
    M2 --> C[Signal Client (Core Request)]
    C --> M2
    M2 --> M1
    M1 --> A
```

---

## 2. Implementing Custom Middleware

The Signal Client's `BaseClient` utilizes `httpx.AsyncClient` which supports custom middleware through event hooks. You can leverage this by creating your own `httpx.AsyncClient` instance and passing it to the `BaseClient`.

### Example: Adding a Custom Header Middleware

Let's say you need to add a custom `X-API-KEY` header to every outgoing request.

```python
import httpx
from signal_client.infrastructure.api_clients.base_client import BaseClient
from signal_client.exceptions import SignalClientError, RateLimitError, UnauthorizedError, ForbiddenError, NotFoundError, ConflictError, ServerError
from typing import Callable, Awaitable

async def add_api_key_middleware(
    request: httpx.Request,
    call_next: Callable[[httpx.Request], Awaitable[httpx.Response]],
) -> httpx.Response:
    """
    Middleware to add a custom X-API-KEY header to requests.
    """
    api_key = "YOUR_SUPER_SECRET_API_KEY"  # Load securely, e.g., from environment variables
    request.headers["X-API-KEY"] = api_key
    response = await call_next(request)
    return response

class CustomClient(BaseClient):
    def __init__(self, base_url: str, api_key: str):
        # Create a custom httpx.AsyncClient with event hooks
        self._async_client = httpx.AsyncClient(base_url=base_url, event_hooks={'request': [add_api_key_middleware]})
        # If you need to pass additional context to your middleware, you might need to
        # wrap it or use a factory function that closes over the context.
        # For simplicity, api_key is hardcoded here, but should be dynamic.

    # Example of how you might use a factory to pass `api_key`
    @staticmethod
    def api_key_factory(api_key: str) -> Callable[[httpx.Request, Callable[[httpx.Request], Awaitable[httpx.Response]]], Awaitable[httpx.Response]]:
        async def api_key_middleware(
            request: httpx.Request,
            call_next: Callable[[httpx.Request], Awaitable[httpx.Response]],
        ) -> httpx.Response:
            request.headers["X-API-KEY"] = api_key
            response = await call_next(request)
            return response
        return api_key_middleware

    @classmethod
    def with_middleware(cls, base_url: str, api_key: str) -> "CustomClient":
        middleware_func = cls.api_key_factory(api_key)
        client = cls(base_url=base_url)
        client._async_client = httpx.AsyncClient(base_url=base_url, event_hooks={'request': [middleware_func]})
        return client

# Usage
# custom_client = CustomClient.with_middleware("https://api.signal.com", "my_secret_key")
# response = await custom_client.some_api_method(...)
```

### Example: Response Logging Middleware

This middleware logs the request and response details, useful for debugging and auditing.

```python
import httpx
import logging
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)

async def log_requests_responses(
    request: httpx.Request,
    call_next: Callable[[httpx.Request], Awaitable[httpx.Response]],
) -> httpx.Response:
    """
    Middleware to log requests and responses.
    """
    logger.info(f"Request: {request.method} {request.url} Headers: {request.headers}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code} {response.url} Headers: {response.headers}")
    return response

# To use this, you'd pass it in the event_hooks as shown above:
# client._async_client = httpx.AsyncClient(base_url="...", event_hooks={'request': [log_requests_responses]})
```

---

## 3. Custom Exception Handling with Middleware

While the `BaseClient` already maps common HTTP status codes to specific exceptions, you might have custom error structures or wish to handle specific status codes differently. You can integrate this into your middleware.

```python
import httpx
from signal_client.exceptions import SignalClientError, RateLimitError, UnauthorizedError, ForbiddenError, NotFoundError, ConflictError, ServerError
from typing import Callable, Awaitable

async def custom_error_handling_middleware(
    request: httpx.Request,
    call_next: Callable[[httpx.Request], Awaitable[httpx.Response]],
) -> httpx.Response:
    response = await call_next(request)

    if response.status_code == 429:
        raise RateLimitError("Rate limit exceeded.")
    elif response.status_code == 401:
        raise UnauthorizedError("Authentication failed.")
    elif response.status_code == 403:
        raise ForbiddenError("Access forbidden.")
    elif response.status_code == 404:
        raise NotFoundError("Resource not found.")
    elif response.status_code == 409:
        raise ConflictError("Conflict with existing resource.")
    elif response.status_code >= 500:
        raise ServerError(f"Server error: {response.status_code} - {response.text}")
    elif response.status_code >= 400:
        # Catch any other client errors not specifically handled
        raise SignalClientError(f"Client error: {response.status_code} - {response.text}")

    return response

# Integrate this by adding it to the 'response' event_hooks:
# client._async_client = httpx.AsyncClient(
#     base_url="...",
#     event_hooks={'response': [custom_error_handling_middleware]}
# )
```

---

## 4. Extending BaseClient for Reusability

For more complex scenarios, or to ensure your middleware is consistently applied across multiple API clients, consider creating a custom `BaseClient` subclass.

```python
import httpx
from signal_client.infrastructure.api_clients.base_client import BaseClient
from typing import Callable, Awaitable, List

async def my_first_middleware(
    request: httpx.Request,
    call_next: Callable[[httpx.Request], Awaitable[httpx.Response]],
) -> httpx.Response:
    # ... your middleware logic ...
    return await call_next(request)

async def my_second_middleware(
    request: httpx.Request,
    call_next: Callable[[httpx.Request], Awaitable[httpx.Response]],
) -> httpx.Response:
    # ... your middleware logic ...
    return await call_next(request)

class MyCustomBaseClient(BaseClient):
    def __init__(self, base_url: str, middlewares: List[Callable] = None):
        super().__init__(base_url)
        # Apply custom middlewares to the httpx.AsyncClient
        if middlewares:
            for middleware in middlewares:
                # Assuming 'request' hooks for simplicity, can extend for 'response'
                self._async_client.event_hooks['request'].append(middleware)

# Usage
# custom_base_client = MyCustomBaseClient(
#     "https://api.signal.com",
#     middlewares=[my_first_middleware, my_second_middleware]
# )
# accounts_client = AccountsClient(custom_base_client) # Pass the custom client
```

---

## 5. Request and Response Transformation

Beyond simple headers, you might need to fundamentally alter the JSON payload of requests or responses. This is particularly useful when integrating with APIs that have idiosyncratic data structures.

### Example: Transforming Outgoing Request Body

```python
import httpx
import json
from typing import Callable, Awaitable

async def transform_request_body(
    request: httpx.Request,
    call_next: Callable[[httpx.Request], Awaitable[httpx.Response]],
) -> httpx.Response:
    if request.method == "POST" and request.url.path == "/v1/messages":
        # Assume the API expects 'content' instead of 'message'
        original_json = json.loads(request.content)
        if "message" in original_json:
            original_json["content"] = original_json.pop("message")
            request.content = json.dumps(original_json).encode("utf-8")
            request.headers["Content-Length"] = str(len(request.content))
    response = await call_next(request)
    return response

# Use this with an event_hook for 'request'.
```

### Example: Transforming Incoming Response Body

```python
import httpx
import json
from typing import Callable, Awaitable

async def transform_response_body(
    response: httpx.Response,
    call_next: Callable[[httpx.Response], Awaitable[httpx.Response]],
) -> httpx.Response:
    if response.request.url.path == "/v1/users" and response.status_code == 200:
        # Assume the API returns 'user_data' but you want 'user'
        original_json = response.json()
        if "user_data" in original_json:
            original_json["user"] = original_json.pop("user_data")
            response._content = json.dumps(original_json).encode("utf-8")
            response.headers["Content-Length"] = str(len(response._content))
    return await call_next(response)

# Note: httpx's event_hooks for responses are processed after _raise_for_status,
# so direct modification of response._content is generally needed.
```

---

## 6. Advanced Asynchronous Patterns

Leverage Python's `asyncio` for concurrent operations when making multiple API calls.

```python
import asyncio
from signal_client.infrastructure.api_clients.contacts_client import ContactsClient
from signal_client.infrastructure.api_clients.messages_client import MessagesClient

async def fetch_contacts_and_send_messages(base_url: str, phone_number: str):
    contacts_client = ContactsClient(base_url=base_url)
    messages_client = MessagesClient(base_url=base_url)

    # Fetch contacts concurrently
    contacts_task = contacts_client.get_contacts(phone_number)
    messages_to_send = [
        {"recipient": "+1234567890", "message": "Hello!"},
        {"recipient": "+1987654321", "message": "How are you?"},
    ]
    send_message_tasks = [
        messages_client.send(msg) for msg in messages_to_send
    ]

    results = await asyncio.gather(contacts_task, *send_message_tasks)

    all_contacts = results[0]
    sent_messages_confirmations = results[1:]

    print("Contacts:", all_contacts)
    print("Sent Messages:", sent_messages_confirmations)

# To run:
# asyncio.run(fetch_contacts_and_send_messages("https://api.signal.com", "+11231231234"))
```

By mastering custom middleware and leveraging asynchronous programming, you can build highly robust, flexible, and performant applications with the Signal Client.
