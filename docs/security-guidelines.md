# Security Guidelines

Cross-cutting rules (credential handling, generated file restrictions, TYPE_CHECKING guards, dependency pinning, PR expectations) are in AGENTS.md. This file covers security-specific depth.

---

## 1. Credential Delivery

- Never provide non-empty default values for credential environment variables. Always default to `""`.
- Never log or print the values of `client_id`, `client_secret`, or access tokens.
- Never pass credentials through CLI arguments -- they appear in process listings and shell history.
- All test credentials must be obviously fake (e.g., `"test-client-id"`, `"test-secret"`, `"https://example.com/token"`). Never use real credentials in tests.

## 2. gRPC Channel Security

### 2.1 Default to TLS

`ClientBuilder._build_credentials()` defaults to `ssl_channel_credentials()` when no channel credentials are explicitly provided. Do not change this default.

### 2.2 Insecure + authenticated guard

`ClientBuilder._validate_credentials()` raises `ValueError` when `oauth2_client_authenticated()` is paired with `insecure_channel_credentials()`. This guard must not be bypassed or removed.

### 2.3 Restrict `insecure()` and `local_channel_credentials()` to development

- `ClientBuilder.insecure()` must only be used against local development servers (`localhost`).
- `grpc.local_channel_credentials()` is acceptable only for same-machine communication.
- Never use either in deployed or staging environments.

### 2.4 Always close channels

Use `with channel:` (sync) or `async with channel:` (async). Unclosed channels leak connections and file descriptors.

## 3. OAuth 2.0 / OIDC

### 3.1 Always use OIDC discovery for the token endpoint

Use `fetch_oidc_discovery(issuer_url)` to obtain the token endpoint dynamically. Do not hardcode token endpoint URLs.

### 3.2 OIDC discovery constraints

`fetch_oidc_discovery()` appends `/.well-known/openid-configuration` and sets `timeout=10`. When modifying this function:
- Never remove the timeout.
- Never downgrade from HTTPS to HTTP for the issuer URL.
- Always call `response.raise_for_status()` before parsing JSON.

### 3.3 Client Credentials flow only

This SDK uses `BackendApplicationClient` (client credentials grant). Do not introduce authorization code or implicit flows.

## 4. Token Management

### 4.1 Built-in caching

`OAuth2ClientCredentials.get_token()` caches the access token and auto-refreshes 300 seconds before expiry. Do not implement external caching or store tokens in files/databases.

### 4.2 Do not reduce the 300-second refresh buffer

The early-refresh logic (`self._expiry <= current_time + timedelta(seconds=300)`) prevents requests with nearly-expired tokens. Do not reduce below 60 seconds.

### 4.3 Missing `expires_in`

When the token response lacks `expires_in`, the SDK defaults to `0`, causing immediate re-fetch. This is safe but inefficient. Prefer failing loudly over silently accepting missing expiry data.

### 4.4 Thread safety

`OAuth2ClientCredentials` is not thread-safe. `_token` and `_expiry` have no locking. If sharing across threads, wrap `get_token()` with a `threading.Lock`.

## 5. RBAC REST Client

### 5.1 Validate `org_id` before use

The `org_id` is sent as the `x-rh-rbac-org-id` header. Never accept org IDs from untrusted user input without validation -- an attacker-controlled org ID could authorize cross-tenant access.

### 5.2 Always pass `auth` for non-local calls

`fetch_root_workspace()` and `fetch_default_workspace()` accept an optional `auth` parameter. Always provide authentication for any non-local endpoint.

## 6. Code Hygiene

- The `src/kessel/` directory contains zero `print`, `logging`, or `debug` statements. Maintain this. If adding logging, never log access tokens, client secrets, or authorization headers.
- Example files in `examples/` may use `insecure()` for simplicity when targeting local dev servers. Production consumers must use `oauth2_client_authenticated()` with TLS.
