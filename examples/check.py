import grpc

from kessel.inventory import v1beta2
from kessel.inventory.v1beta2 import (
    CheckRequest,
    ResourceReference,
    ReporterReference,
    rbac,
)


def run():
    stub = v1beta2.ClientBuilder.with_defaults_localhost(9000).build_inventory_stub()

    # Prepare the subject reference object
    subject = rbac.principal_subject_for_user_id("bob", "localhost")

    # Prepare the resource reference object
    resource_ref = ResourceReference(
        resource_id="bob_club",
        resource_type="group",
        reporter=ReporterReference(type="rbac"),
    )

    check_request = CheckRequest(
        subject=subject,
        relation="member",
        object=resource_ref,
    )

    try:
        check_response = stub.Check(check_request)
        print("Check response received successfully")
        print(check_response)
    except grpc.RpcError as e:
        print("gRPC error occurred during Check:")
        print(f"Code: {e.code()}")
        print(f"Details: {e.details()}")


if __name__ == "__main__":
    run()
