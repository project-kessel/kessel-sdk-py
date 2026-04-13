"""
Connect-Python client wrapper for API compatibility.

Provides a minimal wrapper that maps PascalCase method names (grpcio convention)
to snake_case method names (Connect-Python convention).

Exceptions propagate naturally as ConnectError - no wrapping needed.
"""

import re


class StubWrapper:
    """
    Minimal wrapper to map stub.Check() -> client.check()

    This wrapper exists solely to maintain API compatibility by converting
    method name casing. Exceptions are not wrapped - they propagate as
    ConnectError naturally.

    Example:
        stub.Check(request)  -> client.check(request)
        stub.ReportResource(request) -> client.report_resource(request)
    """

    def __init__(self, connect_client):
        """
        Initialize wrapper with Connect client.

        Args:
            connect_client: Connect-Python client instance
        """
        self._client = connect_client

    def __getattr__(self, name: str):
        """
        Proxy method calls from PascalCase to snake_case.

        Automatically called when accessing methods like stub.Check().
        Converts to snake_case and returns the Connect client's method.

        Args:
            name: Method name in PascalCase (e.g., "Check", "ReportResource")

        Returns:
            The Connect client's snake_case method

        Raises:
            AttributeError: If the method doesn't exist on Connect client
        """
        snake_case_name = self._to_snake_case(name)

        # Check if Connect client has this method
        if not hasattr(self._client, snake_case_name):
            raise AttributeError(
                f"'{type(self._client).__name__}' has no method '{snake_case_name}' "
                f"(mapped from '{name}')"
            )

        # Return the method directly - no wrapper needed
        return getattr(self._client, snake_case_name)

    @staticmethod
    def _to_snake_case(name: str) -> str:
        """
        Convert PascalCase to snake_case.

        Examples:
            Check -> check
            CheckSelf -> check_self
            ReportResource -> report_resource
            StreamedListObjects -> streamed_list_objects

        Args:
            name: PascalCase string

        Returns:
            snake_case string
        """
        # Insert underscore before uppercase letters (except first)
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        # Insert underscore before uppercase letters preceded by lowercase/digit
        s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
        # Convert to lowercase
        return s2.lower()


class AsyncStubWrapper:
    """
    Minimal async wrapper to map stub.Check() -> client.check()

    Same as StubWrapper but for async clients.
    """

    def __init__(self, connect_client):
        """
        Initialize wrapper with Connect async client.

        Args:
            connect_client: Connect-Python async client instance
        """
        self._client = connect_client

    def __getattr__(self, name: str):
        """
        Proxy async method calls from PascalCase to snake_case.

        Args:
            name: Method name in PascalCase

        Returns:
            The Connect client's snake_case method

        Raises:
            AttributeError: If the method doesn't exist on Connect client
        """
        snake_case_name = self._to_snake_case(name)

        if not hasattr(self._client, snake_case_name):
            raise AttributeError(
                f"'{type(self._client).__name__}' has no method '{snake_case_name}' "
                f"(mapped from '{name}')"
            )

        # Return the method directly - no wrapper needed
        return getattr(self._client, snake_case_name)

    @staticmethod
    def _to_snake_case(name: str) -> str:
        """Convert PascalCase to snake_case."""
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
        return s2.lower()


class ChannelWrapper:
    """
    Wraps Connect client to provide channel-like context manager.

    Provides compatibility with grpcio's channel context manager pattern.
    """

    def __init__(self, connect_client):
        """
        Initialize wrapper with Connect client.

        Args:
            connect_client: Connect-Python client
        """
        self._client = connect_client

    def __enter__(self):
        """Enter context manager."""
        # Connect clients don't have context managers, just return self
        return self

    def __exit__(self, *args):
        """Exit context manager."""
        # Connect clients don't need explicit cleanup
        pass

    def close(self):
        """Close the underlying client."""
        if hasattr(self._client, "close"):
            return self._client.close()


class AsyncChannelWrapper:
    """
    Wraps async Connect client to provide channel-like async context manager.
    """

    def __init__(self, connect_client):
        """
        Initialize wrapper with async Connect client.

        Args:
            connect_client: Connect-Python async client
        """
        self._client = connect_client

    async def __aenter__(self):
        """Enter async context manager."""
        # Connect clients don't have context managers, just return self
        return self

    async def __aexit__(self, *args):
        """Exit async context manager."""
        # Connect clients don't need explicit cleanup
        pass

    async def close(self):
        """Close the underlying client."""
        if hasattr(self._client, "close"):
            return await self._client.close()
