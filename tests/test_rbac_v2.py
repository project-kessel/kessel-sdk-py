import pytest

from kessel.rbac.v2 import (
    workspace_type,
    role_type,
    principal_resource,
    role_resource,
    workspace_resource,
    principal_subject,
    subject,
)


def test_workspace_type():
    rt = workspace_type()
    assert rt.resource_type == "workspace"
    assert rt.reporter_type == "rbac"


def test_role_type():
    rt = role_type()
    assert rt.resource_type == "role"
    assert rt.reporter_type == "rbac"


@pytest.mark.parametrize(
    "id,domain,expected_res_id,expected_res_type",
    [
        ("user123", "redhat", "redhat/user123", "principal"),
        ("12345", "example", "example/12345", "principal"),
    ],
)
def test_principal_resource(id, domain, expected_res_id, expected_res_type):
    ref = principal_resource(id, domain)
    assert ref.resource_type == expected_res_type
    assert ref.resource_id == expected_res_id
    assert ref.reporter.type == "rbac"


def test_role_resource():
    ref = role_resource("admin")
    assert ref.resource_type == "role"
    assert ref.resource_id == "admin"
    assert ref.reporter.type == "rbac"


def test_workspace_resource():
    ref = workspace_resource("ws-123")
    assert ref.resource_type == "workspace"
    assert ref.resource_id == "ws-123"
    assert ref.reporter.type == "rbac"


def test_principal_subject():
    subj = principal_subject("user123", "redhat")
    assert subj.resource.resource_type == "principal"
    assert subj.resource.resource_id == "redhat/user123"
    assert not subj.HasField("relation")


@pytest.mark.parametrize(
    "resource_ref,relation,expect_relation,expected_relation",
    [
        (workspace_resource("ws-123"), "member", True, "member"),
        (principal_resource("user123", "redhat"), None, False, None),
    ],
)
def test_subject(resource_ref, relation, expect_relation, expected_relation):
    if relation is not None:
        subj = subject(resource_ref, relation)
    else:
        subj = subject(resource_ref)
    
    assert subj is not None
    assert subj.resource is not None
    
    if expect_relation:
        assert subj.HasField("relation")
        assert subj.relation == expected_relation
    else:
        assert not subj.HasField("relation")

