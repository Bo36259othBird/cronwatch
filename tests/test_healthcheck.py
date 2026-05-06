"""Tests for cronwatch.healthcheck."""
from __future__ import annotations

import json
import socket
import time
import urllib.request

import pytest

from cronwatch.healthcheck import HealthcheckServer


def _free_port() -> int:
    """Return an available TCP port on localhost."""
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture()
def server():
    """Start a HealthcheckServer on a random free port and stop it after the test."""
    port = _free_port()
    status = {"alive": True, "active_jobs": 0}
    srv = HealthcheckServer(port=port, status_fn=lambda: status)
    srv.start()
    # Give the thread a moment to bind
    time.sleep(0.05)
    yield srv, port, status
    srv.stop()


def test_server_is_running_after_start(server):
    srv, _port, _status = server
    assert srv.is_running


def test_health_endpoint_returns_200(server):
    srv, port, _status = server
    resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/health")
    assert resp.status == 200


def test_health_endpoint_returns_json(server):
    _srv, port, _status = server
    resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/health")
    data = json.loads(resp.read())
    assert isinstance(data, dict)


def test_health_endpoint_reflects_status_fn(server):
    _srv, port, status = server
    status["active_jobs"] = 3
    resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/health")
    data = json.loads(resp.read())
    assert data["active_jobs"] == 3


def test_unknown_path_returns_404(server):
    _srv, port, _status = server
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/unknown")
        pytest.fail("Expected HTTPError")
    except urllib.error.HTTPError as exc:
        assert exc.code == 404


def test_server_is_not_running_after_stop(server):
    srv, _port, _status = server
    srv.stop()
    # Allow thread to finish
    time.sleep(0.05)
    assert not srv.is_running
