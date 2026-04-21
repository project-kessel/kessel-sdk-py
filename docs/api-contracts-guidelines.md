# API Contracts Guidelines

AGENTS.md covers protobuf generation workflow (`buf generate`), generated vs hand-written file lists, and the v1beta1 deprecation. This file covers API-level type conventions and versioning rules.

---

## 1. v1beta1 to v1beta2 Evolution

`v1beta1` used resource-specific services (e.g., `KesselK8sClusterService` with `CreateK8sCluster`/`UpdateK8sCluster`/`DeleteK8sCluster`).

`v1beta2` consolidated into a single `KesselInventoryService` with a generic resource model (`ReportResource`/`DeleteResource`) where resource type is a string field. When adding support for a new resource type, use `ReportResource` with the appropriate `type` field value. Do not create a new service definition.

## 2. Request/Response Type Conventions

### 2.1 Naming pattern

Every RPC has a dedicated request and response message in its own `_pb2.py` file named in snake_case:

| Method | Request | Response |
|--------|---------|----------|
| `Check` | `CheckRequest` | `CheckResponse` |
| `CheckSelf` | `CheckSelfRequest` | `CheckSelfResponse` |
| `CheckForUpdate` | `CheckForUpdateRequest` | `CheckForUpdateResponse` |
| `CheckBulk` | `CheckBulkRequest` | `CheckBulkResponse` |
| `CheckSelfBulk` | `CheckSelfBulkRequest` | `CheckSelfBulkResponse` |
| `CheckForUpdateBulk` | `CheckForUpdateBulkRequest` | `CheckForUpdateBulkResponse` |
| `ReportResource` | `ReportResourceRequest` | `ReportResourceResponse` |
| `DeleteResource` | `DeleteResourceRequest` | `DeleteResourceResponse` |
| `StreamedListObjects` | `StreamedListObjectsRequest` | `StreamedListObjectsResponse` |
| `StreamedListSubjects` | `StreamedListSubjectsRequest` | `StreamedListSubjectsResponse` |

Bulk variants use an `Item` message (e.g., `CheckBulkRequestItem`) wrapped in a top-level request with an `items` repeated field.

### 2.2 Shared reference types

Core reusable types in `v1beta2`:
- `ResourceReference` -- identifies a resource (resource_type, resource_id, reporter)
- `SubjectReference` -- identifies a subject (wraps ResourceReference, optional relation)
- `ReporterReference` -- identifies a reporter system (type field)
- `Consistency` -- oneof: minimize_latency, at_least_as_fresh (token), at_least_as_acknowledged
- `RequestPagination` / `ResponsePagination` -- cursor-based pagination with continuation_token
- `WriteVisibility` -- enum: UNSPECIFIED, MINIMIZE_LATENCY, IMMEDIATE
- `Allowed` -- enum: UNSPECIFIED, TRUE, FALSE

### 2.3 Field validation

Fields use `buf.validate` annotations (not manually enforced):
- Required message fields: `[(buf.validate.field).required = true]`
- Required strings: `[(buf.validate.field).string.min_len = 1]`
- Pattern-constrained strings: regex like `^[A-Za-z0-9_-]+$` for type/reporter_type fields

## 3. gRPC Method Patterns

- **Unary** (`unary_unary`): `Check`, `CheckSelf`, `CheckForUpdate`, `CheckForUpdateBulk`, `CheckBulk`, `CheckSelfBulk`, `ReportResource`, `DeleteResource`.
- **Server-streaming** (`unary_stream`): `StreamedListObjects`, `StreamedListSubjects`. Consume with `for`/`async for`. Paginate via `continuation_token`.

## 4. Backward Compatibility

- Never remove a version directory. Old versions must remain importable.
- Removing an API version requires a major version bump (SemVer).
- SDK versions across languages (Python, Ruby, Go) are independent.

## 5. Protobuf Runtime Compatibility

Each `_pb2.py` file contains a runtime version check:

```python
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC, 6, 31, 1, '', ...)
```

The `protobuf` dependency range in `pyproject.toml` must match the version used by the buf plugins in `buf.gen.yaml`. Update both together.
