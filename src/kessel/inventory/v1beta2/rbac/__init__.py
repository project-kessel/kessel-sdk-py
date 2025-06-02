from kessel.inventory.v1beta2.reporter_reference_pb2 import ReporterReference
from kessel.inventory.v1beta2.resource_reference_pb2 import ResourceReference
from kessel.inventory.v1beta2.subject_reference_pb2 import SubjectReference


REPORTER = ReporterReference(type="rbac")


def principal_resource_for_user_id(id: str, domain: str) -> ResourceReference:
    return ResourceReference(
        resource_type="principal", reporter=REPORTER, resource_id=f"{domain}/{id}"
    )


def principal_subject_for_user_id(id: str, domain: str) -> SubjectReference:
    return SubjectReference(resource=principal_resource_for_user_id(id, domain))
