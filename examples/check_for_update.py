import grpc

import kessel.inventory.v1beta2 as v1beta2
from kessel.inventory.v1beta2 import (
    CheckForUpdateRequest,
    ResourceReference,
    ReporterReference,
    SubjectReference,
)


def run():
    stub = v1beta2.KesselInventoryServiceStub(grpc.insecure_channel("localhost:9000"))

    # Prepare the subject reference object
    subject = SubjectReference(
        resource=ResourceReference(
            reporter=ReporterReference(type="rbac"), resource_id="bob", resource_type="principal"
        )
    )

    # Prepare the resource reference object
    resource_ref = ResourceReference(
        resource_id="bob_club",
        resource_type="group",
        reporter=ReporterReference(type="rbac"),
    )

    checkforupdate_request = CheckForUpdateRequest(
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
