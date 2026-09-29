"""Keepalive configuration examples.

Every SDK-built channel has HTTP/2 keepalive enabled by default
(interval 45 s, ACK timeout 10 s, pings permitted without active RPCs).
Use ``ClientBuilder.keepalive()`` to override individual values.
"""

import os
from datetime import timedelta

from kessel.inventory.v1beta2 import ClientBuilder

KESSEL_ENDPOINT = os.environ.get("KESSEL_ENDPOINT", "localhost:9000")


def run_with_defaults():
    """Build a channel with the default keepalive policy (no extra call needed)."""
    stub, channel = ClientBuilder(KESSEL_ENDPOINT).insecure().build()
    with channel:
        print("Channel built with default keepalive policy")
        print("  interval=45s, timeout=10s, permit_without_calls=True")


def run_with_custom_keepalive():
    """Build a channel with a custom keepalive policy."""
    stub, channel = (
        ClientBuilder(KESSEL_ENDPOINT)
        .insecure()
        .keepalive(
            interval=timedelta(seconds=30),
            timeout=timedelta(seconds=5),
            permit_without_calls=True,
        )
        .build()
    )
    with channel:
        print("Channel built with custom keepalive policy")
        print("  interval=30s, timeout=5s, permit_without_calls=True")


def run_async_with_keepalive():
    """Build an async channel with a custom keepalive policy."""
    stub, channel = (
        ClientBuilder(KESSEL_ENDPOINT)
        .insecure()
        .keepalive(interval=timedelta(seconds=60))
        .build_async()
    )
    print("Async channel built with 60s keepalive interval")
    print("  (remaining defaults: timeout=10s, permit_without_calls=True)")


if __name__ == "__main__":
    run_with_defaults()
    run_with_custom_keepalive()
    run_async_with_keepalive()
