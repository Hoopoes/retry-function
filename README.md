# 🌀 Retry Tools

A Python decorator for **retrying functions** with **exponential backoff**, **optional jitter**, and full support for **both synchronous and asynchronous** code.


## 🔍 About

This library provides a simple yet powerful `@retry` decorator that retries a function when specified exceptions are raised. It supports:

* **Synchronous and asynchronous functions**
* **Exponential backoff** with optional **jitter**
* **Custom exception handling**
* **Logging or custom log output**

Useful for handling flaky APIs, intermittent database errors, or any transient issues where retrying helps.


## 📦 Installation

```bash
pip install retrytools
```


## 🚀 Quick Start

### Basic Usage

```python
from retrytools import retry

@retry(catch_errors=ValueError, tries=3, delay=1)
def flaky_function():
    # Simulates an error-prone operation
    if random.random() < 0.7:
        raise ValueError("Transient issue!")
    return "Success!"

result = flaky_function()
print(result)
```


### With Async Function

```python
import asyncio
from retrytools import retry

@retry(catch_errors=ConnectionError, tries=5, delay=0.5)
async def unstable_async_api():
    if random.random() < 0.5:
        raise ConnectionError("Temporary network glitch")
    return "Fetched!"

asyncio.run(unstable_async_api())
```

## ⚙️ Parameters

| Argument       | Type                          | Description                                                        |
| -------------- | ----------------------------- | ------------------------------------------------------------------ |
| `catch_errors` | `Type[Exception]` or tuple    | Exception(s) to retry on                                           |
| `tries`        | `int`                         | Max attempts (default: 3)                                          |
| `delay`        | `float`                       | Initial delay in seconds                                           |
| `throw_error`  | `Exception` (optional)        | Custom error to raise after final failure                          |
| `logger`       | `Logger` or `Callable[[str]]` | Logging handler (e.g., `print` or `logging.Logger`)                |
| `jitter`       | `bool` or `float`             | Random delay variation: `True` for full jitter, float for additive |


## 📝 Example with Logging

```python
import logging
from retrytools import retry

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@retry(catch_errors=RuntimeError, tries=4, throw_error=Exception("Custom"), delay=2, logger=logger, jitter=True)
def sometimes_fails():
    if random.randint(0, 1):
        raise RuntimeError("Oops!")
    return "Got it!"

sometimes_fails()
```


## 📌 Notes

* **Jitter** is helpful to avoid retry storms in distributed systems.
* Supports Python 3.8+.
* Works transparently for both sync and async code.


## 🛠️ License

MIT License