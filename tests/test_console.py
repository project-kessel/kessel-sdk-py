import json
from base64 import b64encode

import pytest

from kessel.console import (
    _extract_user_id,
    principal_from_rh_identity,
    principal_from_rh_identity_header,
)


class TestExtractUserId:
    def test_user_with_user_id(self):
        identity = {"type": "User", "user": {"user_id": "7393748", "username": "foobar"}}
        assert _extract_user_id(identity) == "7393748"

    def test_user_missing_user_id(self):
        identity = {"type": "User", "user": {"username": "foobar"}}
        with pytest.raises(ValueError, match="Unable to resolve user ID"):
            _extract_user_id(identity)

    def test_user_empty_user_id(self):
        identity = {"type": "User", "user": {"user_id": ""}}
        with pytest.raises(ValueError, match="Unable to resolve user ID"):
            _extract_user_id(identity)

    def test_service_account_with_user_id(self):
        identity = {
            "type": "ServiceAccount",
            "service_account": {"user_id": "sa-456", "client_id": "b69eaf9e"},
        }
        assert _extract_user_id(identity) == "sa-456"

    def test_service_account_missing_user_id(self):
        identity = {
            "type": "ServiceAccount",
            "service_account": {"client_id": "b69eaf9e"},
        }
        with pytest.raises(ValueError, match="Unable to resolve user ID"):
            _extract_user_id(identity)

    def test_service_account_empty_user_id(self):
        identity = {
            "type": "ServiceAccount",
            "service_account": {"user_id": "", "client_id": "b69eaf9e"},
        }
        with pytest.raises(ValueError, match="Unable to resolve user ID"):
            _extract_user_id(identity)

    @pytest.mark.parametrize("identity_type", ["System", "X509", "Associate"])
    def test_unsupported_identity_type(self, identity_type):
        identity = {"type": identity_type}
        with pytest.raises(ValueError, match="Unsupported identity type"):
            _extract_user_id(identity)

    def test_missing_type_field(self):
        with pytest.raises(ValueError, match="Unsupported identity type"):
            _extract_user_id({"org_id": "123"})

    def test_missing_user_details(self):
        identity = {"type": "User"}
        with pytest.raises(ValueError, match="missing the 'user' field"):
            _extract_user_id(identity)

    def test_missing_service_account_details(self):
        identity = {"type": "ServiceAccount"}
        with pytest.raises(ValueError, match="missing the 'service_account' field"):
            _extract_user_id(identity)

    def test_user_details_not_a_dict(self):
        identity = {"type": "User", "user": "not-a-dict"}
        with pytest.raises(ValueError, match="missing the 'user' field"):
            _extract_user_id(identity)

    def test_identity_not_a_dict(self):
        with pytest.raises(ValueError, match="identity must be a dict"):
            _extract_user_id(None)

    def test_identity_is_a_string(self):
        with pytest.raises(ValueError, match="identity must be a dict"):
            _extract_user_id("not-a-dict")


class TestPrincipalFromRHIdentity:
    def test_user_identity(self):
        identity = {
            "type": "User",
            "org_id": "1979710",
            "user": {"user_id": "7393748", "username": "foobar"},
        }
        ref = principal_from_rh_identity(identity)
        assert ref.resource.resource_type == "principal"
        assert ref.resource.resource_id == "redhat/7393748"
        assert ref.resource.reporter.type == "rbac"

    def test_service_account_identity(self):
        identity = {
            "type": "ServiceAccount",
            "org_id": "456",
            "service_account": {"user_id": "sa-456", "client_id": "b69eaf9e", "username": "svc-b69eaf9e"},
        }
        ref = principal_from_rh_identity(identity)
        assert ref.resource.resource_id == "redhat/sa-456"

    def test_custom_domain(self):
        identity = {"type": "User", "user": {"user_id": "42"}}
        ref = principal_from_rh_identity(identity, domain="custom")
        assert ref.resource.resource_id == "custom/42"

    def test_propagates_error_for_unsupported_type(self):
        identity = {"type": "System", "system": {"cn": "abc"}}
        with pytest.raises(ValueError, match="Unsupported identity type"):
            principal_from_rh_identity(identity)


