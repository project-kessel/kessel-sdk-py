import grpc
import os

from kessel.inventory.v1beta2 import (
    check_bulk_request_pb2,
    check_bulk_response_pb2,
    resource_reference_pb2,
    reporter_reference_pb2,
    subject_reference_pb2,
    allowed_pb2,
    ClientBuilder,
)

KESSEL_ENDPOINT = os.environ.get("KESSEL_ENDPOINT", "localhost:9000")


def run():
    stub, channel = ClientBuilder(KESSEL_ENDPOINT).insecure().build()

    with channel:        
        # Item 1: Check if bob is a member of bob_club
        item1 = check_bulk_request_pb2.CheckBulkRequestItem(
            object=resource_reference_pb2.ResourceReference(
                resource_id="bob_club",
                resource_type="group",
                reporter=reporter_reference_pb2.ReporterReference(type="rbac"),
            ),
            relation="member",
            subject=subject_reference_pb2.SubjectReference(
                resource=resource_reference_pb2.ResourceReference(
                    reporter=reporter_reference_pb2.ReporterReference(type="rbac"),
                    resource_id="bob",
                    resource_type="principal",
                )
            ),
        )

        # Item 2: Check if bob is a member of alice_club
        item2 = check_bulk_request_pb2.CheckBulkRequestItem(
            object=resource_reference_pb2.ResourceReference(
                resource_id="alice_club",
                resource_type="group",
                reporter=reporter_reference_pb2.ReporterReference(type="rbac"),
            ),
            relation="member",
            subject=subject_reference_pb2.SubjectReference(
                resource=resource_reference_pb2.ResourceReference(
                    reporter=reporter_reference_pb2.ReporterReference(type="rbac"),
                    resource_id="bob",
                    resource_type="principal",
                )
            ),
        )

        # Item 3: Check if alice is an admin of alice_club
        item3 = check_bulk_request_pb2.CheckBulkRequestItem(
            object=resource_reference_pb2.ResourceReference(
                resource_id="alice_club",
                resource_type="group",
                reporter=reporter_reference_pb2.ReporterReference(type="rbac"),
            ),
            relation="admin",
            subject=subject_reference_pb2.SubjectReference(
                resource=resource_reference_pb2.ResourceReference(
                    reporter=reporter_reference_pb2.ReporterReference(type="rbac"),
                    resource_id="alice",
                    resource_type="principal",
                )
            ),
        )

        check_bulk_request = check_bulk_request_pb2.CheckBulkRequest(
            items=[item1, item2, item3]
        )

        try:
            check_bulk_response = stub.CheckBulk(check_bulk_request)
            print("CheckBulk response received successfully")
            print(f"Total pairs in response: {len(check_bulk_response.pairs)}\n")

            for idx, pair in enumerate(check_bulk_response.pairs):
                print(f"--- Result {idx + 1} ---")
                
                req = pair.request
                print(f"Request: subject={req.subject.resource.resource_id} "
                      f"relation={req.relation} "
                      f"object={req.object.resource_id}")
                
                if pair.HasField("item"):
                    print(pair.item)
                elif pair.HasField("error"):
                    print(f"Error: Code={pair.error.code}, Message={pair.error.message}")
                
                print()

        except grpc.RpcError as e:
            print("gRPC error occurred during CheckBulk:")
            print(f"Code: {e.code()}")
            print(f"Details: {e.details()}")


if __name__ == "__main__":
    run()

