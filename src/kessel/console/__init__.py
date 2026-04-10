import json
from base64 import b64decode

from kessel.inventory.v1beta2.subject_reference_pb2 import SubjectReference
from kessel.rbac.v2 import principal_subject

_IDENTITY_TYPE_FIELDS = {
    "User": "user",
    "ServiceAccount": "service_account",
}

_USER_ID_KEYS = {
    "User": ("user_id",),
    "ServiceAccount": ("user_id", "client_id"),
}


def _extract_user_id(identity: dict) -> str:
    """Extract the user identifier from a parsed x-rh-identity dict.

    Args:
        identity: The inner identity dict (``{"type": "User", "user": {...}, ...}``).

    Returns:
        The resolved user identifier string.

    Raises:
        ValueError: If the identity type is unsupported or no user ID can be resolved.
    """
    if not isinstance(identity, dict):
        raise ValueError("identity must be a dict")

    identity_type = identity.get("type")
    field = _IDENTITY_TYPE_FIELDS.get(identity_type)
    if field is None:
        supported = ", ".join(sorted(_IDENTITY_TYPE_FIELDS))
        raise ValueError(f"Unsupported identity type: {identity_type!r} (supported: {supported})")

    details = identity.get(field)
    if not isinstance(details, dict):
        raise ValueError(f"Identity type {identity_type!r} is missing the {field!r} field")

    for key in _USER_ID_KEYS[identity_type]:
        value = details.get(key)
        if value:
            return value

    tried = ", ".join(_USER_ID_KEYS[identity_type])
    raise ValueError(
        f"Unable to resolve user ID from {identity_type} identity " f"(tried: {tried})"
    )


def principal_from_rh_identity(identity: dict, domain: str = "redhat") -> SubjectReference:
    """Build a principal ``SubjectReference`` from a parsed ``x-rh-identity`` dict.

    Args:
        identity: The inner identity dict from the ``x-rh-identity`` header
                  (e.g. ``{"type": "User", "org_id": "...", "user": {...}}``).
        domain: The domain or organization the user belongs to.
                Defaults to ``"redhat"``.

    Returns:
        A ``SubjectReference`` for the resolved principal.

    Raises:
        ValueError: If the user ID cannot be resolved from the identity.
    """
    user_id = _extract_user_id(identity)
    return principal_subject(user_id, domain)


def principal_from_rh_identity_header(header: str, domain: str = "redhat") -> SubjectReference:
    """Build a principal ``SubjectReference`` from a raw ``x-rh-identity`` header.

    Args:
        header: The base64-encoded ``x-rh-identity`` header value.
        domain: The domain or organization the user belongs to.
                Defaults to ``"redhat"``.

    Returns:
        A ``SubjectReference`` for the resolved principal.

    Raises:
        ValueError: If the header is malformed or the user ID cannot be resolved.
    """
    try:
        decoded = json.loads(b64decode(header))
    except Exception as exc:
        raise ValueError(f"Failed to decode identity header: {exc}") from exc

    if not isinstance(decoded, dict):
        raise ValueError("Identity header did not decode to a JSON object")

    identity = decoded.get("identity", decoded)
    return principal_from_rh_identity(identity, domain)
