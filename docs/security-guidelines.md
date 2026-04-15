# Security Guidelines

## Scope

These guidelines apply to all contributors and consumers of `kessel-sdk-py`. They cover OAuth 2.0 credential handling, gRPC channel security, token lifecycle management, and the RBAC REST client surface.

---

## 1. Credential Delivery

### 1.1 Use environment variables for all secrets

All examples in this repo follow the pattern of reading credentials from environment variables. This is the only acceptable method.

```python
# CORRECT
CLIENT_ID     = os.environ.get("AUTH_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("AUTH_CLIENT_SECRET", "")
ISSUER_URL    = os.environ.get("AUTH_DISCOVERY_ISSUER_URL", "")
```

**Rules:**
- Never hardcode `client_id`, `client_secret`, token endpoints, or org IDs in source code.
- Never provide non-empty default values for credential environment variables. Always default to `""`.
- Never commit `.env` files. The `.gitignore` already excludes `.env`; do not remove that entry.
- Never log or print the values of `client_id`, `client_secret`, or access tokens.

### 1.2 Do not pass credentials through CLI arguments

CLI arguments appear in process listings and shell history. Always use environment variables or mounted secret files instead.

---

## 2. gRPC Channel Security

### 2.1 Default to TLS

`ClientBuilder._build_credentials()` defaults to `ssl_channel_credentials()` when no channel credentials are explicitly provided. Do not change this default.

```python
# CORRECT - defaults to TLS
ClientBuilder(target).oauth2_client_authenticated(creds).build()

# CORRECT - explicit TLS
ClientBuilder(target).oauth2_client_authenticated(creds, ssl_channel_credentials()).build()
```

### 2.2 Never combine authentication with insecure channels in production

`ClientBuilder._validate_credentials()` raises `ValueError` when `oauth2_client_authenticated()` is paired with `insecure_channel_credentials()`. This guard must not be bypassed or removed.

```python
# RAISES ValueError - tokens would be sent in plaintext
ClientBuilder(target).oauth2_client_authenticated(
    creds, insecure_channel_credentials()
).build()
```

### 2.3 Restrict `insecure()` and `local_channel_credentials()` to development

- `ClientBuilder.insecure()` creates an unencrypted, unauthenticated channel. It must only be used against local development servers (`localhost`).
- `grpc.local_channel_credentials()` is acceptable only for same-machine communication. Document this clearly when used.
- Never use either in deployed or staging environments.

### 2.4 Always close channels

Use the `with channel:` (sync) or `async with channel:` (async) context manager pattern demonstrated in examples. Unclosed channels leak connections and file descriptors.

---

## 3. OAuth 2.0 / OIDC

### 3.1 Always use OIDC discovery for the token endpoint

Use `fetch_oidc_discovery(issuer_url)` to obtain the token endpoint dynamically. Do not hardcode token endpoint URLs, as they may rotate.

```python
# CORRECT
discovery = fetch_oidc_discovery(issuer_url)
creds = OAuth2ClientCredentials(client_id, client_secret, discovery.token_endpoint)

# WRONG - hardcoded token endpoint
creds = OAuth2ClientCredentials(client_id, client_secret, "https://sso.example.com/token")
```

### 3.2 OIDC discovery uses HTTPS with a timeout

`fetch_oidc_discovery()` appends `/.well-known/openid-configuration` and sets `timeout=10`. When modifying this function:
- Never remove the timeout. Network calls without timeouts can hang indefinitely.
- Never downgrade from HTTPS to HTTP for the issuer URL.
- Always call `response.raise_for_status()` before parsing JSON.

### 3.3 Client Credentials flow only

This SDK uses `BackendApplicationClient` from `oauthlib` (client credentials grant, no user interaction). Do not introduce authorization code or implicit flows; they are not appropriate for service-to-service communication.

---

## 4. Token Management

### 4.1 Rely on built-in token caching

`OAuth2ClientCredentials.get_token()` caches the access token and auto-refreshes 300 seconds before expiry. Do not implement external caching or store tokens in files/databases.

### 4.2 Do not disable the 300-second refresh buffer

The early-refresh logic (`self._expiry <= current_time + timedelta(seconds=300)`) prevents requests with nearly-expired tokens. Do not reduce this buffer below 60 seconds.

### 4.3 Handle missing `expires_in`

When the token response lacks `expires_in`, the SDK defaults to `0`, causing immediate re-fetch on the next call. This is safe but inefficient. If extending the auth module, prefer failing loudly over silently accepting missing expiry data.

### 4.4 Token thread safety

