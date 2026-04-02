import os
from connectrpc.errors import ConnectError

from kessel.inventory.v1beta2 import (
    check_request_pb2,
    resource_reference_pb2,
    reporter_reference_pb2,
    subject_reference_pb2,
    ClientBuilder,
)

KESSEL_ENDPOINT = os.environ.get("KESSEL_ENDPOINT", "localhost:9000")


def run():
    stub, channel = ClientBuilder(KESSEL_ENDPOINT).insecure().build()

    with channel:

        # Prepare the subject reference object
        subject = subject_reference_pb2.SubjectReference(
            resource=resource_reference_pb2.ResourceReference(
                reporter=reporter_reference_pb2.ReporterReference(type="rbac"),
                resource_id="bob",
                resource_type="principal",
            )
        )

        # Prepare the resource reference object
        resource_ref = resource_reference_pb2.ResourceReference(
            resource_id="bob_club",
            resource_type="group",
            reporter=reporter_reference_pb2.ReporterReference(type="rbac"),
        )

        check_request = check_request_pb2.CheckRequest(
            subject=subject,
            relation="member",
            object=resource_ref,
        )

        try:
            check_response = stub.Check(check_request)
            print("Check response received successfully")
            print(check_response)
        except ConnectError as e:
            print("RPC error occurred during Check:")
            print(f"Code: {e.code}")
            print(f"Message: {e.message}")


if __name__ == "__main__":
    run()
