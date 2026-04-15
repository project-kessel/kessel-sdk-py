# Testing Guidelines

## Overview

This document defines testing conventions for the `kessel-sdk-py` repository. All tests are unit tests that run without network access or external services. The SDK source lives in `src/kessel/`, and tests live in `tests/`.

## Tooling and Configuration

### Framework
- **pytest** with **pytest-asyncio** for async tests.
- Both are declared in `pyproject.toml` under `[project.optional-dependencies] dev`.
- Install with: `pip install -e ".[dev,auth]"`
- Run tests with: `pytest`

### No pytest configuration section
- There is no `[tool.pytest.ini_options]` in `pyproject.toml`, no `pytest.ini`, no `setup.cfg`, and no `tox.ini`.
- pytest uses default discovery: files matching `test_*.py` in the `tests/` directory.
- Async tests must be explicitly marked with `@pytest.mark.asyncio`.

### Linting
- **black** (line-length 100, target py313) for formatting. Excludes `*_pb2*` files.
- **flake8** (line-length 100) for linting. Excludes `.git`, `__pycache__`, `build`, `dist`, `.venv`, `*_pb2*`.
- Linting runs in a separate CI workflow (`lint.yml`) and does not gate `pytest`.

### CI Workflow
- Defined in `.github/workflows/test.yml`.
- Triggers on push to `main` and pull requests targeting `main`.
- Runs on `ubuntu-latest` with Python 3.11.
- Installs with `pip install -e ".[dev,auth]"`, then runs `pytest` with no flags.
- No coverage enforcement or reporting in CI.

## Test File Organization

### Directory Structure
```
tests/
  __init__.py          # Package marker (contains only a comment)
  test_auth.py         # OAuth2/OIDC auth tests
  test_client_builder.py  # ClientBuilder construction/config tests
  test_rbac_v2.py      # RBAC v2 helpers and workspace fetch tests
  test_console.py      # Console x-rh-identity helper tests
```

### Naming Conventions
- Test files: `test_<module_or_feature>.py`
- Test functions: `test_<behavior_description>` using snake_case.
- Test classes: `Test<ClassName>` or `Test<FeatureName>` (e.g., `TestClientBuilderInsecure`, `TestListWorkspacesAsync`).

### When to Use Classes vs. Bare Functions
- **Bare functions** for testing module-level functions with independent state (see `test_auth.py`).
- **Test classes** to group related tests for a single class or feature (see `test_client_builder.py` grouping by method: `TestClientBuilderConstructor`, `TestClientBuilderInsecure`, etc.).
- Test classes do not inherit from `unittest.TestCase`. They are plain classes used for grouping only.

### File-to-Module Mapping
- `test_auth.py` tests `kessel.auth` (specifically `kessel.auth.auth`).
- `test_client_builder.py` tests `kessel.inventory.ClientBuilder`.
- `test_rbac_v2.py` tests `kessel.rbac.v2` (helper functions and workspace fetchers).
- `test_console.py` tests `kessel.console` (identity parsing and principal construction).
- When adding a new module, create a corresponding `test_<module>.py` in `tests/`.

## Mocking Patterns

### Imports
```python
from unittest.mock import Mock, patch
```
Only `Mock` and `patch` from `unittest.mock` are used. `MagicMock`, `AsyncMock`, `PropertyMock`, `create_autospec` are not used in this codebase.

### `@patch` Decorator Pattern
- Patch at the location where the name is looked up, not where it is defined.
- Use the full dotted path: `@patch("kessel.auth.auth.requests.get")`, `@patch("kessel.inventory.insecure_channel_credentials")`.
- For class-level patches in `test_client_builder.py`, the mock is passed as the first argument after `self`:
```python
@patch("kessel.inventory.insecure_channel_credentials")
def test_insecure_sets_channel_credentials(self, mock_insecure_creds):
```

### `patch.object` Context Manager Pattern
- Used when patching a method on a specific instance (common for `credentials._session`):
```python
with patch.object(credentials._session, "fetch_token", return_value=mock_token_data):
    result = credentials.get_token()
```

### Mock Configuration Conventions
- Use `Mock()` for simple stand-in objects.
- Set `return_value` for expected return values.
- Set `side_effect` for exceptions: `side_effect=Exception("message")`.
- Configure mock responses with proper structure matching the real API:
```python
mock_response = Mock()
mock_response.json.return_value = {"data": [...]}
mock_response.raise_for_status = Mock()
mock_requests.get.return_value = mock_response
```

### Verifying Mock Calls
- `mock.assert_called_once()` or `mock.assert_called_once_with(...)` for single-call verification.
- `mock.assert_not_called()` to verify no interaction.
- `mock.call_count` for numeric verification.
- `mock.call_args` and `mock.call_args_list` to inspect arguments to calls.

## Async Test Patterns

### Marking Async Tests
```python
@pytest.mark.asyncio
async def test_builds_request_with_correct_parameters(self):
```
- Always use `@pytest.mark.asyncio` on every async test method.
- Async tests live alongside sync tests in the same file and class.

