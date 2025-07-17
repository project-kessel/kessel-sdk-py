import grpc

from kessel.inventory import v1beta2
from kessel.inventory.v1beta2 import (
    DeleteResourceRequest,
    ResourceReference,
    ReporterReference,
)


def run():
    stub = v1beta2.KesselInventoryServiceStub(
        grpc.insecure_channel("localhost:9000")
    )

    delete_request = DeleteResourceRequest(
        reference=ResourceReference(
            resource_type="host",
            resource_id="854589f0-3be7-4cad-8bcd-45e18f33cb81",
            reporter=ReporterReference(type="HBI"),
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
