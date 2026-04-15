# Error Handling Guidelines

## Scope

These guidelines cover error handling for the `kessel-sdk-py` Python SDK, which provides gRPC and HTTP clients for Kessel Inventory and RBAC services.

## 1. gRPC Error Handling

### 1.1 Always catch `grpc.RpcError` around stub calls

Every gRPC stub method (`Check`, `CheckBulk`, `CheckForUpdate`, `CheckForUpdateBulk`, `CheckSelf`, `CheckSelfBulk`, `ReportResource`, `DeleteResource`, `StreamedListObjects`, `StreamedListSubjects`) can raise `grpc.RpcError`. Always wrap these calls.

```python
try:
    response = stub.Check(request)
except grpc.RpcError as e:
    print(f"Code: {e.code()}")
    print(f"Details: {e.details()}")
```

### 1.2 Use `e.code()` and `e.details()` for diagnostics

The SDK convention is to extract both the gRPC status code and the human-readable details string. Do not catch the bare `Exception` type for gRPC calls -- always catch `grpc.RpcError` specifically.

### 1.3 Branch on specific status codes when actionable

```python
except grpc.RpcError as e:
    if e.code() == grpc.StatusCode.PERMISSION_DENIED:
        # Handle auth failure
    elif e.code() == grpc.StatusCode.UNAVAILABLE:
        # Handle connectivity / retry
    elif e.code() == grpc.StatusCode.UNAUTHENTICATED:
        # Token may be expired; force refresh and retry
    else:
        raise  # Propagate unexpected errors
```

Common status codes returned by Kessel Inventory:
- `PERMISSION_DENIED` -- caller lacks authorization
- `UNAUTHENTICATED` -- missing or invalid credentials
- `UNAVAILABLE` -- service is down or unreachable
- `INVALID_ARGUMENT` -- malformed request (e.g., invalid resource type)
- `NOT_FOUND` -- referenced resource does not exist

### 1.4 Async gRPC uses the same exception type

In `async` code with `grpc.aio` channels, `grpc.RpcError` is still raised. Handle it identically.

## 2. Streaming Operations

### 2.1 Wrap the entire iteration in a try/except

For `StreamedListObjects` and `StreamedListSubjects` (server-streaming RPCs), errors can surface when initiating the stream or during iteration. The `grpc.RpcError` is raised when calling `next()` on the iterator.

```python
try:
    responses = stub.StreamedListObjects(request)
    for response in responses:
        process(response)
except grpc.RpcError as e:
    print(f"Code: {e.code()}")
    print(f"Details: {e.details()}")
```

### 2.2 Streaming helpers propagate errors -- do not swallow them

The `list_workspaces()` and `list_workspaces_async()` generators in `kessel.rbac.v2` yield responses directly from `StreamedListObjects`. They do not catch exceptions internally. Callers must handle `grpc.RpcError` at the call site.

### 2.3 Async streaming uses `async for` with the same error contract

```python
try:
    async for obj in list_workspaces_async(stub, subject=subj, relation="member"):
        process(obj)
except grpc.RpcError as e:
    handle_error(e)
```

## 3. CheckBulk Per-Item Errors

### 3.1 Bulk responses use a pair/oneof model -- not exceptions

`CheckBulk`, `CheckSelfBulk`, and `CheckForUpdateBulk` each return a response with a `pairs` list. Each pair contains the original `request` and a oneof `response` that is either an `item` (success with `allowed` field) or an `error` (`google.rpc.Status`).

A successful RPC call does **not** mean every item succeeded. Always inspect each pair:

```python
response = stub.CheckBulk(bulk_request)
for pair in response.pairs:
    if pair.HasField("item"):
        # Success: inspect pair.item.allowed
        pass
    elif pair.HasField("error"):
        # Per-item failure: inspect pair.error.code and pair.error.message
        print(f"Error: Code={pair.error.code}, Message={pair.error.message}")
```

### 3.2 The RPC itself can still fail

Wrap the `CheckBulk` call in `try/except grpc.RpcError` for transport-level and request-level errors. Per-item errors are returned inside the response.

## 4. HTTP / RBAC Error Handling

### 4.1 `raise_for_status()` is used for HTTP calls

The RBAC workspace functions (`fetch_root_workspace`, `fetch_default_workspace`) and `fetch_oidc_discovery` call `response.raise_for_status()` which raises `requests.exceptions.HTTPError` on 4xx/5xx responses.

```python
try:
    workspace = fetch_root_workspace(
        rbac_base_endpoint=endpoint, org_id="12345", auth=auth
    )
except requests.exceptions.HTTPError as e:
    handle_http_error(e)
```

### 4.2 `ValueError` for empty or malformed responses

`_fetch_workspace_by_type` raises `ValueError` when the JSON response has no matching workspace data:

