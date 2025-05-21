import grpc

import kessel.grpc as ksl_channels
from kessel.inventory.v1beta2 import (
    inventory_service_pb2_grpc,
    check_for_update_request_pb2,
    subject_reference_pb2,
    resource_reference_pb2,
    reporter_reference_pb2
)


def run():
    channel = ksl_channels.insecure("localhost:9000")
    stub = inventory_service_pb2_grpc.KesselInventoryServiceStub(channel)

    # Prepare the subject reference object
    subject = subject_reference_pb2.SubjectReference(
        resource=resource_reference_pb2.ResourceReference(
            resource_id="bob",
            resource_type="principal",
            reporter=reporter_reference_pb2.ReporterReference(
                type="rbac"
            )
        )
    )

    # Prepare the resource reference object
    resource_ref = resource_reference_pb2.ResourceReference(
        resource_id="bob_club",
        resource_type="group",
        reporter=reporter_reference_pb2.ReporterReference(
            type="rbac"
        )
    )

    checkforupdate_request = check_for_update_request_pb2.CheckForUpdateRequest(
        subject=subject,
        relation="member",
        object=resource_ref,
    )

    try:
        checkforupdate_response = stub.CheckForUpdate(checkforupdate_request)
        print("CheckForUpdate response received successfully")
        print(checkforupdate_response)
    except grpc.RpcError as e:
        print("gRPC error occurred during CheckForUpdate:")
        print(f"Code: {e.code()}")
        print(f"Details: {e.details()}")


if __name__ == "__main__":
    run()