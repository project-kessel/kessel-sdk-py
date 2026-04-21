# Error Handling Guidelines

AGENTS.md covers the two key pitfalls: always catch `grpc.RpcError` (not bare `Exception`), and always check per-item errors in bulk responses. This file provides the detailed patterns.

---

## 1. gRPC Status Codes

Branch on specific codes when actionable:

```python
except grpc.RpcError as e:
    if e.code() == grpc.StatusCode.PERMISSION_DENIED:
        # Auth failure
    elif e.code() == grpc.StatusCode.UNAVAILABLE:
        # Connectivity / retry
    elif e.code() == grpc.StatusCode.UNAUTHENTICATED:
        # Token expired; force refresh and retry
    else:
        raise
```

Common codes returned by Kessel Inventory:
- `PERMISSION_DENIED` -- caller lacks authorization
- `UNAUTHENTICATED` -- missing or invalid credentials
- `UNAVAILABLE` -- service down or unreachable
- `INVALID_ARGUMENT` -- malformed request
- `NOT_FOUND` -- resource does not exist

Async gRPC (`grpc.aio`) raises the same `grpc.RpcError`.

## 2. Streaming Errors

Wrap the entire iteration in `try/except` -- errors can surface when initiating the stream or during iteration:

```python
try:
    for response in stub.StreamedListObjects(request):
        process(response)
except grpc.RpcError as e:
    handle(e)
```

`list_workspaces()` and `list_workspaces_async()` do not catch exceptions internally -- callers must handle `grpc.RpcError`.

## 3. CheckBulk Per-Item Errors

A successful RPC does not mean every item succeeded. Each pair in the response contains a oneof: `item` (success) or `error` (`google.rpc.Status`).

```python
response = stub.CheckBulk(bulk_request)
for pair in response.pairs:
    if pair.HasField("item"):
        # pair.item.allowed
        pass
    elif pair.HasField("error"):
        print(f"Error: Code={pair.error.code}, Message={pair.error.message}")
```

The RPC itself can still fail with `grpc.RpcError` for transport-level errors.

## 4. HTTP / RBAC Errors

- `fetch_root_workspace`, `fetch_default_workspace`, and `fetch_oidc_discovery` call `response.raise_for_status()`, raising `requests.exceptions.HTTPError` on 4xx/5xx.
- `_fetch_workspace_by_type` raises `ValueError` when the response has no matching workspace data.
- Network failures raise `requests.exceptions.RequestException` subclasses.

## 5. Authentication Errors

- Token fetch failures propagate from `oauthlib`/`requests_oauthlib`. Let them propagate unless you have a specific retry strategy.
- `fetch_oidc_discovery()` can raise `HTTPError`, `RequestException`, or `ValueError` (invalid JSON).
- Token refresh errors surface at gRPC/HTTP call time (via `AuthRequest.__call__()` or `GoogleOAuth2ClientCredentials.refresh()`), not during client construction.

## 6. ClientBuilder Validation

- `ClientBuilder("")`, `ClientBuilder(None)`, `ClientBuilder(12345)` raise `TypeError`.
- `oauth2_client_authenticated(creds, channel_credentials=insecure_channel_credentials())` raises `ValueError`.

## 7. Channel Lifecycle

Always place `try/except grpc.RpcError` inside the `with channel:` context manager for proper cleanup:

```python
with channel:
    try:
        response = stub.Check(request)
    except grpc.RpcError as e:
        handle(e)
```
