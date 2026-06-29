import hashlib

from core.local_cookie_importer import (
    ChromiumCookie,
    build_tabbit_token_value,
    decrypt_chromium_cookie_value,
)


def test_build_tabbit_token_value_uses_jwt_sapisid_and_user_id():
    token_value = build_tabbit_token_value(
        {
            "token": "jwt-token",
            "SAPISID": "sapisid",
            "user_id": "device-id",
        }
    )

    assert token_value == "jwt-token|sapisid|device-id"


def test_build_tabbit_token_value_requires_token():
    try:
        build_tabbit_token_value({"SAPISID": "sapisid", "user_id": "device-id"})
    except ValueError as exc:
        assert "token cookie" in str(exc)
    else:
        raise AssertionError("Expected missing token cookie to fail")


def test_decrypt_chromium_cookie_value_strips_host_hash():
    cookie = ChromiumCookie(
        host_key="web.tabbit.ai",
        name="token",
        encrypted_value=b"v10",
    )
    plaintext = hashlib.sha256(cookie.host_key.encode()).digest() + b"jwt-token"

    assert decrypt_chromium_cookie_value(cookie, lambda value: plaintext) == "jwt-token"
