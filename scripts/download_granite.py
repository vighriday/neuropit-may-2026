"""Download an IBM Granite model into a cache directory of your choice.

Defaults are picked so the script works on every platform without
touching the system drive:

* On Linux and macOS the cache goes to ``~/.cache/huggingface`` (the
  normal Hugging Face default).
* On Windows it goes to ``D:\\huggingface`` if the D drive exists,
  otherwise ``%USERPROFILE%\\.cache\\huggingface``.

Override either choice with ``HF_HOME``/``HF_HUB_CACHE`` in your
environment. Override the model with ``GRANITE_MODEL_ID``. Both are
honoured by the rest of the pipeline through ``src/backend/config.py``.

Usage::

    python scripts/download_granite.py
    HF_HOME=/data/hf python scripts/download_granite.py
    GRANITE_MODEL_ID=ibm-granite/granite-3.1-8b-instruct python scripts/download_granite.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _default_cache_dir() -> Path:
    explicit = os.environ.get("HF_HUB_CACHE") or os.environ.get("HF_HOME")
    if explicit:
        return Path(explicit)
    if sys.platform == "win32":
        d_drive = Path("D:/")
        if d_drive.exists():
            return d_drive / "huggingface"
    return Path.home() / ".cache" / "huggingface"


def main() -> None:
    target = _default_cache_dir()
    target.mkdir(parents=True, exist_ok=True)
    xet = target / "xet"
    tmp = target / "tmp"
    xet.mkdir(parents=True, exist_ok=True)
    tmp.mkdir(parents=True, exist_ok=True)

    target_str = str(target)
    os.environ["HF_HOME"] = target_str
    os.environ["HF_HUB_CACHE"] = target_str
    os.environ["HUGGINGFACE_HUB_CACHE"] = target_str
    os.environ["HF_XET_CACHE"] = str(xet)
    os.environ["HF_XET_CACHE_DIR"] = str(xet)
    os.environ["TMPDIR"] = str(tmp)
    os.environ["TEMP"] = str(tmp)
    os.environ["TMP"] = str(tmp)

    from huggingface_hub import snapshot_download

    model_id = os.environ.get(
        "GRANITE_MODEL_ID", "ibm-granite/granite-3.0-2b-instruct"
    )

    print(f"target: {target_str}", flush=True)
    print(f"model:  {model_id}", flush=True)

    path = snapshot_download(model_id, cache_dir=target_str)
    print(f"DONE -> {path}", flush=True)


if __name__ == "__main__":
    main()
