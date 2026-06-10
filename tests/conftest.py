from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_path() -> Path:
    path = Path(tempfile.mkdtemp(prefix="mini-agent-demo-", dir=str(Path.cwd() / ".pytest-tmp")))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def pytest_configure() -> None:
    tmp_root = Path(".pytest-tmp")
    tmp_root.mkdir(parents=True, exist_ok=True)
    tmp_path = str(tmp_root.resolve())
    os.environ.setdefault("TMPDIR", tmp_path)
    os.environ.setdefault("TEMP", tmp_path)
    os.environ.setdefault("TMP", tmp_path)
