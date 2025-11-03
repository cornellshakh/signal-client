# Configuration Reference

The `signal-client` library is configured via a Python dictionary passed to the `SignalClient` constructor. This document details all the available configuration options.

---

## Core Configuration

These are the essential settings required to get your bot running.

### `signal_service`

- **Type:** `str`
- **Description:** The URL of the `signal-cli-rest-api` service.
- **Example:** `"http://localhost:8080"`

### `phone_number`

- **Type:** `str`
- **Description:** The phone number of your bot's Signal account, in E.164 format.
- **Example:** `"+1234567890"`

---

## Performance Tuning

These settings allow you to fine-tune the performance of your bot.

### `worker_pool_size`

- **Type:** `int`
- **Default:** `4`
- **Description:** The number of concurrent worker tasks that will be created to process incoming messages. A larger pool size can handle a higher volume of messages but will consume more system resources.
- **Example:** `8`

### `rate_limiter`

- **Type:** `dict`
- **Default:** `{"rate_limit": 2, "period": 1.0}`
- **Description:** A dictionary containing the configuration for the rate limiter.
  - `rate_limit`: The maximum number of requests to allow within the specified period.
  - `period`: The time period in seconds.
- **Example:** `{"rate_limit": 10, "period": 60.0}`

### `circuit_breaker`

- **Type:** `dict`
- **Default:** `{"failure_threshold": 5, "reset_timeout": 30}`
- **Description:** A dictionary containing the configuration for the circuit breaker.
  - `failure_threshold`: The number of consecutive failures that will cause the circuit breaker to open.
  - `reset_timeout`: The number of seconds the circuit breaker will wait before transitioning to the "half-open" state.
- **Example:** `{"failure_threshold": 10, "reset_timeout": 60}`

---

## Example Configuration

Here is an example of a complete configuration dictionary:

```python
config = {
    "signal_service": "http://localhost:8080",
    "phone_number": "+1234567890",
    "worker_pool_size": 8,
    "rate_limiter": {
        "rate_limit": 10,
        "period": 60.0,
    },
    "circuit_breaker": {
        "failure_threshold": 10,
        "reset_timeout": 60,
    },
}

client = SignalClient(config)
```
