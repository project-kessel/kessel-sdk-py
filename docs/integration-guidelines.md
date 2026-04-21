# Integration Guidelines

AGENTS.md covers the ClientBuilder fluent pattern, `client_builder_for_stub()` factory, google-auth adapter, dual-protocol architecture, protobuf code generation, and package dependencies. This file covers integration-specific patterns and workflows.

---

## 1. Adding a ClientBuilder for a New Kessel Service

To integrate a new gRPC service (e.g., `kessel.notifications.v1`):

1. Add the module to `buf.gen.yaml` inputs (or create a separate `buf.gen.yaml`).
2. Run `buf generate` to produce stubs under `src/kessel/<service>/`.
3. Create `src/kessel/<service>/__init__.py`:
   ```python
   from kessel.inventory import client_builder_for_stub
   from kessel.<service>.v1.<service>_service_pb2_grpc import <ServiceName>Stub
   ClientBuilder = client_builder_for_stub(<ServiceName>Stub)
   ```
4. The new `ClientBuilder` inherits all auth/channel patterns automatically.

## 2. gRPC Target Format

Targets use `host:port` format with no scheme prefix:
- `localhost:9000` (local dev)
- `inventory.kessel.example.com:443` (production)

Read from environment: `os.environ.get("KESSEL_ENDPOINT", "localhost:9000")`.

## 3. RBAC v2 REST API

### 3.1 Endpoint pattern

```
GET {rbac_base_endpoint}/api/rbac/v2/workspaces/?type={root|default}
```

- `rbac_base_endpoint` is the full base URL. Trailing slashes are stripped automatically.
- The `x-rh-rbac-org-id` header is required on every request.
- Content-Type is always `application/json`.

### 3.2 Authentication for REST calls

Use `oauth2_auth_request(credentials)` from `kessel.auth`:

```python
from kessel.auth import oauth2_auth_request

auth = oauth2_auth_request(auth_credentials)
workspace = fetch_default_workspace(rbac_base_endpoint=URL, org_id="12345", auth=auth)
```

### 3.3 HTTP client injection

All REST functions accept an optional `http_client` parameter (defaults to the `requests` module). Use for testing or custom session configuration.

### 3.4 Resource conventions

- Principal resource IDs: `{domain}/{id}` (e.g., `redhat/alice`).
- Reporter type is always `"rbac"` for RBAC resources.
- Use factory functions: `principal_resource()`, `workspace_resource()`, `role_resource()`, `principal_subject()`, `subject()`.

## 4. Environment Variables

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

## 5. Multi-Protocol Coordination

Some operations require both gRPC and REST. Share a single `OAuth2ClientCredentials` instance across both:

```python
# 1. Shared auth
auth_credentials = OAuth2ClientCredentials(...)

# 2. REST: fetch workspace metadata
auth = oauth2_auth_request(auth_credentials)
default_ws = fetch_default_workspace(rbac_base_endpoint=RBAC_URL, org_id="12345", auth=auth)

# 3. gRPC: query inventory
stub, channel = ClientBuilder(KESSEL_ENDPOINT).oauth2_client_authenticated(auth_credentials).build()
with channel:
    for obj in list_workspaces(stub, subject=principal_subject("alice", "redhat"), relation="view_document"):
        ...
```

gRPC credentials use `oauth2_call_credentials()` (google-auth adapter). REST credentials use `oauth2_auth_request()` (requests `AuthBase`).

## 6. New Kessel Service Integration Checklist

1. Add the buf.build module to `buf.gen.yaml` and run `buf generate`.
2. Create `src/kessel/<service>/__init__.py` with a `ClientBuilder` via `client_builder_for_stub()`.
3. If the service has REST endpoints, create helpers following the RBAC v2 pattern (factory functions, `http_client` injection, `auth` parameter).
4. Add an example in `examples/`.
5. Add unit tests in `tests/`.
6. Update `pyproject.toml` if new runtime dependencies are needed.
