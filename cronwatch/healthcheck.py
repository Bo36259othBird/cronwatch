"""Healthcheck endpoint support for cronwatch daemon.

Exposes a simple HTTP server that responds with the current daemon
status so external monitoring tools (e.g. UptimeRobot, Kubernetes
livenessProbe) can verify the daemon is alive.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable


class _Handler(BaseHTTPRequestHandler):
    """Minimal HTTP handler that delegates status to a callable."""

    status_fn: Callable[[], dict]  # injected by HealthcheckServer

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return

        payload = self.status_fn()
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args, **kwargs) -> None:  # pragma: no cover
        """Suppress default request logging."""


class HealthcheckServer:
    """Runs a lightweight HTTP healthcheck server in a daemon thread."""

    def __init__(self, port: int, status_fn: Callable[[], dict]) -> None:
        self._port = port
        self._status_fn = status_fn
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the HTTP server in a background daemon thread."""
        handler_cls = type(
            "_BoundHandler",
            (_Handler,),
            {"status_fn": staticmethod(self._status_fn)},
        )
        self._server = HTTPServer(("0.0.0.0", self._port), handler_cls)
        self._thread = threading.Thread(
            target=self._server.serve_forever, daemon=True, name="cronwatch-health"
        )
        self._thread.start()

    def stop(self) -> None:
        """Shut down the HTTP server gracefully."""
        if self._server is not None:
            self._server.shutdown()
            self._server = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
