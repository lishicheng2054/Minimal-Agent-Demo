from __future__ import annotations

import os
from pathlib import Path


def pytest_configure() -> None:
    tmp_root = Path(".pytest-tmp")
    tmp_root.mkdir(parents=True, exist_ok=True)
    tmp_path = str(tmp_root.resolve())
    os.environ.setdefault("TMPDIR", tmp_path)
    os.environ.setdefault("TEMP", tmp_path)
    os.environ.setdefault("TMP", tmp_path)
