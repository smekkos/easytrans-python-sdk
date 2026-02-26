# Webhook Handling

EasyTrans can push **order-status update events** to an HTTP endpoint you host.
The SDK provides [`WebhookPayload`](../api-reference/models.md) to parse and validate incoming webhook payloads.

## Webhook Payload Structure

EasyTrans sends a JSON `POST` to your endpoint whenever an order status changes.
The body corresponds to the [`WebhookPayload`](../api-reference/models.md) model.

## Parsing a Webhook

```python
import json
from easytrans import WebhookPayload

raw_body: bytes = request.body          # Django / Flask / FastAPI raw request body
data: dict = json.loads(raw_body)
payload = WebhookPayload.from_dict(data)

print(payload.orderno)       # e.g. 'ET-100001'
print(payload.status)        # e.g. 'delivered'
print(payload.datetime)      # ISO-8601 timestamp string
```

## Django Example

```python
# views.py
import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from easytrans import WebhookPayload

@csrf_exempt
def easytrans_webhook(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    try:
        data = json.loads(request.body)
        payload = WebhookPayload.from_dict(data)
    except (ValueError, KeyError) as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    # Handle the event
    handle_status_update(payload.orderno, payload.status)
    return HttpResponse(status=200)
```

## Flask Example

```python
from flask import Flask, request, jsonify
from easytrans import WebhookPayload

app = Flask(__name__)

@app.post("/webhooks/easytrans")
def easytrans_webhook():
    payload = WebhookPayload.from_dict(request.get_json(force=True))
    handle_status_update(payload.orderno, payload.status)
    return jsonify({"ok": True})
```

## Security

EasyTrans does not sign webhook requests by default.
It is strongly recommended to:

1. Restrict the webhook endpoint to EasyTrans IP ranges via your firewall or load balancer.
2. Use HTTPS exclusively.
3. Return `HTTP 200` quickly — offload heavy processing to a background task queue.
