# Testing Guidelines

AGENTS.md covers test file naming (`test_<module>.py`), test function naming (`test_<behavior>`), class naming (`Test<Feature>`), CI workflow, and the pytest/black/flake8 toolchain. This file covers testing patterns and conventions.

---

## 1. Classes vs Bare Functions

- **Bare functions** for testing module-level functions with independent state (see `test_auth.py`).
- **Test classes** to group related tests for a single class or feature (see `test_client_builder.py`). Plain classes, not `unittest.TestCase`.

## 2. Mocking Patterns

### 2.1 `@patch` decorator

Patch at the location where the name is looked up, not where it is defined:

```python
@patch("kessel.inventory.insecure_channel_credentials")
def test_insecure_sets_channel_credentials(self, mock_insecure_creds):
```

### 2.2 `patch.object` context manager

For patching a method on a specific instance:

```python
with patch.object(credentials._session, "fetch_token", return_value=mock_token_data):
    result = credentials.get_token()
```

### 2.3 Mock configuration

- Only `Mock` and `patch` from `unittest.mock` are used. `MagicMock`, `AsyncMock`, `PropertyMock`, `create_autospec` are not used.
- Use `return_value` for expected returns, `side_effect` for exceptions.
- Configure mock responses to match real API structure:

```python
mock_response = Mock()
mock_response.json.return_value = {"data": [...]}
mock_response.raise_for_status = Mock()
mock_requests.get.return_value = mock_response
```

## 3. Async Tests

### 3.1 Marking

Always use `@pytest.mark.asyncio` on every async test method. Async tests live alongside sync tests.

### 3.2 Mocking async iterators

Mock streaming gRPC responses with local async generator functions:

```python
async def async_iter():
    yield response

mock_inventory.StreamedListObjects.return_value = async_iter()
```

For paginated multi-page scenarios, use `side_effect` with a list of async iterators:

```python
mock_inventory.StreamedListObjects.side_effect = [async_iter1(), async_iter2()]
```

## 4. Assertions

- Use plain `assert` (not `self.assertEqual`).
- Use `pytest.raises` with `match=` for exception message verification:

```python
with pytest.raises(ValueError, match="No default workspace found"):
    fetch_default_workspace(...)
```

- Verify mock calls with `assert_called_once_with(...)`, `assert_not_called()`, `call_count`, `call_args`.

## 5. Parameterized Tests

Use `@pytest.mark.parametrize` when the same assertion logic applies to multiple inputs:

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

## 6. What is NOT Tested

- Generated protobuf files (`*_pb2.py`, `*_pb2_grpc.py`).
- `build()` / `build_async()` methods on `ClientBuilder` (real gRPC channel creation).
- `oauth2_call_credentials` in `kessel.grpc` (depends on google-auth transport).
- Integration or end-to-end tests against a live Kessel service.

## 7. Writing Tests for New SDK Features

1. Create or extend a test file in `tests/` following `test_<module>.py`.
2. Never make network calls. Mock all external dependencies.
3. Patch at the import site, not at the definition site.
4. Test both success and error paths.
5. For sync generators, consume with `list()` and assert on collected results.
6. For async generators, use `@pytest.mark.asyncio`, create local `async def` generator functions for mocking, consume with `async for`.
7. For builder/fluent APIs, verify method chaining returns `self` and internal state is set correctly.
8. Add docstrings to every test function.
9. Group related tests in a class.
10. Use `@pytest.mark.parametrize` for multiple input combinations.
