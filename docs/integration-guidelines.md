# Integration Guidelines

## 1. Architecture Overview

This SDK provides two integration pathways to Kessel services:
- **gRPC** (primary): Kessel Inventory Service via generated protobuf stubs (`kessel.inventory.v1beta2`)
- **HTTP/REST** (secondary): RBAC v2 API via the `requests` library (`kessel.rbac.v2`)

Authentication is shared across both pathways via `kessel.auth`, which implements OAuth 2.0 Client Credentials flow with OIDC discovery.

## 2. Protobuf Code Generation (buf.build)

### 2.1 Source of Truth
All protobuf definitions come from `buf.build/project-kessel/inventory-api`. The SDK does NOT vendor `.proto` files -- `buf generate` pulls them directly from the buf.build registry.

### 2.2 Generation Rules
- Run `buf generate` from the repo root. Configuration lives in `buf.gen.yaml`.
- Three plugins are used: `protocolbuffers/pyi` (type stubs), `protocolbuffers/python` (messages), `grpc/python` (service stubs).
- `include_imports: true` is required because `buf.validate` protos are not available on PyPI.
- Output goes to `src/`, producing files under `src/kessel/inventory/`, `src/buf/validate/`, and `src/google/api/`.
- A GitHub Actions workflow (`buf-generate.yml`) runs `buf generate` every 6 hours and auto-creates a PR if files change.

### 2.3 Rules for Generated Files
- Never manually edit `*_pb2.py` or `*_pb2_grpc.py` files.
- Exclude generated files from formatting and linting: `black --exclude '.*_pb2(_grpc)?\.py'` and `flake8 --exclude '*_pb2.py,*_pb2_grpc.py'`.
- Pin buf plugin versions in `buf.gen.yaml` to keep generation reproducible.
- When upgrading the `protobuf` runtime in `pyproject.toml`, ensure the buf plugin version is compatible.

## 3. gRPC Integration -- Kessel Inventory Service

### 3.1 ClientBuilder Pattern
The SDK uses a fluent `ClientBuilder` to construct gRPC stubs. Never create channels manually in production code.

```python
from kessel.inventory.v1beta2 import ClientBuilder

# Insecure (local dev only)
stub, channel = ClientBuilder("localhost:9000").insecure().build()

# Authenticated (staging/prod)
stub, channel = (
    ClientBuilder("inventory.kessel.example.com:443")
    .oauth2_client_authenticated(auth_credentials)
    .build()
)

# Async variant
stub, channel = ClientBuilder(target).oauth2_client_authenticated(creds).build_async()
```

### 3.2 ClientBuilder Integration Rules
- `build()` returns a tuple of `(stub, channel)`. Always close the channel with a context manager.
- `insecure()` uses `grpc.experimental.insecure_channel_credentials()` and clears call credentials. Never combine authentication with insecure channels -- `ClientBuilder` raises `ValueError` if you try.
- `oauth2_client_authenticated()` accepts an optional `channel_credentials` parameter. When omitted, `ssl_channel_credentials()` (TLS) is used by default.
- For local dev behind a proxy, use `grpc.local_channel_credentials()` as the `channel_credentials` argument.
- Sync channels enable `ChannelOptions.SingleThreadedUnaryStream` for unary stream calls. Async channels do not set this option.

### 3.3 Adding a ClientBuilder for a New Kessel Service
To integrate a new gRPC service (e.g., a hypothetical `kessel.notifications.v1`):

1. Add the new module to `buf.gen.yaml` inputs (or create a separate `buf.gen.yaml`).
2. Run `buf generate` to produce stubs under `src/kessel/<service>/`.
3. Create `src/kessel/<service>/__init__.py` with:
   ```python
   from kessel.inventory import client_builder_for_stub
   from kessel.<service>.v1.<service>_service_pb2_grpc import <ServiceName>Stub
   ClientBuilder = client_builder_for_stub(<ServiceName>Stub)
   ```
4. The new `ClientBuilder` inherits all auth/channel patterns automatically.

### 3.4 Target Format
- Targets use `host:port` format (no scheme prefix). Example: `localhost:9000`, `inventory.kessel.example.com:443`.
- Read from environment: `os.environ.get("KESSEL_ENDPOINT", "localhost:9000")`.

