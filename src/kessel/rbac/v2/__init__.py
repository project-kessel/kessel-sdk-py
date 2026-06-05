import os
import threading
import time
from collections import OrderedDict
from typing import Optional, AsyncIterator, Iterable
from requests.auth import AuthBase
import requests

from kessel.inventory.v1beta2.representation_type_pb2 import RepresentationType
from kessel.inventory.v1beta2.resource_reference_pb2 import ResourceReference
from kessel.inventory.v1beta2.subject_reference_pb2 import SubjectReference
from kessel.inventory.v1beta2.reporter_reference_pb2 import ReporterReference
from kessel.inventory.v1beta2.streamed_list_objects_request_pb2 import StreamedListObjectsRequest
from kessel.inventory.v1beta2.streamed_list_objects_response_pb2 import StreamedListObjectsResponse
from kessel.inventory.v1beta2.request_pagination_pb2 import RequestPagination
from kessel.inventory.v1beta2.inventory_service_pb2_grpc import KesselInventoryServiceStub


class Workspace:
    def __init__(self, id: str, name: str, type: str, description: str):
        """
        Initialize a Workspace instance.

        Args:
            id: Workspace identifier
            name: Workspace name
            type: Workspace type ("root", "default")
            description: Workspace description
        """
        self.id = id
        self.name = name
        self.type = type
        self.description = description


class WorkspaceClient:
    """Client for fetching workspace data from RBAC with optional caching and connection pooling.

    Args:
        rbac_base_endpoint: The RBAC service endpoint URL.
        auth: Authentication object compatible with requests.
        http_client: Optional requests-like client. If None, creates a requests.Session internally.
        cache_ttl: Seconds to cache workspace results. 0 disables caching.
            Falls back to KESSEL_WORKSPACE_CACHE_TTL env var if not provided.
        cache_max_size: Maximum number of cached entries. Oldest entries are evicted when full.
            Falls back to KESSEL_WORKSPACE_CACHE_MAX_SIZE env var if not provided.
    """

    def __init__(
        self,
        rbac_base_endpoint: str,
        auth: Optional[AuthBase] = None,
        http_client=None,
        cache_ttl: Optional[int] = None,
        cache_max_size: Optional[int] = None,
    ):
        self._rbac_base_endpoint = rbac_base_endpoint
        self._auth = auth
        self._http_client = http_client if http_client is not None else requests.Session()
        self._cache_ttl = (
            cache_ttl
            if cache_ttl is not None
            else int(os.environ.get("KESSEL_WORKSPACE_CACHE_TTL", "900"))
        )
        self._cache_max_size = (
            cache_max_size
            if cache_max_size is not None
            else int(os.environ.get("KESSEL_WORKSPACE_CACHE_MAX_SIZE", "10000"))
        )
        self._cache: OrderedDict[tuple[str, str], tuple["Workspace", float]] = OrderedDict()
        self._lock = threading.Lock()

    def fetch_default_workspace(self, org_id: str) -> "Workspace":
        """Fetch the default workspace for the specified organization."""
        return self._fetch(org_id, "default")

    def fetch_root_workspace(self, org_id: str) -> "Workspace":
        """Fetch the root workspace for the specified organization."""
        return self._fetch(org_id, "root")

    def clear_cache(self):
        """Evict all cached workspace entries."""
        with self._lock:
            self._cache.clear()

    def _fetch(self, org_id: str, workspace_type: str) -> "Workspace":
        if self._cache_ttl > 0:
            key = (org_id, workspace_type)
            cached = self._cache.get(key)
            if cached and time.monotonic() < cached[1]:
                with self._lock:
                    self._cache.move_to_end(key)
                return cached[0]

            with self._lock:
                cached = self._cache.get(key)
                if cached and time.monotonic() < cached[1]:
                    self._cache.move_to_end(key)
                    return cached[0]

                workspace = _fetch_workspace_by_type(
                    rbac_base_endpoint=self._rbac_base_endpoint,
                    org_id=org_id,
                    workspace_type=workspace_type,
                    auth=self._auth,
                    http_client=self._http_client,
                )
                self._cache[key] = (workspace, time.monotonic() + self._cache_ttl)
                self._cache.move_to_end(key)
                if len(self._cache) > self._cache_max_size:
                    self._cache.popitem(last=False)
                return workspace

        return _fetch_workspace_by_type(
            rbac_base_endpoint=self._rbac_base_endpoint,
            org_id=org_id,
            workspace_type=workspace_type,
            auth=self._auth,
            http_client=self._http_client,
        )


