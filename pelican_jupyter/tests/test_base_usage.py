from __future__ import annotations

import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SITE = Path(__file__).parent / "pelican" / "markup-nbdata"


class _RequestCounter(BaseHTTPRequestHandler):
    requests = 0

    def do_GET(self):
        type(self).requests += 1
        self.send_response(204)
        self.end_headers()

    def log_message(self, _format, *_args):
        return


def test_minimal_pelican_site_builds_both_direct_notebook_routes_without_execution(
    tmp_path,
):
    marker = tmp_path / "build-executed.marker"
    output = tmp_path / "output"
    _RequestCounter.requests = 0
    server = ThreadingHTTPServer(("127.0.0.1", 0), _RequestCounter)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    environment = {
        **os.environ,
        "PELICAN_IPYNB_SENTINEL_MARKER": str(marker),
        "PELICAN_IPYNB_SENTINEL_URL": (
            f"http://127.0.0.1:{server.server_port}/sentinel"
        ),
    }

    try:
        run = subprocess.run(
            [
                sys.executable,
                "-m",
                "pelican",
                "content",
                "-s",
                "pelicanconf.py",
                "-o",
                str(output),
                "--fatal",
                "errors",
            ],
            cwd=SITE,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)

    assert run.returncode == 0, run.stdout + run.stderr
    routes = {path.relative_to(output).as_posix() for path in output.rglob("*.html")}
    assert "articles/synthetic-notebook.html" in routes
    assert "articles/build-no-execution-sentinel.html" in routes
    sentinel_html = (
        output / "articles" / "build-no-execution-sentinel.html"
    ).read_text(encoding="utf-8")
    assert "BUILD_SENTINEL_COMMITTED_OUTPUT" in sentinel_html
    assert "urlopen" in sentinel_html
    assert not marker.exists()
    assert _RequestCounter.requests == 0