```python
try:
    workspace = fetch_default_workspace(...)
except ValueError as e:
    # "No default workspace found in response"
    handle_missing_workspace(e)
except requests.exceptions.HTTPError as e:
    handle_http_error(e)
```

### 4.3 Network errors raise `requests.exceptions.RequestException`

Connection timeouts, DNS failures, and similar transport errors raise subclasses of `RequestException`. The `fetch_oidc_discovery` function documents this in its docstring.

## 5. Authentication Errors

### 5.1 Token fetch errors propagate from `oauthlib`/`requests_oauthlib`

`OAuth2ClientCredentials.get_token()` delegates to `OAuth2Session.fetch_token()`. Failures (invalid credentials, unreachable token endpoint) raise exceptions from the underlying OAuth library. Let these propagate unless you have a specific retry strategy.

### 5.2 OIDC discovery errors

`fetch_oidc_discovery()` can raise:
- `requests.exceptions.HTTPError` -- non-2xx from the discovery endpoint
- `requests.exceptions.RequestException` -- network-level failure
- `ValueError` -- response is not valid JSON

Always call `fetch_oidc_discovery` before constructing `OAuth2ClientCredentials`. If it fails, the client cannot be built.

### 5.3 Token refresh is automatic -- errors surface at call time

`AuthRequest.__call__()` and `GoogleOAuth2ClientCredentials.refresh()` invoke `get_token()` transparently. If the token endpoint is down, the error surfaces when the gRPC call or HTTP request is made, not during client construction.

## 6. ClientBuilder Validation Errors

### 6.1 `TypeError` for invalid target

`ClientBuilder("")`, `ClientBuilder(None)`, and `ClientBuilder(12345)` all raise `TypeError`. Validate the target string before constructing the builder.

### 6.2 `ValueError` for insecure + authenticated

Calling `oauth2_client_authenticated(creds, channel_credentials=insecure_channel_credentials())` raises `ValueError` with message `"Invalid credential configuration: can not authenticate with insecure channel"`. This is a build-time guard -- do not catch and ignore it.

## 7. Error Propagation Rules

### 7.1 SDK library code does NOT catch `grpc.RpcError`

Internal SDK functions (e.g., `list_workspaces`, `list_workspaces_async`) do not catch gRPC errors. They propagate to the caller. This is intentional -- the SDK consumer decides the error handling strategy.

### 7.2 SDK library code does NOT catch HTTP errors from `raise_for_status()`

`_fetch_workspace_by_type` and `fetch_oidc_discovery` call `raise_for_status()` and let the exception propagate. They only raise their own `ValueError` for business-logic failures (missing data).

### 7.3 What to catch vs. what to propagate

| Layer | Catch | Propagate |
|---|---|---|
| Example / application code | `grpc.RpcError`, `HTTPError`, `ValueError` | Unexpected errors |
| SDK library functions | Nothing (except raising `ValueError` for validation) | All transport and RPC errors |
| Tests | Use `pytest.raises(...)` to assert expected exceptions | N/A |

## 8. Channel Lifecycle and Resource Cleanup

### 8.1 Always use context managers for channels

Sync channels use `with channel:`, async channels use `async with channel:`. This ensures cleanup even when exceptions occur inside the block.

### 8.2 Place error handling inside the context manager

`grpc.RpcError` captures its status code and details locally, so `e.code()` and `e.details()` work regardless of channel state. Still, place the `try/except grpc.RpcError` block inside the `with channel:` context manager for proper resource cleanup and clearer control flow.

## 9. Testing Error Scenarios

### 9.1 Use `side_effect` to simulate errors

```python
mock_inventory.StreamedListObjects.side_effect = Exception("stream failed")
with pytest.raises(Exception, match="stream failed"):
    list(list_workspaces(mock_inventory, subj, "member"))
```

### 9.2 Use `raise_for_status.side_effect` for HTTP errors

```python
mock_response.raise_for_status.side_effect = HTTPError("Not Found")
with pytest.raises(HTTPError):
    fetch_oidc_discovery("https://invalid.example.com")
```

### 9.3 Test per-item bulk errors separately from RPC errors

Verify that `CheckBulkResponsePair.HasField("error")` is handled correctly. This is distinct from testing that `grpc.RpcError` is raised at the RPC level.

## 10. Anti-Patterns to Avoid

1. **Do not catch bare `Exception` for gRPC calls.** Always use `grpc.RpcError`.

2. **Do not ignore `pair.error` in bulk responses.** A successful `CheckBulk` RPC can contain per-item failures.

3. **Do not swallow errors in streaming iteration.** If one response in a stream fails, the entire iterator raises. Handle it or propagate it.

4. **Do not construct `OAuth2ClientCredentials` with an unvalidated token endpoint.** Always call `fetch_oidc_discovery` first and handle its errors before proceeding to client construction.

5. **Do not use insecure channels with authenticated credentials.** The `ClientBuilder` enforces this with a `ValueError` at build time.
