"""
Kessel Inventory SDK client builder.

This module exports ClientBuilder for creating gRPC clients to Kessel services.
As of v3.0, this uses Connect-Python internally for pure Python implementation
and faster builds, while maintaining backwards-compatible API.
"""

from kessel.inventory.client_builder import ClientBuilder

__all__ = ["ClientBuilder"]
