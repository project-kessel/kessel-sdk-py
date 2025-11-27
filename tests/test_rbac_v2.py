import pytest
from unittest.mock import Mock, patch

from kessel.rbac.v2 import (
    workspace_type,
    role_type,
    principal_resource,
    role_resource,
    workspace_resource,
    principal_subject,
    subject,
    list_workspaces,
    list_workspaces_async,
    fetch_root_workspace,
    fetch_default_workspace,
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


class TestListWorkspacesAsync:
    @pytest.mark.asyncio
    async def test_builds_request_with_correct_parameters(self):
        """Test that list_workspaces_async builds request with correct parameters"""
        mock_inventory = Mock()
        response = StreamedListObjectsResponse(
            pagination=ResponsePagination(continuation_token="")
        )
        
        async def async_iter():
            yield response
        
        mock_inventory.StreamedListObjects.return_value = async_iter()
        
        subj = principal_subject("user123", "redhat")
        
        responses = []
        async for resp in list_workspaces_async(mock_inventory, subj, "member"):
            responses.append(resp)
        
        assert len(responses) == 1
        
        assert mock_inventory.StreamedListObjects.call_count == 1
        call_args = mock_inventory.StreamedListObjects.call_args[0][0]
        
        assert call_args.relation == "member"
        assert call_args.object_type.resource_type == "workspace"
        assert call_args.object_type.reporter_type == "rbac"
        assert call_args.subject == subj

    @pytest.mark.asyncio
    async def test_handles_pagination_with_continuation_token(self):
        """Test that list_workspaces_async handles pagination with continuation token"""
        mock_inventory = Mock()
        
        response1 = StreamedListObjectsResponse(
            pagination=ResponsePagination(continuation_token="next-page-token")
        )
        response2 = StreamedListObjectsResponse(
            pagination=ResponsePagination(continuation_token="")
        )
        
        async def async_iter1():
            yield response1
        
        async def async_iter2():
            yield response2
        
        mock_inventory.StreamedListObjects.side_effect = [async_iter1(), async_iter2()]
        
        subj = principal_subject("user123", "redhat")
        
        responses = []
        async for resp in list_workspaces_async(mock_inventory, subj, "viewer"):
            responses.append(resp)
        
        assert len(responses) == 2
        
        assert mock_inventory.StreamedListObjects.call_count == 2
        
        second_call_args = mock_inventory.StreamedListObjects.call_args_list[1][0][0]
        assert second_call_args.pagination is not None
        assert second_call_args.pagination.continuation_token == "next-page-token"

    @pytest.mark.asyncio
    async def test_stops_when_no_continuation_token(self):
        """Test that list_workspaces_async stops when no continuation token is present"""
        mock_inventory = Mock()
        response = StreamedListObjectsResponse(
            pagination=ResponsePagination(continuation_token="")
        )
        
        async def async_iter():
            yield response
        
        mock_inventory.StreamedListObjects.return_value = async_iter()
        
        subj = principal_subject("user123", "redhat")
        
        responses = []
        async for resp in list_workspaces_async(mock_inventory, subj, "admin"):
            responses.append(resp)
        
        assert mock_inventory.StreamedListObjects.call_count == 1
        assert len(responses) == 1

    @pytest.mark.asyncio
    async def test_handles_stream_errors(self):
        """Test that list_workspaces_async properly propagates stream errors"""
        mock_inventory = Mock()
        mock_inventory.StreamedListObjects.side_effect = Exception("stream failed")
        
        subj = principal_subject("user123", "redhat")
        
        with pytest.raises(Exception, match="stream failed"):
            async for _ in list_workspaces_async(mock_inventory, subj, "member"):
                pass

    @pytest.mark.asyncio
    async def test_uses_provided_continuation_token(self):
        """Test that list_workspaces_async uses provided continuation token"""
        mock_inventory = Mock()
        response = StreamedListObjectsResponse(
            pagination=ResponsePagination(continuation_token="")
        )
        
        async def async_iter():
            yield response
        
        mock_inventory.StreamedListObjects.return_value = async_iter()
        
        subj = principal_subject("user123", "redhat")
        
        responses = []
        async for resp in list_workspaces_async(
            mock_inventory, 
            subj, 
            "member", 
            continuation_token="resume-from-here"
        ):
            responses.append(resp)
        
        assert len(responses) == 1
        
        call_args = mock_inventory.StreamedListObjects.call_args[0][0]
        assert call_args.pagination is not None
        assert call_args.pagination.continuation_token == "resume-from-here"

    @pytest.mark.asyncio
    async def test_handles_none_continuation_token_initial_request(self):
        """Test that list_workspaces_async handles None continuation token correctly"""
        mock_inventory = Mock()
        response = StreamedListObjectsResponse(
            pagination=ResponsePagination(continuation_token="")
        )
        
        async def async_iter():
            yield response
        
        mock_inventory.StreamedListObjects.return_value = async_iter()
        
        subj = principal_subject("user123", "redhat")
        
        responses = []
        async for resp in list_workspaces_async(mock_inventory, subj, "member", continuation_token=None):
            responses.append(resp)
        
        assert len(responses) == 1
        
        call_args = mock_inventory.StreamedListObjects.call_args[0][0]
        if hasattr(call_args, 'HasField'):
            assert not call_args.HasField("pagination")
        else:
            assert call_args.pagination is None


class TestFetchDefaultWorkspace:
    @patch('kessel.rbac.v2.requests')
    def test_successful_default_workspace_fetch(self, mock_requests):
        """Test successful fetch of default workspace"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{
                "id": "default-ws-123",
                "name": "Default Workspace",
                "type": "default",
                "description": "Organization default workspace"
            }]
        }
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response
        
        result = fetch_default_workspace(
            rbac_base_endpoint="http://example.com",
            org_id="org123"
        )
        
        assert result is not None
        assert result.id == "default-ws-123"
        assert result.name == "Default Workspace"
        assert result.type == "default"
        assert result.description == "Organization default workspace"
        
        mock_requests.get.assert_called_once()
        call_kwargs = mock_requests.get.call_args
        assert call_kwargs[1]["params"]["type"] == "default"
        assert call_kwargs[1]["headers"]["x-rh-rbac-org-id"] == "org123"

    @patch('kessel.rbac.v2.requests')
    def test_server_error_response(self, mock_requests):
        """Test handling of server error response"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("Internal Server Error")
        mock_requests.get.return_value = mock_response
        
        with pytest.raises(Exception, match="Internal Server Error"):
            fetch_default_workspace(
                rbac_base_endpoint="http://example.com",
                org_id="org123"
            )

    @patch('kessel.rbac.v2.requests')
    def test_empty_workspace_response(self, mock_requests):
        """Test handling of empty workspace response"""
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response
        
        with pytest.raises(ValueError, match="No default workspace found"):
            fetch_default_workspace(
                rbac_base_endpoint="http://example.com",
                org_id="org123"
            )

    @patch('kessel.rbac.v2.requests')
    def test_rbac_endpoint_with_trailing_slash(self, mock_requests):
        """Test that trailing slashes are handled correctly"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"id": "ws1", "name": "WS1", "type": "default", "description": ""}]
        }
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response
        
        result = fetch_default_workspace(
            rbac_base_endpoint="http://example.com/",
            org_id="org123"
        )
        
        assert result is not None
        assert result.id == "ws1"
        
        call_args = mock_requests.get.call_args[0][0]
        assert "/api/rbac/v2/workspaces/" in call_args
        assert "//api/rbac" not in call_args

    @patch('kessel.rbac.v2.requests')
    def test_with_custom_http_client(self, mock_requests):
        """Test using custom HTTP client"""
        mock_http_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"id": "ws1", "name": "WS1", "type": "default", "description": ""}]
        }
        mock_response.raise_for_status = Mock()
        mock_http_client.get.return_value = mock_response
        
        result = fetch_default_workspace(
            rbac_base_endpoint="http://example.com",
            org_id="org123",
            http_client=mock_http_client
        )
        
        assert result is not None
        mock_http_client.get.assert_called_once()
        mock_requests.get.assert_not_called()

    @patch('kessel.rbac.v2.requests')
    def test_with_auth(self, mock_requests):
        """Test fetch with authentication"""
        mock_auth = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"id": "ws1", "name": "WS1", "type": "default", "description": ""}]
        }
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response
        
        result = fetch_default_workspace(
            rbac_base_endpoint="http://example.com",
            org_id="org123",
            auth=mock_auth
        )
        
        assert result is not None
        call_kwargs = mock_requests.get.call_args[1]
        assert call_kwargs["auth"] == mock_auth

    @patch('kessel.rbac.v2.requests')
    def test_invalid_json_response(self, mock_requests):
        """Test handling of invalid JSON response"""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            fetch_default_workspace(
                rbac_base_endpoint="http://example.com",
                org_id="org123"
            )


class TestFetchRootWorkspace:
    @patch('kessel.rbac.v2.requests')
    def test_successful_root_workspace_fetch(self, mock_requests):
        """Test successful fetch of root workspace"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{
                "id": "root-ws-456",
                "name": "Root Workspace",
                "type": "root",
                "description": "Organization root workspace"
            }]
        }
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response
        
        result = fetch_root_workspace(
            rbac_base_endpoint="http://example.com",
            org_id="org123"
        )
        
        assert result is not None
        assert result.id == "root-ws-456"
        assert result.name == "Root Workspace"
        assert result.type == "root"
        assert result.description == "Organization root workspace"
        
        call_kwargs = mock_requests.get.call_args
        assert call_kwargs[1]["params"]["type"] == "root"

    @patch('kessel.rbac.v2.requests')
    def test_unauthorized_error(self, mock_requests):
        """Test handling of unauthorized error"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("Unauthorized")
        mock_requests.get.return_value = mock_response
        
        with pytest.raises(Exception, match="Unauthorized"):
            fetch_root_workspace(
                rbac_base_endpoint="http://example.com",
                org_id="org123"
            )

    @patch('kessel.rbac.v2.requests')
    def test_empty_root_workspace_response(self, mock_requests):
        """Test handling of empty root workspace response"""
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response
        
        with pytest.raises(ValueError, match="No root workspace found"):
            fetch_root_workspace(
                rbac_base_endpoint="http://example.com",
                org_id="org123"
            )

    @patch('kessel.rbac.v2.requests')
    def test_url_construction(self, mock_requests):
        """Test correct URL construction"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"id": "ws1", "name": "WS1", "type": "root", "description": ""}]
        }
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response
        
        fetch_root_workspace(
            rbac_base_endpoint="http://example.com",
            org_id="org123"
        )
        
        call_args = mock_requests.get.call_args[0][0]
        assert call_args == "http://example.com/api/rbac/v2/workspaces/"

    @patch('kessel.rbac.v2.requests')
    def test_headers_set_correctly(self, mock_requests):
        """Test that required headers are set correctly"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"id": "ws1", "name": "WS1", "type": "root", "description": ""}]
        }
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response
        
        fetch_root_workspace(
            rbac_base_endpoint="http://example.com",
            org_id="test-org-id"
        )
        
        call_kwargs = mock_requests.get.call_args[1]
        assert call_kwargs["headers"]["x-rh-rbac-org-id"] == "test-org-id"
        assert call_kwargs["headers"]["Content-Type"] == "application/json"

