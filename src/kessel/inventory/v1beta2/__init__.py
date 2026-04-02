"""
Kessel Inventory v1beta2 API.

This module provides access to protobuf message types for the Kessel Inventory v1beta2 API.

For creating clients, use:
    from kessel.inventory import ClientBuilder

As of v3.0, uses Connect-Python for pure Python implementation.
"""

# Re-export ClientBuilder from parent for convenience
# Import is deferred to avoid circular import
def __getattr__(name):
    if name == "ClientBuilder":
        from kessel.inventory import ClientBuilder
        return ClientBuilder
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = ["ClientBuilder"]
