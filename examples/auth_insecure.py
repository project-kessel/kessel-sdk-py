import os

import grpc
import google.auth.transport.requests
import google.auth.transport.grpc

from kessel.auth import fetch_oidc_discovery, OAuth2ClientCredentials
from kessel.inventory.v1beta2 import (
    check_request_pb2,
    inventory_service_pb2_grpc,
    reporter_reference_pb2,
    resource_reference_pb2,
    subject_reference_pb2,
)

KESSEL_ENDPOINT = os.environ.get("KESSEL_ENDPOINT", "localhost:9000")
ISSUER_URL = os.environ.get("AUTH_DISCOVERY_ISSUER_URL", "")
CLIENT_ID = os.environ.get("AUTH_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("AUTH_CLIENT_SECRET", "")


def run():
    try:
        # network call occurs here
        discovery = fetch_oidc_discovery(ISSUER_URL)
        token_endpoint = discovery.token_endpoint

        # Create OAuth2 credentials with the discovered token endpoint
        auth_credentials = OAuth2ClientCredentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            token_url=token_endpoint,
        )

        auth_plugin = google.auth.transport.grpc.AuthMetadataPlugin(
            credentials=auth_credentials._get_credentials(),
            request=google.auth.transport.requests.Request(),
        )

        call_credentials = grpc.metadata_call_credentials(auth_plugin)

        channel_credentials = grpc.composite_channel_credentials(
            grpc.local_channel_credentials(),
            call_credentials,
        )

        with grpc.secure_channel(KESSEL_ENDPOINT, channel_credentials) as channel:
            stub = inventory_service_pb2_grpc.KesselInventoryServiceStub(channel)

            subject = subject_reference_pb2.SubjectReference(
                resource=resource_reference_pb2.ResourceReference(
                    reporter=reporter_reference_pb2.ReporterReference(type="rbac"),
                    resource_id="alice",
                    resource_type="principal",
                )
            )

            resource_ref = resource_reference_pb2.ResourceReference(
                resource_id="alice_club",
                resource_type="group",
                reporter=reporter_reference_pb2.ReporterReference(type="rbac"),
            )

            request = check_request_pb2.CheckRequest(
                subject=subject,
                relation="member",
                object=resource_ref,
            )

            response = stub.Check(request)
            print("Check response received successfully")
            print(response)

    except grpc.RpcError as e:
        print("gRPC error occurred during Check:")
        print(f"Code: {e.code()}")
        print(f"Details: {e.details()}")


if __name__ == "__main__":
    run()
