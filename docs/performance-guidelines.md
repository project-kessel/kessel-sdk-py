# Performance Guidelines

Cross-cutting rules (channel reuse, sync/async separation) are in AGENTS.md Common Pitfalls. This file covers performance-specific depth.

---

## 1. SingleThreadedUnaryStream

`ClientBuilder.build()` sets `ChannelOptions.SingleThreadedUnaryStream = 1` on sync channels, reducing thread overhead for server-streaming RPCs. Do not override this option. `build_async()` does not set it (the async event loop avoids thread-per-stream overhead natively).

## 2. Async vs Sync Client Selection

- Use `build_async()` for concurrent workloads (parallel Check calls, concurrent stream consumption). It avoids thread-pool exhaustion.
- Use `build()` for CLI tools, scripts, and single-threaded applications where simplicity matters.

## 3. Streaming APIs

### 3.1 Prefer streaming over collecting

`StreamedListObjects` and `StreamedListSubjects` are server-streaming RPCs. Process results as they arrive to reduce peak memory and time-to-first-result.

```python
# Good -- incremental processing
for response in stub.StreamedListObjects(request):
    process(response)

# Bad -- loads entire stream into memory
all_results = list(stub.StreamedListObjects(request))
```

### 3.2 Continuation token pagination

When writing pagination loops over streaming RPCs:
- Extract `continuation_token` from each response's `pagination` field.
- Stop when the token is empty/falsy.
- Pass the token in `RequestPagination(limit=N, continuation_token=token)` on the next request.
- Default limit is `1000` (used by SDK helpers).

`list_workspaces()` and `list_workspaces_async()` in `kessel.rbac.v2` handle pagination automatically.

## 4. Bulk APIs

### 4.1 Use CheckBulk over multiple Check calls

Batch multiple resource-subject-relation triples into a single `CheckBulk` (or `CheckSelfBulk`, `CheckForUpdateBulk`) request to eliminate per-call overhead.

### 4.2 Check vs CheckForUpdate consistency

- `Check`: Eventually consistent. Use for read-path authorization (dashboards, UI gating). Lower latency.
- `CheckForUpdate`: Strongly consistent. Use before write/delete operations. Higher latency.

## 5. Consistency and Write Visibility

### 5.1 Consistency modes on read requests

`CheckRequest`, `StreamedListObjectsRequest`, and `StreamedListSubjectsRequest` accept an optional `Consistency` field:
- `minimize_latency`: Fastest; may use cached/stale data.
- `at_least_as_fresh(ConsistencyToken)`: Ensures data is at least as fresh as the provided token.
- `at_least_as_acknowledged`: Ensures all acknowledged writes are visible.

Omitting consistency lets the server choose. Only set stricter modes when required, as they increase latency.

### 5.2 Write visibility on ReportResource

`ReportResourceRequest.write_visibility`:
- `IMMEDIATE`: Forces visibility to subsequent `Check` calls right away (higher latency).
- `MINIMIZE_LATENCY` or unspecified: Fire-and-forget reporting.

## 6. RBAC HTTP Connection Reuse

Pass a `requests.Session` as `http_client` to `fetch_root_workspace()` and `fetch_default_workspace()` to enable HTTP connection pooling across multiple calls.
