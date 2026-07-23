"""UI request hardening helpers for the report frontend."""

from __future__ import annotations

import os
import secrets
import sys


def warn_if_non_loopback(host: str) -> None:
    if host not in {"127.0.0.1", "localhost", "::1"}:
        sys.stderr.write(
            "shipgate: warning: binding "
            f"{host} exposes POST /runs/new; set SHIPGATE_UI_TOKEN "
            "and prefer 127.0.0.1\n"
        )


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def ui_token_from_env() -> str | None:
    value = os.environ.get("SHIPGATE_UI_TOKEN")
    if value is None or value == "":
        return None
    return value


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
