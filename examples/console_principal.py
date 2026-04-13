import json
from base64 import b64encode

from kessel.console import principal_from_rh_identity, principal_from_rh_identity_header


def run():
    # --- From a parsed User identity dict ---
    user_identity = {
        "type": "User",
        "org_id": "12345",
        "user": {"user_id": "7393748", "username": "jdoe"},
    }
    subject = principal_from_rh_identity(user_identity)
    print(f"User principal:            {subject.resource.resource_id}")

    # --- From a parsed ServiceAccount identity dict ---
    sa_identity = {
        "type": "ServiceAccount",
        "org_id": "456",
        "service_account": {
            "client_id": "b69eaf9e-e6a6-4f9e-805e-02987daddfbd",
            "username": "service-account-b69eaf9e",
        },
    }
    subject = principal_from_rh_identity(sa_identity)
    print(f"ServiceAccount principal:  {subject.resource.resource_id}")

    # --- From a raw base64-encoded x-rh-identity header ---
    header_payload = {
        "identity": {
            "type": "User",
            "org_id": "12345",
            "user": {"user_id": "7393748", "username": "jdoe"},
        }
    }
    header = b64encode(json.dumps(header_payload).encode()).decode("ascii")
    subject = principal_from_rh_identity_header(header)
    print(f"From header principal:     {subject.resource.resource_id}")


if __name__ == "__main__":
    run()