def _fetch_workspace_by_type(
    rbac_base_endpoint: str,
    org_id: str,
    workspace_type: str,
    auth: Optional[AuthBase] = None,
    http_client: Optional[requests] = None,
) -> Workspace:
    """
    Internal helper to fetch a workspace by type ("root", "default").

    Args:
        auth: Authentication object compatible with requests.
        rbac_base_endpoint: The RBAC service endpoint URL.
        org_id: Organization ID to use for the request.
        workspace_type: The workspace type to query for.
        http_client: Optional requests-like client. Defaults to requests.

    Returns:
        A Workspace instance of the requested type.
    """
    client = http_client if http_client is not None else requests

    url = f"{rbac_base_endpoint.rstrip('/')}/api/rbac/v2/workspaces/"
    headers = {
        "x-rh-rbac-org-id": org_id,
        "Content-Type": "application/json",
    }

    response = client.get(url, params={"type": workspace_type}, headers=headers, auth=auth)
    response.raise_for_status()

    data = response.json()

    if "data" in data and data["data"]:
        workspace_data = data["data"][0]
    else:
        raise ValueError(f"No {workspace_type} workspace found in response")

    return Workspace(
        workspace_data["id"],
        workspace_data["name"],
        workspace_data["type"],
        workspace_data["description"],
    )


def fetch_root_workspace(
    rbac_base_endpoint: str,
    org_id: str,
    auth: Optional[AuthBase] = None,
    http_client: Optional[requests] = None,
) -> Workspace:
    """
    Fetches the root workspace for the specified organization.
    This function queries RBAC v2 to find the root workspace for the given org_id.

    GET /api/rbac/v2/workspaces/?type=root

    Args:
        auth: Authentication object compatible with requests (e.g. oauth2_auth(credentials)).
        rbac_base_endpoint: The RBAC service endpoint URL (stage/prod/ephemeral)
        org_id: Organization ID to use for the request.
        http_client: Optional requests module.
                    If not provided, uses the default requests module.

    Returns:
        A Workspace object representing the root workspace for the organization.
    """
    return _fetch_workspace_by_type(
        rbac_base_endpoint=rbac_base_endpoint,
        org_id=org_id,
        workspace_type="root",
        auth=auth,
        http_client=http_client,
    )


def fetch_default_workspace(
    rbac_base_endpoint: str,
    org_id: str,
    auth: Optional[AuthBase] = None,
    http_client: Optional[requests] = None,
) -> Workspace:
    """
    Fetches the default workspace for the specified organization.
    This function queries RBAC v2 to find the default workspace for the given org_id.

    GET /api/rbac/v2/workspaces/?type=default

    Args:
        auth: Authentication object compatible with requests (e.g. oauth2_auth(credentials)).
        rbac_base_endpoint: The RBAC service endpoint URL (stage/prod/ephemeral)
        org_id: Organization ID to use for the request.
        http_client: Optional requests module.
                    If not provided, uses the default requests module.

    Returns:
        A Workspace object representing the default workspace for the organization.
    """
    return _fetch_workspace_by_type(
        rbac_base_endpoint=rbac_base_endpoint,
        org_id=org_id,
        workspace_type="default",
        auth=auth,
        http_client=http_client,
    )


def workspace_type() -> RepresentationType:
    """
    Function to create a RepresentationType for workspace resources.
    Returns a protobuf RepresentationType configured for RBAC workspace objects.

    Returns:
        RepresentationType: A RepresentationType for workspace resources
    """
    return RepresentationType(resource_type="workspace", reporter_type="rbac")


def role_type() -> RepresentationType:
    """
    Function to create a RepresentationType for role resources.
    Returns a protobuf RepresentationType configured for RBAC role objects.

    Returns:
        RepresentationType: A RepresentationType for role resources
    """
    return RepresentationType(resource_type="role", reporter_type="rbac")


def principal_resource(id: str, domain: str) -> ResourceReference:
    """
    Creates a ResourceReference for a user principal based on user ID and domain.
    This function standardizes the creation of principal resources.

    Args:
        id: The user identifier
        domain: The domain or organization the user belongs to

    Returns:
        ResourceReference: A ResourceReference pointing to the user's principal resource
    """
    return ResourceReference(
        resource_type="principal",
        resource_id=f"{domain}/{id}",
        reporter=ReporterReference(type="rbac"),
    )


def role_resource(resource_id: str) -> ResourceReference:
    """
    Function to create a ResourceReference for a role.
    Returns a protobuf ResourceReference configured for RBAC role resources.

    Args:
        resource_id: The role identifier

    Returns:
        ResourceReference: A ResourceReference for the role
    """
    return ResourceReference(
        resource_type="role", resource_id=resource_id, reporter=ReporterReference(type="rbac")
    )


