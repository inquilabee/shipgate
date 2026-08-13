"""UI request hardening helpers for the report frontend."""

from __future__ import annotations

import os
import secrets
import sys

LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def is_loopback_host(host: str) -> bool:
    return host in LOOPBACK_HOSTS


def warn_if_non_loopback(host: str) -> None:
    if not is_loopback_host(host):
        sys.stderr.write(
            "shipgate: warning: binding "
            f"{host} exposes POST /runs/new; set SHIPGATE_UI_TOKEN "
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


def validate_run_submit_tokens(
    *,
    csrf_expected: str,
    csrf_submitted: str | None,
    ui_token_expected: str | None,
    ui_token_submitted: str | None,
) -> None:
    if not csrf_submitted or not secrets.compare_digest(csrf_submitted, csrf_expected):
        raise PermissionError("invalid CSRF token")
    if ui_token_expected is not None and (
        not ui_token_submitted or not secrets.compare_digest(ui_token_submitted, ui_token_expected)
    ):
        raise PermissionError("invalid UI token")