def _encode_identity_header(payload: dict) -> str:
    return b64encode(json.dumps(payload).encode()).decode("ascii")


class TestPrincipalFromRHIdentityHeader:
    def test_full_envelope(self):
        header = _encode_identity_header({
            "identity": {
                "type": "User",
                "org_id": "1979710",
                "user": {"user_id": "7393748", "username": "foobar"},
            }
        })
        ref = principal_from_rh_identity_header(header)
        assert ref.resource.resource_id == "redhat/7393748"
        assert ref.resource.resource_type == "principal"

    def test_missing_identity_envelope(self):
        header = _encode_identity_header({
            "type": "User",
            "user": {"user_id": "42"},
        })
        with pytest.raises(ValueError, match="missing the 'identity' envelope key"):
            principal_from_rh_identity_header(header)

    def test_service_account_header(self):
        header = _encode_identity_header({
            "identity": {
                "type": "ServiceAccount",
                "org_id": "456",
                "service_account": {"user_id": "sa-789", "client_id": "b69eaf9e"},
            }
        })
        ref = principal_from_rh_identity_header(header)
        assert ref.resource.resource_id == "redhat/sa-789"

    def test_custom_domain(self):
        header = _encode_identity_header({
            "identity": {"type": "User", "user": {"user_id": "1"}},
        })
        ref = principal_from_rh_identity_header(header, domain="acme")
        assert ref.resource.resource_id == "acme/1"

    def test_malformed_base64(self):
        with pytest.raises(ValueError, match="Failed to decode identity header"):
            principal_from_rh_identity_header("not-valid-base64!!!")

    def test_invalid_json(self):
        header = b64encode(b"this is not json").decode("ascii")
        with pytest.raises(ValueError, match="Failed to decode identity header"):
            principal_from_rh_identity_header(header)

    def test_non_object_json(self):
        header = b64encode(b'"just a string"').decode("ascii")
        with pytest.raises(ValueError, match="did not decode to a JSON object"):
            principal_from_rh_identity_header(header)

    def test_unsupported_type_in_header(self):
        header = _encode_identity_header({
            "identity": {"type": "System", "system": {"cn": "abc", "cert_type": "system"}},
        })
        with pytest.raises(ValueError, match="Unsupported identity type"):
            principal_from_rh_identity_header(header)

    def test_user_header_missing_user_id(self):
        header = _encode_identity_header({
            "identity": {
                "type": "User",
                "org_id": "1979710",
                "user": {"username": "foobar"},
            }
        })
        with pytest.raises(ValueError, match="Unable to resolve user ID"):
            principal_from_rh_identity_header(header)

    def test_service_account_header_missing_user_id(self):
        header = _encode_identity_header({
            "identity": {
                "type": "ServiceAccount",
                "org_id": "456",
                "service_account": {
                    "client_id": "b69eaf9e",
                    "username": "svc-b69eaf9e",
                },
            }
        })
        with pytest.raises(ValueError, match="Unable to resolve user ID"):
            principal_from_rh_identity_header(header)

    def test_realistic_user_header(self):
        header = _encode_identity_header({
            "identity": {
                "account_number": "540155",
                "org_id": "1979710",
                "user": {
                    "username": "rhn-support-foobar",
                    "is_internal": True,
                    "is_org_admin": True,
                    "first_name": "foo",
                    "last_name": "bar",
                    "is_active": True,
                    "user_id": "7393748",
                    "email": "example@redhat.com",
                },
                "type": "User",
            }
        })
        ref = principal_from_rh_identity_header(header)
        assert ref.resource.resource_id == "redhat/7393748"
        assert ref.resource.resource_type == "principal"
        assert ref.resource.reporter.type == "rbac"

    def test_realistic_service_account_header(self):
        header = _encode_identity_header({
            "identity": {
                "org_id": "456",
                "type": "ServiceAccount",
                "service_account": {
                    "user_id": "sa-b69eaf9e",
                    "client_id": "b69eaf9e-e6a6-4f9e-805e-02987daddfbd",
                    "username": "service-account-b69eaf9e-e6a6-4f9e-805e-02987daddfbd",
                },
            }
        })
        ref = principal_from_rh_identity_header(header)
        assert ref.resource.resource_id == "redhat/sa-b69eaf9e"
