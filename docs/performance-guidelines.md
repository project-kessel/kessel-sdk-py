# Performance Guidelines

## 1. Client Lifecycle and Channel Management

### 1.1 Reuse a single `(stub, channel)` pair per service endpoint

`ClientBuilder.build()` and `build_async()` each return a `(stub, channel)` tuple. Creating a channel is expensive (TCP + TLS handshake, HTTP/2 negotiation). Build once at startup and share the stub across your application.

```python
# Good -- build once, reuse
stub, channel = ClientBuilder(KESSEL_ENDPOINT).oauth2_client_authenticated(creds).build()

# Bad -- building per request
def check(subject, resource):
    stub, channel = ClientBuilder(KESSEL_ENDPOINT).oauth2_client_authenticated(creds).build()
    return stub.Check(request)
```

### 1.2 Always close channels

Use the channel as a context manager to guarantee resource cleanup. For sync clients use `with channel:`, for async clients use `async with channel:`. Alternatively, call `channel.close()` (sync) or `await channel.close()` (async) explicitly.

### 1.3 SingleThreadedUnaryStream is enabled by default

The `ClientBuilder.build()` method sets `ChannelOptions.SingleThreadedUnaryStream = 1` on sync channels. This reduces thread overhead for server-streaming RPCs (`StreamedListObjects`, `StreamedListSubjects`) by avoiding spawning a background thread per stream. Do not override this option unless you have a specific reason. Note: `build_async()` does not set this option because the async event loop already avoids thread-per-stream overhead.

## 2. Async vs Sync Client Selection

### 2.1 Use `build_async()` for concurrent workloads

When your application needs to issue multiple RPCs concurrently (e.g., parallel Check calls, concurrent stream consumption), use the async client. It avoids thread-pool exhaustion under high concurrency.

```python
stub, channel = ClientBuilder(KESSEL_ENDPOINT).oauth2_client_authenticated(creds).build_async()

async with channel:
    results = await asyncio.gather(
        stub.Check(request1),
        stub.Check(request2),
        stub.Check(request3),
    )
```

### 2.2 Use `build()` for simple sequential flows

The sync client is appropriate for CLI tools, scripts, and single-threaded applications where simplicity matters more than concurrency.

### 2.3 Do not mix sync and async stubs on the same channel

A channel created by `build()` uses `grpc.secure_channel` (sync); a channel from `build_async()` uses `grpc.aio.secure_channel`. They are not interchangeable. Never pass an async channel to sync iteration patterns or vice versa.

## 3. Streaming APIs

### 3.1 Prefer `StreamedListObjects` / `StreamedListSubjects` over collecting all results

These are server-streaming RPCs (`unary_stream`). Results arrive incrementally, reducing peak memory usage and time-to-first-result compared to waiting for a complete list.

```python
# Good -- process each result as it arrives
for response in stub.StreamedListObjects(request):
    process(response)

# Bad -- materialize entire stream into a list first
all_results = list(stub.StreamedListObjects(request))
```

### 3.2 Use the SDK's auto-paginating helpers for workspace listing

`list_workspaces()` (sync) and `list_workspaces_async()` (async) in `kessel.rbac.v2` handle continuation token pagination automatically. They yield individual `StreamedListObjectsResponse` messages, internally issuing new `StreamedListObjects` RPCs when continuation tokens are present.

### 3.3 Handle continuation tokens correctly in custom streaming loops

When writing your own pagination loop over `StreamedListObjects` or `StreamedListSubjects`:
- Extract `continuation_token` from each response's `pagination` field.
- Stop when the token is empty/falsy.
- Pass the token in `RequestPagination(limit=N, continuation_token=token)` on the next request.
- The SDK helpers use a default limit of `1000`. Use a similar value unless you have a reason to change it.

## 4. Bulk APIs

### 4.1 Use `CheckBulk` instead of multiple `Check` calls

When verifying permissions for multiple resource-subject-relation triples, batch them into a single `CheckBulk` (or `CheckSelfBulk`, `CheckForUpdateBulk`) request. This is a single unary RPC that eliminates per-call overhead.