### Mocking Async Iterators
- The SDK uses async generators for streaming gRPC responses. Mock them with local async generator functions:
```python
async def async_iter():
    yield response

mock_inventory.StreamedListObjects.return_value = async_iter()
```
- For paginated multi-page scenarios, use `side_effect` with a list of async iterators:
```python
mock_inventory.StreamedListObjects.side_effect = [async_iter1(), async_iter2()]
```

### Consuming Async Iterators in Tests
```python
responses = []
async for resp in list_workspaces_async(mock_inventory, subj, "member"):
    responses.append(resp)
```

## Parametrized Tests

Use `@pytest.mark.parametrize` for testing the same logic with multiple inputs:
```python
@pytest.mark.parametrize(
    "id,domain,expected_res_id,expected_res_type",
    [
        ("user123", "redhat", "redhat/user123", "principal"),
        ("12345", "example", "example/12345", "principal"),
    ],
)
def test_principal_resource(id, domain, expected_res_id, expected_res_type):
```
- Parameter names in the decorator string match function argument names.
- Use parametrize when testing pure helper functions with varied inputs (e.g., resource/subject constructors).

## Assertion Patterns

- Use plain `assert` statements (not `self.assertEqual`).
- Use `pytest.raises` as a context manager for expected exceptions:
```python
with pytest.raises(TypeError):
    ClientBuilder("")

with pytest.raises(Exception, match="stream failed"):
    list(list_workspaces(mock_inventory, subj, "member"))

with pytest.raises(ValueError, match="No default workspace found"):
    fetch_default_workspace(...)
```
- Use `match=` to verify exception message content when the message is meaningful.

## What Gets Tested

### Auth (`test_auth.py`)
- `OAuth2ClientCredentials` initialization, token fetching, caching, expiry, force-refresh, error handling.
- `RefreshTokenResponse` data class.
- `OIDCDiscoveryMetadata` and `fetch_oidc_discovery` (OIDC discovery endpoint behavior, URL normalization, HTTP errors).
- `AuthRequest` callable (Bearer token injection into request headers).
- `GoogleOAuth2ClientCredentials` adapter (token property delegation, refresh delegation).

### Client Builder (`test_client_builder.py`)
- Constructor validation (empty, None, non-string targets).
- `insecure()`, `unauthenticated()`, `authenticated()`, `oauth2_client_authenticated()` methods.
- Method chaining (returns `self`).
- Credential validation (rejecting auth over insecure channel).
- `build()` and `build_async()` are NOT tested (they create real gRPC channels).

### RBAC v2 (`test_rbac_v2.py`)
- Protobuf helper functions (`workspace_type`, `role_type`, `principal_resource`, `role_resource`, `workspace_resource`, `principal_subject`, `subject`).
- `list_workspaces` sync generator (request construction, pagination, error propagation, continuation tokens).
- `list_workspaces_async` async generator (mirrors sync tests).
- `fetch_default_workspace` and `fetch_root_workspace` (HTTP calls, URL construction, headers, auth passthrough, custom HTTP client, error handling, empty results).

### Console (`test_console.py`)
- `_extract_user_id` (User and ServiceAccount identity types, missing/empty user_id, unsupported types, malformed input).
- `principal_from_rh_identity` (builds SubjectReference from parsed identity dict, custom domain, error propagation).
- `principal_from_rh_identity_header` (base64 decoding, JSON parsing, envelope validation, end-to-end header-to-SubjectReference).

### What is NOT Tested
- Generated protobuf files (`*_pb2.py`, `*_pb2_grpc.py`).
- `build()` / `build_async()` methods on `ClientBuilder` (real gRPC channel creation).
- `oauth2_call_credentials` in `kessel.grpc` (depends on google-auth transport).
- Integration or end-to-end tests against a live Kessel service.

## Writing Tests for New SDK Features

1. **Create or extend a test file** in `tests/` following the `test_<module>.py` convention.
2. **Never make network calls.** Mock all external dependencies (gRPC stubs, HTTP clients, OAuth sessions) using `unittest.mock.Mock` and `@patch`.
3. **Patch at the import site**, not at the definition site.
4. **Test both success and error paths.** Include tests for HTTP errors, empty responses, invalid input, and edge cases.
5. **For sync generators**, consume with `list()` and assert on the collected results.
6. **For async generators**, use `@pytest.mark.asyncio`, create local `async def` generator functions for mocking, and consume with `async for`.
7. **For builder/fluent APIs**, verify method chaining returns `self` and that internal state is set correctly.
8. **Add docstrings** to every test function describing the specific behavior being verified.
9. **Group related tests** in a class when testing multiple aspects of the same class or feature.
10. **Use `@pytest.mark.parametrize`** when the same assertion logic applies to multiple input combinations.
11. **Format with black** before committing: `black --exclude '.*_pb2(_grpc)?\.py' src/ tests/`
12. **Run the full suite** before pushing: `pytest`
