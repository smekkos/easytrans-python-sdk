# Authentication

EasyTrans uses **two separate authentication mechanisms** depending on which API surface you call.
The SDK handles both transparently — you supply the four constructor arguments once.

## Constructor Parameters

```python
from easytrans import EasyTransClient

client = EasyTransClient(
    server_url="mytrans.nl",        # (1)
    environment_name="production",  # (2)
    username="your_username",       # (3)
    password="your_password",       # (4)
    default_mode="test",            # (5) optional, default "test"
    timeout=30,                     # (6) optional, seconds
)
```

1. **`server_url`** — Domain of your EasyTrans instance, e.g. `mytrans.nl`, `mytrans.be`
2. **`environment_name`** — The EasyTrans environment identifier provided by your carrier
3. **`username`** — API username (obtained from your carrier)
4. **`password`** — API password
5. **`default_mode`** — `"test"` (dry-run, no records created) or `"effect"` (live)
6. **`timeout`** — HTTP request timeout in seconds (default `30`)

## JSON Import API

Credentials are embedded **in the POST body** (not HTTP headers).
The SDK handles this automatically whenever you call [`import_orders()`](../api-reference/client.md) or [`import_customers()`](../api-reference/client.md).

## REST API

The REST API (`/api/v1/`) uses standard **HTTP Basic Authentication** over HTTPS.
The SDK builds the `Authorization: Basic …` header automatically for every REST call.

## Obtaining Credentials

Contact your EasyTrans carrier/operator to obtain:

- Server URL
- Environment name
- API username and password

## Environment Variables (Recommended)

Store credentials in environment variables rather than hard-coding them:

```python
import os
from easytrans import EasyTransClient

client = EasyTransClient(
    server_url=os.environ["EASYTRANS_SERVER_URL"],
    environment_name=os.environ["EASYTRANS_ENVIRONMENT"],
    username=os.environ["EASYTRANS_USERNAME"],
    password=os.environ["EASYTRANS_PASSWORD"],
)
```

See [`.env.example`](https://github.com/yourusername/easytrans-sdk/blob/main/.env.example) for the full list of supported variables.
