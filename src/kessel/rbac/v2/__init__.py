from typing import Optional
import requests
from kessel.auth import OAuth2ClientCredentials
from kessel.requests import oauth2_auth


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


def fetch_root_workspace(
    oauth_credentials: OAuth2ClientCredentials,
    rbac_base_endpoint: str,
    org_id: str,
    http_client: Optional[requests] = None,
) -> Workspace:
    """
    Fetches the root workspace for the specified organization.
    This function queries RBAC v2 to find the root workspace for the given org_id.

    GET /api/rbac/v2/workspaces/?type=root

    Args:
        oauth_credentials: OAuth2 client credentials for automatic auth. The function will
                         internally create the appropriate auth adapter for the HTTP library.
        rbac_base_endpoint: The RBAC service endpoint URL (stage/prod/ephemeral)
        org_id: Organization ID to use for the request.
        http_client: Optional requests module.
                    If not provided, uses the default requests module.
                    Allows users to inject custom sessions with additional headers or configuration.

    Returns:
        A Workspace object representing the root workspace for the organization.
    """
    # Use provided http_client or default to requests
    client = http_client if http_client is not None else requests

    url = f"{rbac_base_endpoint.rstrip('/')}/api/rbac/v2/workspaces/"
    headers = {
        "x-rh-rbac-org-id": org_id,
        "Content-Type": "application/json",
    }
    # Add auth to the request
    auth = oauth2_auth(oauth_credentials)

    response = client.get(url, params={"type": "root"}, headers=headers, auth=auth)
    response.raise_for_status()

    data = response.json()

    if "data" in data and data["data"]:
        workspace_data = data["data"][0]
    else:
        raise ValueError("No root workspace found in response")

    return Workspace(
        workspace_data["id"],
        workspace_data["name"],
        workspace_data["type"],
        workspace_data["description"],
    )


def fetch_default_workspace(
    oauth_credentials: OAuth2ClientCredentials,
    rbac_base_endpoint: str,
    org_id: str,
    http_client: Optional[requests] = None,
) -> Workspace:
    """
    Fetches the default workspace for the specified organization.
    This function queries RBAC v2 to find the default workspace for the given org_id.

    GET /api/rbac/v2/workspaces/?type=default

    Args:
        oauth_credentials: OAuth2 client credentials for automatic auth. The function will
                         internally create the appropriate auth adapter for the HTTP library.
        rbac_base_endpoint: The RBAC service endpoint URL (stage/prod/ephemeral)
        org_id: Organization ID to use for the request.
        http_client: Optional requests module.
                    If not provided, uses the default requests module.
                    Allows users to inject custom sessions with additional headers or configuration.

    Returns:
        A Workspace object representing the default workspace for the organization.
    """
    # Use provided http_client or default to requests
    client = http_client if http_client is not None else requests

    url = f"{rbac_base_endpoint.rstrip('/')}/api/rbac/v2/workspaces/"
    headers = {
        "x-rh-rbac-org-id": org_id,
        "Content-Type": "application/json",
    }

    # Add auth to the request
    auth = oauth2_auth(oauth_credentials)

    response = client.get(url, params={"type": "default"}, headers=headers, auth=auth)
    response.raise_for_status()

    data = response.json()

    if "data" in data and data["data"]:
        workspace_data = data["data"][0]
    else:
        raise ValueError("No default workspace found in response")

    return Workspace(
        workspace_data["id"],
        workspace_data["name"],
        workspace_data["type"],
        workspace_data["description"],
    )
