"""Report HTTP server."""

from __future__ import annotations

import webbrowser
from pathlib import Path


def serve(
    project_root: Path,
    host: str = "127.0.0.1",
    port: int = 8765,
    *,
    open_browser: bool = False,
) -> None:
    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit(
            'shipgate serve requires the server extra: pip install "shipgate[server]"'
        ) from exc

    from shipgate.frontend.web.app import create_app
    from shipgate.frontend.web.security import is_loopback_host, require_bind_safety

    require_bind_safety(host)
    primary = Path(project_root).resolve()
    app = create_app(primary, require_ui_token=not is_loopback_host(host))
    url = f"http://{host}:{port}/"
    print(f"ShipGate report server at {url}")
    if open_browser:
        webbrowser.open(url)
    uvicorn.run(app, host=host, port=port)