`OAuth2ClientCredentials` is not thread-safe. The `_token` and `_expiry` fields have no locking. If sharing an instance across threads, wrap `get_token()` calls with a `threading.Lock`. Consider adding a lock if the SDK is extended for concurrent use.

---

## 5. RBAC REST Client (`kessel.rbac.v2`)

### 5.1 Always pass `auth` for non-local calls

`fetch_root_workspace()` and `fetch_default_workspace()` accept an optional `auth` parameter. For any non-local endpoint, always provide authentication:

```python
auth = oauth2_auth_request(credentials)
workspace = fetch_default_workspace(rbac_base_endpoint, org_id, auth=auth)
```

### 5.2 Validate `org_id` before use

The `org_id` is sent as the `x-rh-rbac-org-id` header. Never accept org IDs from untrusted user input without validation. An attacker-controlled org ID could authorize cross-tenant access.

### 5.3 Prefer `http_client` injection for testing

Use the `http_client` parameter to inject a mock or session-based client in tests. Never disable TLS verification on the default `requests` module.

---

## 6. Dependency Security

### 6.1 Auth dependencies are optional

The `[auth]` extra (`google-auth`, `requests-oauthlib`, `requests`) is only installed when needed. This reduces attack surface for consumers that bring their own auth. Do not move auth dependencies into the base `dependencies` list.

### 6.2 Pin dependency ranges

`pyproject.toml` pins `protobuf>=6.31.1,<6.34.0` and `types-protobuf~=6.30` for the base dependencies. Dev dependencies like `flake8` and `black` also use version constraints. Auth dependencies (`google-auth`, `requests-oauthlib`, `requests`) and `grpcio` currently have no version pins. When adding new dependencies, prefer version-pinned ranges for reproducible builds.

### 6.3 Keep Dependabot active

The repository runs daily Dependabot checks for both `pip` and `github-actions`. Do not disable these. Review and merge security updates promptly.

### 6.4 Generated protobuf code

Protobuf/gRPC files (`*_pb2.py`, `*_pb2_grpc.py`) are generated from `buf.build/project-kessel/inventory-api`. Never manually edit these files. Regenerate with `buf generate` and review diffs for unexpected changes after upstream updates.

---

## 7. Code Hygiene

### 7.1 No logging of sensitive data

The `src/kessel/` directory contains zero `print`, `logging`, or `debug` statements. Maintain this. If adding logging:
- Never log access tokens, client secrets, or authorization headers.
- Use structured logging at `INFO` level for connection events, never for credential content.

### 7.2 Use `TYPE_CHECKING` for auth imports

The codebase uses `if TYPE_CHECKING:` guards (in `src/kessel/inventory/__init__.py` and `src/kessel/grpc/__init__.py`) to avoid importing auth modules at runtime when they are not installed. Maintain this pattern for any new auth-related type hints.

### 7.3 Test credentials must be obviously fake

All test files use placeholder values like `"test-client-id"`, `"test-secret"`, `"https://example.com/token"`. Never use real credentials in tests even if mocked. Test credential strings should be clearly synthetic.

### 7.4 Example files are not production code

Examples in `examples/` may use `insecure()` for simplicity when targeting local development servers. Production consumers must use `oauth2_client_authenticated()` with TLS.

---

## 8. Anti-Patterns to Avoid

| Anti-Pattern | Why It Is Dangerous |
|---|---|
| `grpc.insecure_channel()` in production | Sends all data (including tokens) in plaintext |
| Hardcoding `client_secret` in source | Secrets leak via version control |
| Storing tokens in files or databases | Tokens should live only in memory; disk storage widens the attack surface |
| Disabling `raise_for_status()` on OIDC discovery | Silently uses invalid/error responses as configuration |
| Removing the `_validate_credentials` check | Allows authenticated calls over insecure channels |
| Sharing `OAuth2ClientCredentials` across threads without locking | Race conditions can cause duplicate token fetches or stale tokens |
| Accepting `org_id` from user input without validation | Enables cross-tenant RBAC queries |
| Manually editing `*_pb2.py` / `*_pb2_grpc.py` files | Edits are overwritten by `buf generate`; may introduce vulnerabilities |

---

## 9. Security Review Checklist for PRs

- [ ] No secrets or credentials in diff (including defaults for env vars)
- [ ] No new uses of `insecure_channel` or `insecure()` outside `examples/`
- [ ] `_validate_credentials` guard is intact
- [ ] OIDC discovery timeout is preserved
- [ ] Token refresh buffer (300s) is not reduced
- [ ] Auth imports use `TYPE_CHECKING` guards
- [ ] New dependencies are version-pinned
- [ ] Generated protobuf files are not manually modified
- [ ] No `print`/`logging` of tokens, secrets, or auth headers
