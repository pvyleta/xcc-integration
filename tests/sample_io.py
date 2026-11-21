"""Read sample XML as text regardless of how it was saved.

Fresh captures keep the controller's raw bytes (data pages are windows-1250);
older fixtures were re-saved as UTF-8 under the same declaration.
"""

from __future__ import annotations

from pathlib import Path


def read_sample_xml(path: str | Path) -> str:
    raw = Path(path).read_bytes()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("windows-1250")
