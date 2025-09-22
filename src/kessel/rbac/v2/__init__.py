from typing import Optional, Any
import requests


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


def _fetch_workspace_by_type(
    auth: Any,
    rbac_base_endpoint: str,
    org_id: str,
    workspace_type: str,
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
    auth: Any,
    rbac_base_endpoint: str,
    org_id: str,
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
        auth=auth,
        rbac_base_endpoint=rbac_base_endpoint,
        org_id=org_id,
        workspace_type="root",
        http_client=http_client,
    )


def fetch_default_workspace(
    auth: Any,
    rbac_base_endpoint: str,
    org_id: str,
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
        auth=auth,
        rbac_base_endpoint=rbac_base_endpoint,
        org_id=org_id,
        workspace_type="default",
        http_client=http_client,
    )