### 3.5 Streaming Responses
`StreamedListObjects` and `StreamedListSubjects` return server-side streams. Consume them with:
```python
# Sync
for response in stub.StreamedListObjects(request):
    process(response)

# Async
async for response in stub.StreamedListObjects(request):
    process(response)
```
Handle pagination via `continuation_token` in `ResponsePagination`. See `kessel.rbac.v2.list_workspaces` for the canonical pagination loop pattern.

## 4. RBAC v2 REST API Integration

### 4.1 Module Location
RBAC v2 helpers live in `src/kessel/rbac/v2/__init__.py`. This module bridges gRPC (inventory) and REST (RBAC) by providing:
- Resource/subject reference factories for RBAC types
- HTTP client functions for RBAC workspace queries
- Paginated workspace listing via gRPC streaming

### 4.2 REST Endpoint Pattern
```
GET {rbac_base_endpoint}/api/rbac/v2/workspaces/?type={root|default}
```
- `rbac_base_endpoint` is the full base URL (e.g., `https://rbac.stage.example.com`). Trailing slashes are stripped automatically.
- The `x-rh-rbac-org-id` header is REQUIRED on every request.
- Content-Type is always `application/json`.

### 4.3 Authentication for REST Calls
Use `oauth2_auth_request(credentials)` from `kessel.auth` to create a `requests.auth.AuthBase` handler:
```python
from kessel.auth import oauth2_auth_request
auth = oauth2_auth_request(auth_credentials)
workspace = fetch_default_workspace(rbac_base_endpoint=URL, org_id="12345", auth=auth)
```

### 4.4 HTTP Client Injection
All REST functions accept an optional `http_client` parameter (defaults to the `requests` module). Use this for testing or custom session configuration.

### 4.5 RBAC Resource Conventions
- Principal resource IDs use the format `{domain}/{id}` (e.g., `redhat/alice`).
- Reporter type is always `"rbac"` for RBAC resources.
- Use the provided factory functions: `principal_resource()`, `workspace_resource()`, `role_resource()`, `principal_subject()`, `subject()`.

## 5. Console Identity Helpers (`kessel.console`)

### 5.1 Purpose
The `kessel.console` module provides helpers for console.redhat.com services that receive the `x-rh-identity` header. It extracts a user ID from the identity payload and returns a `SubjectReference` that can be passed directly to inventory gRPC calls (`Check`, `StreamedListObjects`, etc.).

### 5.2 Usage
```python
from kessel.console import principal_from_rh_identity, principal_from_rh_identity_header

# From a parsed identity dict (e.g., after decoding in middleware)
subject = principal_from_rh_identity(identity_dict)

# From the raw base64-encoded header value
subject = principal_from_rh_identity_header(header_value)
```

### 5.3 Rules
- Supports `User` and `ServiceAccount` identity types. Resolves `user_id` from the type-specific sub-dict.
- Raises `ValueError` for unsupported identity types, missing fields, or malformed headers.
- The `domain` parameter defaults to `"redhat"`. Override it when the principal belongs to a different domain.
- This module depends on `kessel.rbac.v2` for the `principal_subject` factory. The HTTP functions in `kessel.rbac.v2` require the `[auth]` extra, but `kessel.console` only uses the pure protobuf helpers and works with a core-only install.

## 6. OIDC Provider Integration

### 6.1 Discovery Flow
```python
from kessel.auth import fetch_oidc_discovery, OAuth2ClientCredentials

discovery = fetch_oidc_discovery(ISSUER_URL)
credentials = OAuth2ClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    token_endpoint=discovery.token_endpoint,
)
```

### 6.2 Rules (OIDC)
- `fetch_oidc_discovery()` makes a synchronous HTTP GET with a 10-second timeout. It strips trailing slashes from the issuer URL before appending `/.well-known/openid-configuration`.
- `OAuth2ClientCredentials` requires a direct `token_endpoint` URL -- it does NOT perform discovery itself. Always call `fetch_oidc_discovery()` first.
- Tokens are cached and automatically refreshed 300 seconds before expiry.

