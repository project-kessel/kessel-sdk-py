import os

from kessel.auth import fetch_oidc_discovery, OAuth2ClientCredentials
from kessel.requests import oauth2_auth
from kessel.rbac.v2 import fetch_default_workspace, fetch_root_workspace

RBAC_BASE_ENDPOINT = os.environ.get("RBAC_BASE_ENDPOINT", "")
ISSUER_URL = os.environ.get("AUTH_DISCOVERY_ISSUER_URL", "")
CLIENT_ID = os.environ.get("AUTH_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("AUTH_CLIENT_SECRET", "")


def run():
    discovery = fetch_oidc_discovery(ISSUER_URL)
    auth_credentials = OAuth2ClientCredentials(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        token_endpoint=discovery.token_endpoint,
    )

    try:
        print("Fetching workspaces for org_id 12345")

        # Create auth object
        auth = oauth2_auth(auth_credentials)

        # Fetch default workspace
        default_workspace = fetch_default_workspace(
            auth=auth,
            rbac_base_endpoint=RBAC_BASE_ENDPOINT,
            org_id="12345",
        )
        print(f"Default workspace: {default_workspace.name} (ID: {default_workspace.id})")

        # Fetch root workspace
        root_workspace = fetch_root_workspace(
            auth=auth,
            rbac_base_endpoint=RBAC_BASE_ENDPOINT,
            org_id="12345",
        )
        print(f"Root workspace: {root_workspace.name} (ID: {root_workspace.id})")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    run()