```python
# Good -- single RPC
bulk_request = CheckBulkRequest(items=[item1, item2, item3])
bulk_response = stub.CheckBulk(bulk_request)

# Bad -- N separate RPCs
for item in items:
    stub.Check(CheckRequest(...))
```

### 4.2 Choose `Check` vs `CheckForUpdate` based on consistency needs

- `Check`: Eventually consistent. Use for read-path authorization (dashboards, UI gating). Lower latency.
- `CheckForUpdate`: Strongly consistent. Use immediately before write/delete operations. Higher latency due to consistency guarantee.

The same distinction applies to their bulk variants.

## 5. Token Caching and Authentication

### 5.1 Reuse a single `OAuth2ClientCredentials` instance

`OAuth2ClientCredentials` caches the access token and automatically refreshes it when it expires or is within 300 seconds (5 minutes) of expiry. Creating multiple instances defeats the cache and causes redundant token fetches.

```python
# Good -- create once, share
auth_credentials = OAuth2ClientCredentials(client_id=ID, client_secret=SECRET, token_endpoint=EP)
stub1, _ = ClientBuilder(EP1).oauth2_client_authenticated(auth_credentials).build()
stub2, _ = ClientBuilder(EP2).oauth2_client_authenticated(auth_credentials).build()
```

### 5.2 Call `fetch_oidc_discovery()` once at startup

`fetch_oidc_discovery()` makes a synchronous HTTP request to `{issuer}/.well-known/openid-configuration`. Cache the returned `OIDCDiscoveryMetadata` rather than calling it before every client creation.

### 5.3 Token refresh is not thread-safe

`OAuth2ClientCredentials.get_token()` is not synchronized. If you share a single instance across threads, concurrent calls during token refresh may trigger multiple refresh requests. In multi-threaded sync applications, protect `get_token()` with a lock or use the async client instead.

## 6. Consistency and Write Visibility

### 6.1 Set `consistency` on read requests only when needed

`CheckRequest`, `StreamedListObjectsRequest`, and `StreamedListSubjectsRequest` accept an optional `Consistency` field with three modes:
- `minimize_latency`: Fastest; may use cached/stale data.
- `at_least_as_fresh(ConsistencyToken)`: Ensures data is at least as fresh as the provided token.
- `at_least_as_acknowledged`: Ensures all acknowledged writes are visible.

Omitting consistency (the default) lets the server choose. Only set `at_least_as_acknowledged` or `at_least_as_fresh` when your use case requires it, as they increase latency.

### 6.2 Use `write_visibility = IMMEDIATE` on `ReportResource` only when needed

`ReportResourceRequest` has a `write_visibility` field. Setting `IMMEDIATE` forces the server to make the reported resource visible to subsequent `Check` calls right away, at a latency cost. Use `MINIMIZE_LATENCY` (or leave unspecified) for fire-and-forget reporting.

## 7. Anti-Patterns to Avoid

- **Do not create channels per request.** Each `ClientBuilder.build()` or `build_async()` call creates a new gRPC channel with full connection setup. Reuse stubs.
- **Do not ignore the channel return value.** `build()` returns `(stub, channel)`. If you discard the channel, you cannot close it, leading to leaked connections and file descriptors.
- **Do not use `force_refresh=True` on every `get_token()` call.** This bypasses the token cache and forces a round-trip to the OIDC provider on every call. Let the 300-second expiry buffer handle refresh automatically.
- **Do not materialize large streams into lists.** Calling `list()` on `StreamedListObjects` or `StreamedListSubjects` loads all results into memory. For large result sets, iterate and process incrementally.
- **Do not use sync streaming in async contexts.** Use `async for` with async stubs for streaming RPCs. Using sync `for` on a sync stub inside an `async def` blocks the event loop.

## 8. RBAC HTTP API Performance

### 8.1 Pass a `requests.Session` as `http_client` for connection reuse

`fetch_root_workspace()` and `fetch_default_workspace()` accept an `http_client` parameter. Passing a `requests.Session` (instead of the default `requests` module) enables HTTP connection pooling across multiple calls.

```python
import requests

session = requests.Session()
root_ws = fetch_root_workspace(endpoint, org_id, auth=auth, http_client=session)
default_ws = fetch_default_workspace(endpoint, org_id, auth=auth, http_client=session)
```
