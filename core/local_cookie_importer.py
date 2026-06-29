import hashlib
import os
import platform
import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

TABBIT_COOKIE_HOST = "web.tabbit.ai"
TABBIT_COOKIE_NAMES = ("token", "SAPISID", "user_id")
KEYCHAIN_SERVICE = "Tabbit Safe Storage"


@dataclass(frozen=True)
class ChromiumCookie:
    host_key: str
    name: str
    encrypted_value: bytes


def default_tabbit_cookie_db() -> Path:
    return (
        Path.home()
        / "Library"
        / "Application Support"
        / "Tabbit"
        / "Default"
        / "Cookies"
    )


def _require_macos():
    if platform.system() != "Darwin":
        raise RuntimeError("local Tabbit cookie import is only supported on macOS")


def _read_keychain_password(service: str = KEYCHAIN_SERVICE) -> str:
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-w"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise RuntimeError(f"failed to read macOS Keychain item: {service}") from exc

    password = result.stdout.strip()
    if not password:
        raise RuntimeError(f"empty macOS Keychain password for: {service}")
    return password


def _derive_chromium_key(password: str) -> bytes:
    return hashlib.pbkdf2_hmac("sha1", password.encode(), b"saltysalt", 1003, 16)


def _decrypt_v10_with_openssl(encrypted_value: bytes, key: bytes) -> bytes:
    if not encrypted_value.startswith(b"v10"):
        raise ValueError("unsupported Chromium cookie encryption format")

    iv = (b" " * 16).hex()
    with NamedTemporaryFile() as input_file:
        input_file.write(encrypted_value[3:])
        input_file.flush()
        try:
            result = subprocess.run(
                [
                    "openssl",
                    "enc",
                    "-aes-128-cbc",
                    "-d",
                    "-K",
                    key.hex(),
                    "-iv",
                    iv,
                    "-in",
                    input_file.name,
                ],
                check=True,
                capture_output=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            raise RuntimeError("failed to decrypt Chromium cookie with openssl") from exc
    return result.stdout


def decrypt_chromium_cookie_value(cookie: ChromiumCookie, decryptor) -> str:
    plaintext = decryptor(cookie.encrypted_value)
    host_hash = hashlib.sha256(cookie.host_key.encode()).digest()
    if plaintext.startswith(host_hash):
        plaintext = plaintext[len(host_hash) :]
    return plaintext.decode("utf-8")


def read_chromium_cookies(
    cookie_db: Path,
    host: str = TABBIT_COOKIE_HOST,
    names: tuple[str, ...] = TABBIT_COOKIE_NAMES,
) -> list[ChromiumCookie]:
    if not cookie_db.exists():
        raise RuntimeError(f"Tabbit cookie database not found: {cookie_db}")

    placeholders = ",".join("?" for _ in names)
    query = (
        "select host_key, name, encrypted_value from cookies "
        f"where host_key = ? and name in ({placeholders})"
    )
    uri = f"file:{cookie_db}?mode=ro"
    with sqlite3.connect(uri, uri=True) as conn:
        rows = conn.execute(query, (host, *names)).fetchall()

    return [
        ChromiumCookie(host_key=row[0], name=row[1], encrypted_value=row[2])
        for row in rows
    ]


def build_tabbit_token_value(values: dict[str, str]) -> str:
    jwt_token = values.get("token", "").strip()
    if not jwt_token:
        raise ValueError("missing token cookie")

    parts = [jwt_token]
    sapisid = values.get("SAPISID", "").strip()
    user_id = values.get("user_id", "").strip()
    if sapisid:
        parts.append(sapisid)
    if user_id:
        parts.append(user_id)
    return "|".join(parts)


def import_tabbit_token_from_local_cookies(
    cookie_db: Path | None = None,
    host: str = TABBIT_COOKIE_HOST,
) -> dict:
    _require_macos()
    cookie_db = Path(os.path.expanduser(cookie_db or default_tabbit_cookie_db()))
    password = _read_keychain_password()
    key = _derive_chromium_key(password)
    cookies = read_chromium_cookies(cookie_db, host=host)
    if not cookies:
        raise RuntimeError(f"no Tabbit cookies found for host: {host}")

    def decryptor(value: bytes) -> bytes:
        return _decrypt_v10_with_openssl(value, key)

    values = {
        cookie.name: decrypt_chromium_cookie_value(cookie, decryptor)
        for cookie in cookies
    }
    token_value = build_tabbit_token_value(values)
    return {
        "token_value": token_value,
        "cookie_names": sorted(values.keys()),
        "host": host,
    }