### 6.3 Environment Variables
All examples use these env vars:
| Variable | Purpose |
|---|---|
| `KESSEL_ENDPOINT` | gRPC target (`host:port`) |
| `AUTH_DISCOVERY_ISSUER_URL` | OIDC issuer base URL |
| `AUTH_CLIENT_ID` | OAuth 2.0 client ID |
| `AUTH_CLIENT_SECRET` | OAuth 2.0 client secret |
| `RBAC_BASE_ENDPOINT` | RBAC v2 REST base URL |
| `RBAC_RELATION` | Relation to check (e.g., `view_document`, `member`) |
| `RBAC_SUBJECT_ID` | Subject principal user ID |
| `RBAC_SUBJECT_DOMAIN` | Subject principal domain (e.g., `redhat`) |

## 7. google-auth Library Integration

### 7.1 Adapter Pattern
`GoogleOAuth2ClientCredentials` adapts `OAuth2ClientCredentials` to implement `google.auth.credentials.Credentials`. This adapter is used internally by `oauth2_call_credentials()` in `kessel.grpc`:

```
OAuth2ClientCredentials
    -> GoogleOAuth2ClientCredentials (google.auth.credentials.Credentials)
        -> google.auth.transport.grpc.AuthMetadataPlugin
            -> grpc.metadata_call_credentials
```

### 7.2 Rules (google-auth)
- Never instantiate `GoogleOAuth2ClientCredentials` directly in application code. Use `ClientBuilder.oauth2_client_authenticated()` or `kessel.grpc.oauth2_call_credentials()`.
- The `google-auth` and `requests-oauthlib` packages are optional dependencies (`pip install "kessel-sdk[auth]"`). Code that imports `kessel.auth` will fail without them.
- The `kessel.grpc` module uses `TYPE_CHECKING` guards for the `OAuth2ClientCredentials` import to avoid runtime import errors when auth extras are not installed.

## 8. Multi-Protocol Coordination

### 8.1 Combined gRPC + REST Workflow
Some operations require both protocols. Example: listing RBAC workspaces.

```python
# 1. Auth (shared credentials)
auth_credentials = OAuth2ClientCredentials(...)

# 2. REST: fetch workspace metadata from RBAC v2
auth = oauth2_auth_request(auth_credentials)
default_ws = fetch_default_workspace(rbac_base_endpoint=RBAC_URL, org_id="12345", auth=auth)

# 3. gRPC: query inventory using RBAC resource references
stub, channel = ClientBuilder(KESSEL_ENDPOINT).oauth2_client_authenticated(auth_credentials).build()
with channel:
    for obj in list_workspaces(stub, subject=principal_subject("alice", "redhat"), relation="view_document"):
        ...
```

### 8.2 Rules
- Share a single `OAuth2ClientCredentials` instance across gRPC and REST calls. Token caching/refresh is handled internally.
- gRPC credentials are created via `oauth2_call_credentials()` wrapping the google-auth adapter. REST credentials use `oauth2_auth_request()` wrapping the requests `AuthBase` interface.

## 9. Package Structure and Dependencies

### 9.1 Installation Profiles
| Profile | Command | Use Case |
|---|---|---|
| Core (gRPC only) | `pip install kessel-sdk` | Protobuf + gRPC, no auth |
| With auth | `pip install "kessel-sdk[auth]"` | Adds google-auth, requests-oauthlib |
| Development | `pip install -e ".[dev,auth]"` | Adds flake8, black, pytest, auth extras |

### 9.2 Dependency Constraints
- Python >= 3.11 required.
- `protobuf` is pinned to `>=6.31.1,<6.34.0`. Coordinate with buf plugin versions when updating.
- `grpcio` has no upper bound pin. Test against the latest version before releasing.

## 10. Adding a New Kessel Service Integration Checklist

1. Add the buf.build module to `buf.gen.yaml` inputs and run `buf generate`.
2. Create `src/kessel/<service>/__init__.py` with a `ClientBuilder` via `client_builder_for_stub()`.
3. If the service has REST endpoints, create helper functions following the RBAC v2 pattern (factory functions, `http_client` injection, `auth` parameter).
4. Add an example in `examples/` demonstrating auth + basic usage.
5. Add unit tests in `tests/` covering request construction, error handling, and pagination.
6. Update `pyproject.toml` if new runtime dependencies are needed.
7. Run `black --exclude '.*_pb2(_grpc)?\.py' src/ examples/` and `flake8 --exclude '*_pb2.py,*_pb2_grpc.py' src/ examples/`.
