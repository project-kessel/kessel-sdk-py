import pytest
from unittest.mock import Mock

from kessel.rbac.v2 import (
    workspace_type,
    role_type,
    principal_resource,
    role_resource,
    workspace_resource,
    principal_subject,
    subject,
    list_workspaces,
)
from kessel.inventory.v1beta2.streamed_list_objects_response_pb2 import StreamedListObjectsResponse
from kessel.inventory.v1beta2.response_pagination_pb2 import ResponsePagination


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


class TestListWorkspaces:
    def test_builds_request_with_correct_parameters(self):
        """Test that list_workspaces builds request with correct parameters"""
        mock_inventory = Mock()
        response = StreamedListObjectsResponse(
            pagination=ResponsePagination(continuation_token="")
        )
        mock_inventory.StreamedListObjects.return_value = iter([response])
        
        subj = principal_subject("user123", "redhat")
        
        responses = list[StreamedListObjectsResponse](list_workspaces(mock_inventory, subj, "member"))
        
        assert len(responses) == 1
        
        assert mock_inventory.StreamedListObjects.call_count == 1
        call_args = mock_inventory.StreamedListObjects.call_args[0][0]
        
        assert call_args.relation == "member"
        assert call_args.object_type.resource_type == "workspace"
        assert call_args.object_type.reporter_type == "rbac"
        assert call_args.subject == subj

    def test_handles_pagination_with_continuation_token(self):
        """Test that list_workspaces handles pagination with continuation token"""
        mock_inventory = Mock()
        
        # First call returns a continuation token
        response1 = StreamedListObjectsResponse(
            pagination=ResponsePagination(continuation_token="next-page-token")
        )
        # Second call returns empty continuation token (end of pagination)
        response2 = StreamedListObjectsResponse(
            pagination=ResponsePagination(continuation_token="")
        )
        
        mock_inventory.StreamedListObjects.side_effect = [
            iter([response1]),
            iter([response2]),
        ]
        
        subj = principal_subject("user123", "redhat")
        
        responses = list(list_workspaces(mock_inventory, subj, "viewer"))
        
        assert len(responses) == 2
        
        assert mock_inventory.StreamedListObjects.call_count == 2
        
        second_call_args = mock_inventory.StreamedListObjects.call_args_list[1][0][0]
        assert second_call_args.pagination is not None
        assert second_call_args.pagination.continuation_token == "next-page-token"

    def test_stops_when_no_continuation_token(self):
        """Test that list_workspaces stops when no continuation token is present"""
        mock_inventory = Mock()
        response = StreamedListObjectsResponse(
            pagination=ResponsePagination(continuation_token="")
        )
        mock_inventory.StreamedListObjects.return_value = iter([response])
        
        subj = principal_subject("user123", "redhat")
        
        responses = list(list_workspaces(mock_inventory, subj, "admin"))
        
        assert mock_inventory.StreamedListObjects.call_count == 1
        assert len(responses) == 1

    def test_handles_stream_errors(self):
        """Test that list_workspaces properly propagates stream errors"""
        mock_inventory = Mock()
        mock_inventory.StreamedListObjects.side_effect = Exception("stream failed")
        
        subj = principal_subject("user123", "redhat")
        
        with pytest.raises(Exception, match="stream failed"):
            list(list_workspaces(mock_inventory, subj, "member"))

    def test_uses_provided_continuation_token(self):
        """Test that list_workspaces uses provided continuation token"""
        mock_inventory = Mock()
        response = StreamedListObjectsResponse(
            pagination=ResponsePagination(continuation_token="")
        )
        mock_inventory.StreamedListObjects.return_value = iter([response])
        
        subj = principal_subject("user123", "redhat")
        
        responses = list(list_workspaces(
            mock_inventory, 
            subj, 
            "member", 
            continuation_token="resume-from-here"
        ))
        
        assert len(responses) == 1
        
        call_args = mock_inventory.StreamedListObjects.call_args[0][0]
        assert call_args.pagination is not None
        assert call_args.pagination.continuation_token == "resume-from-here"

    def test_handles_none_continuation_token_initial_request(self):
        """Test that list_workspaces handles None continuation token correctly"""
        mock_inventory = Mock()
        response = StreamedListObjectsResponse(
            pagination=ResponsePagination(continuation_token="")
        )
        mock_inventory.StreamedListObjects.return_value = iter([response])
        
        subj = principal_subject("user123", "redhat")
        
        responses = list(list_workspaces(mock_inventory, subj, "member", continuation_token=None))
        
        assert len(responses) == 1
        
        # Verify the request had no pagination field set 
        call_args = mock_inventory.StreamedListObjects.call_args[0][0]
        if hasattr(call_args, 'HasField'):
            assert not call_args.HasField("pagination")
        else:
            assert call_args.pagination is None