def workspace_resource(resource_id: str) -> ResourceReference:
    """
    Function to create a ResourceReference for a workspace.
    Returns a protobuf ResourceReference configured for RBAC workspace resources.

    Args:
        resource_id: The workspace identifier

    Returns:
        ResourceReference: A ResourceReference for the workspace
    """
    return ResourceReference(
        resource_type="workspace", resource_id=resource_id, reporter=ReporterReference(type="rbac")
    )


def principal_subject(id: str, domain: str) -> SubjectReference:
    """
    Creates a SubjectReference for a user principal based on user ID and domain.
    This is a convenience function that wraps principal_resource to create a subject reference.

    Args:
        id: The user identifier
        domain: The domain or organization the user belongs to

    Returns:
        SubjectReference: A SubjectReference for the user's principal
    """
    return SubjectReference(resource=principal_resource(id, domain))


def subject(resource_ref: ResourceReference, relation: Optional[str] = None) -> SubjectReference:
    """
    Creates a SubjectReference from a ResourceReference and an optional relation.
    This function allows you to easily create a subject reference.

    Args:
        resource_ref: The resource reference that identifies the subject
        relation: Optional relation that points to a set of subjects (e.g., "members", "owners")

    Returns:
        SubjectReference: A reference to a Subject or, if a relation is provided, a Subject Set.
    """
    if relation is not None:
        return SubjectReference(resource=resource_ref, relation=relation)
    else:
        return SubjectReference(resource=resource_ref)


def list_workspaces(
    inventory: KesselInventoryServiceStub,
    subject: SubjectReference,
    relation: str,
    continuation_token: Optional[str] = None,
) -> Iterable[StreamedListObjectsResponse]:
    """
    Lists all workspaces that a subject has a specific relation to.
    This function queries the inventory service to find workspaces
    based on the subject's permissions.

    Pagination is handled automatically meaning continuation tokens are managed
    internally so callers never need to deal with them.

    Args:
        inventory: The inventory service client stub for making the request.
        subject: The subject to check permissions for.
        relation: The relationship type to check (e.g. "member", "admin", "viewer").
        continuation_token: Optional token to resume listing from a previous page

    Returns:
        An iterator of StreamedListObjectsResponse messages.

    Examples:
        Iterate one-by-one (lazy, low memory)::

            for response in list_workspaces(inventory, subject, "viewer"):
                print(response.object.resource_id)

        Materialise into a list (eager, all results in memory)::

            all_workspaces = list(list_workspaces(inventory, subject, "viewer"))
    """
    while True:
        pagination = None
        if continuation_token is not None:
            pagination = RequestPagination(
                limit=1000,
                continuation_token=continuation_token if continuation_token is not None else "",
            )

        request = StreamedListObjectsRequest(
            object_type=workspace_type(),
            relation=relation,
            subject=subject,
            pagination=pagination,
        )

        last_token = None
        for response in inventory.StreamedListObjects(request):
            yield response
            if response.pagination is not None:
                last_token = response.pagination.continuation_token

        if not last_token:
            break

        continuation_token = last_token


async def list_workspaces_async(
    inventory: KesselInventoryServiceStub,
    subject: SubjectReference,
    relation: str,
    continuation_token: Optional[str] = None,
) -> AsyncIterator[StreamedListObjectsResponse]:
    """
    Async version of :func:`list_workspaces`.

    Lists all workspaces that a subject has a specific relation to.
    This function queries the inventory service to find workspaces
    based on the subject's permissions.
    Pagination is handled automatically meaning continuation tokens are managed
    internally.

    Args:
        inventory: The inventory service client stub for making the request (async channel).
        subject: The subject to check permissions for.
        relation: The relationship type to check (e.g. "member", "admin", "viewer").
        continuation_token: Optional token to resume listing from a previous position.

    Returns:
        An async iterator of StreamedListObjectsResponse messages.

    Examples:
        Iterate one-by-one::

            async for response in list_workspaces_async(inventory, subject, "viewer"):
                print(response.object.resource_id)

        Materialise into a list::

            all_workspaces = [
                r async for r in list_workspaces_async(inventory, subject, "viewer")
            ]
    """
    while True:
        pagination = None
        if continuation_token is not None:
            pagination = RequestPagination(
                limit=1000,
                continuation_token=continuation_token if continuation_token is not None else "",
            )

        request = StreamedListObjectsRequest(
            object_type=workspace_type(),
            relation=relation,
            subject=subject,
            pagination=pagination,
        )

        last_token = None
        async for response in inventory.StreamedListObjects(request):
            yield response
            if response.pagination is not None:
                last_token = response.pagination.continuation_token

        if not last_token:
            break

        continuation_token = last_token
