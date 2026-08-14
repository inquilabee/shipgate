"""UI request hardening helpers for the report frontend."""

from __future__ import annotations

import ipaddress
import os
import secrets
import sys

UI_SESSION_COOKIE = "shipgate_ui_session"
UI_AUTH_HEADER = "X-ShipGate-UI-Token"
UI_UNLOCK_PATH = "/ui-token"
PUBLIC_UI_PATHS = frozenset({"/health", UI_UNLOCK_PATH})


class UiSessionStore:
    """Opaque unlock sessions; never stores ``SHIPGATE_UI_TOKEN``."""

    def __init__(self) -> None:
        self._sessions: set[str] = set()

    def issue(self) -> str:
        session_id = secrets.token_urlsafe(32)
        self._sessions.add(session_id)
        return session_id

    def is_unlocked(self, session_id: str | None) -> bool:
        return session_id is not None and session_id in self._sessions


def is_loopback_host(host: str) -> bool:
    stripped = host.strip()
    if stripped.casefold() == "localhost":
        return True
    candidate = stripped[1:-1] if stripped.startswith("[") and stripped.endswith("]") else stripped
    try:
        return ipaddress.ip_address(candidate).is_loopback
    except ValueError:
        return False


def warn_if_non_loopback(host: str) -> None:
    if not is_loopback_host(host):
        sys.stderr.write(
            "shipgate: warning: binding "
            f"{host} exposes the report UI; set SHIPGATE_UI_TOKEN "
            "and prefer 127.0.0.1\n"
        )


def require_bind_safety(host: str) -> None:
    if is_loopback_host(host):
        return
    if ui_token_from_env() is None:
        raise SystemExit(
            f"shipgate serve refuses to bind {host} without SHIPGATE_UI_TOKEN; prefer 127.0.0.1"
        )
    warn_if_non_loopback(host)


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def ui_token_from_env() -> str | None:
    value = os.environ.get("SHIPGATE_UI_TOKEN")
    return None if value is None or value == "" else value


def ui_token_matches(submitted: str | None, expected: str | None) -> bool:
    return (
        False if expected is None or not submitted else secrets.compare_digest(submitted, expected)
    )


def validate_csrf_token(*, csrf_expected: str, csrf_submitted: str | None) -> None:
    if not csrf_submitted or not secrets.compare_digest(csrf_submitted, csrf_expected):
        raise PermissionError("invalid CSRF token")


def validate_run_submit_tokens(
    *,
    csrf_expected: str,
    csrf_submitted: str | None,
    ui_token_expected: str | None,
    ui_token_submitted: str | None,
) -> None:
    """Legacy CSRF + env-token compare (header path / unit tests)."""
    validate_csrf_token(csrf_expected=csrf_expected, csrf_submitted=csrf_submitted)
    if ui_token_expected is not None and not ui_token_matches(
        ui_token_submitted, ui_token_expected
    ):
        raise PermissionError("invalid UI token")


def is_public_ui_path(path: str) -> bool:
    return path in PUBLIC_UI_PATHS or path.startswith("/static")
