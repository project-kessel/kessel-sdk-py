import grpc

from kessel.inventory import v1beta2
from kessel.inventory.v1beta2 import (
    delete_resource_request_pb2,
    resource_reference_pb2,
    reporter_reference_pb2,
)


def run():
    stub = v1beta2.ClientBuilder.with_defaults_localhost(9000).build_inventory_stub()

    delete_request = delete_resource_request_pb2.DeleteResourceRequest(
        reference=resource_reference_pb2.ResourceReference(
            resource_type="host",
            resource_id="854589f0-3be7-4cad-8bcd-45e18f33cb81",
            reporter=reporter_reference_pb2.ReporterReference(type="HBI"),
        )
    )

    # Send gRPC request
    try:
        response = stub.DeleteResource(delete_request)
        print("Resource deleted successfully")
        print(response)
    except grpc.RpcError as e:
        print("gRPC error occurred:")
        print(f"Code: {e.code()}")
        print(f"Details: {e.details()}")


if __name__ == "__main__":
    run()
