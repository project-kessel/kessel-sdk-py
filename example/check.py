import grpc

from kessel import grpc as kessel_grpc
from kessel.inventory.v1beta2 import (
    check_request_pb2,
    inventory_service_pb2_grpc,
    resource_reference_pb2,
    reporter_reference_pb2,
)
from kessel.rbac import v1beta2_resources


def run():
    channel = kessel_grpc.ChannelBuilder.with_defaults_localhost(9000).build()
    stub = inventory_service_pb2_grpc.KesselInventoryServiceStub(channel)

    # Prepare the subject reference object
    subject = v1beta2_resources.principal_subject_for_user_id("bob", "localhost")

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
    except grpc.RpcError as e:
        print("gRPC error occurred during Check:")
        print(f"Code: {e.code()}")
        print(f"Details: {e.details()}")


if __name__ == "__main__":
    run()
