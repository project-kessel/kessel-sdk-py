import os

import grpc
import google.auth.transport.requests

from kessel.grpc.auth import OAuth2ClientCredentials
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


def get_auth_metadata(credentials):
    # refresh before sending request
    if not credentials.valid:
        credentials.refresh(google.auth.transport.requests.Request())
    
    return [('authorization', f'Bearer {credentials.token}')]


def run():
    try:
        auth_credentials = OAuth2ClientCredentials(
            issuer_url=ISSUER_URL,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
        )

        with grpc.insecure_channel(KESSEL_ENDPOINT) as channel:
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

            metadata = get_auth_metadata(auth_credentials)
            
            # add authorization header to request
            response = stub.Check(request, metadata=metadata)
            print("Check response received successfully")
            print(response)

    except grpc.RpcError as e:
        print("gRPC error occurred during Check:")
        print(f"Code: {e.code()}")
        print(f"Details: {e.details()}")


if __name__ == "__main__":
    run()
