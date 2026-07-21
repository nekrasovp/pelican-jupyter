from __future__ import annotations

import shutil
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from jupyter_client import KernelManager
from nbclient import NotebookClient
from pelican.settings import read_settings

from pelican.plugins.ipynb_reader import IPYNBReader

FIXTURES = Path(__file__).parent / "fixtures"


class _RequestCounter(BaseHTTPRequestHandler):
    requests = 0

    def do_GET(self):
        type(self).requests += 1
        self.send_response(204)
        self.end_headers()

    def log_message(self, _format, *_args):
        return


def test_sentinel_observes_no_file_network_kernel_or_new_execution(
    tmp_path, monkeypatch
):
    source = tmp_path / "sentinel.ipynb"
    shutil.copyfile(FIXTURES / "no_execution_sentinel.ipynb", source)
    shutil.copyfile(
        FIXTURES / "no_execution_sentinel.nbdata", source.with_suffix(".nbdata")
    )
    source_before = source.read_bytes()
    marker = tmp_path / "executed.marker"

    _RequestCounter.requests = 0
    server = ThreadingHTTPServer(("127.0.0.1", 0), _RequestCounter)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    observations = {"kernel_starts": 0, "client_executes": 0}

    def kernel_started(*_args, **_kwargs):
        observations["kernel_starts"] += 1
        raise AssertionError("reader attempted to start a kernel")

    def client_executed(*_args, **_kwargs):
        observations["client_executes"] += 1
        raise AssertionError("reader attempted to execute a notebook")

    monkeypatch.setattr(KernelManager, "start_kernel", kernel_started)
    monkeypatch.setattr(NotebookClient, "execute", client_executed)
    monkeypatch.setenv("PELICAN_IPYNB_SENTINEL_MARKER", str(marker))
    monkeypatch.setenv(
        "PELICAN_IPYNB_SENTINEL_URL",
        f"http://127.0.0.1:{server.server_port}/sentinel",
    )

    try:
        content, _metadata = IPYNBReader(
            read_settings(
                override={
                    "PATH": str(tmp_path),
                    "OUTPUT_PATH": str(tmp_path / "output"),
                    "TIMEZONE": "UTC",
                }
            )
        ).read(str(source))
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)

    assert "SENTINEL_COMMITTED_OUTPUT" in content
    assert "urlopen" in content
    assert source.read_bytes() == source_before
    assert not marker.exists()
    assert _RequestCounter.requests == 0
    assert observations == {"kernel_starts": 0, "client_executes": 0}
