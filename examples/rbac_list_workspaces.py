import asyncio
import os

import grpc

from kessel.auth import fetch_oidc_discovery, OAuth2ClientCredentials
from kessel.inventory.v1beta2 import (
    reporter_reference_pb2,
    resource_reference_pb2,
    subject_reference_pb2,
    ClientBuilder,
)
from kessel.rbac.v2 import list_workspaces, list_workspaces_async


KESSEL_ENDPOINT = os.environ.get("KESSEL_ENDPOINT", "localhost:9000")
ISSUER_URL = os.environ.get("AUTH_DISCOVERY_ISSUER_URL", "")
CLIENT_ID = os.environ.get("AUTH_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("AUTH_CLIENT_SECRET", "")

SUBJECT_ID = os.environ.get("RBAC_SUBJECT_ID", "alice")
RELATION = os.environ.get("RBAC_RELATION", "view_document")

def run_sync():
    try:
        discovery = fetch_oidc_discovery(ISSUER_URL)
        token_endpoint = discovery.token_endpoint

        auth_credentials = OAuth2ClientCredentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            token_endpoint=token_endpoint,
        )

        stub, channel = (
            ClientBuilder(KESSEL_ENDPOINT)
            .oauth2_client_authenticated(auth_credentials, grpc.local_channel_credentials())
            .build()
        )

        with channel:
            subject = subject_reference_pb2.SubjectReference(
                resource=resource_reference_pb2.ResourceReference(
                    reporter=reporter_reference_pb2.ReporterReference(type="rbac"),
                    resource_id=SUBJECT_ID,
                    resource_type="principal",
                )
            )
            print(f"Listing workspaces (sync) for subject='{SUBJECT_ID}' relation='{RELATION}'")
            for obj in list_workspaces(stub, subject=subject, relation=RELATION):
                print(f"{obj.resource_id}")

    except grpc.RpcError as e:
        print("gRPC error occurred during list_workspaces (sync):")
        print(f"Code: {e.code()}")
        print(f"Details: {e.details()}")


async def run_async():
    try:
        discovery = fetch_oidc_discovery(ISSUER_URL)
        token_endpoint = discovery.token_endpoint

        auth_credentials = OAuth2ClientCredentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            token_endpoint=token_endpoint,
        )

        stub, channel = (
            ClientBuilder(KESSEL_ENDPOINT)
            .oauth2_client_authenticated(auth_credentials, grpc.local_channel_credentials())
            .build_async()
        )

        async with channel:
            subject = subject_reference_pb2.SubjectReference(
                resource=resource_reference_pb2.ResourceReference(
                    reporter=reporter_reference_pb2.ReporterReference(type="rbac"),
                    resource_id=SUBJECT_ID,
                    resource_type="principal",
                )
            )
            print(f"Listing workspaces (async) for subject='{SUBJECT_ID}' relation='{RELATION}'")
            async for obj in list_workspaces_async(stub, subject=subject, relation=RELATION):
                print(f"{obj.resource_id}")

    except grpc.RpcError as e:
        print("gRPC error occurred during list_workspaces (async):")
        print(f"Code: {e.code()}")
        print(f"Details: {e.details()}")


if __name__ == "__main__":
    run_sync()
    asyncio.run(run_async())
