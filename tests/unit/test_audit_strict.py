"""Tests for the strict audit append + try_append wrapper.

The contract documented in the README is that ``audit.append`` raises
when the disk write fails so the caller can drop the matching emit.
``try_append`` is best effort and only returns False.
"""

from __future__ import annotations

import pytest

from src.backend.common import audit
from src.backend.config import get_settings


def test_append_writes_a_line(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUDIT_LOG_DIR", str(tmp_path))
    get_settings.cache_clear()
    audit.append({"kind": "test", "value": 1})
    files = list(tmp_path.glob("cognitive-*.jsonl"))
    assert len(files) == 1
    contents = files[0].read_text(encoding="utf-8").strip().splitlines()
    assert len(contents) == 1
    assert '"value": 1' in contents[0]


def test_append_raises_when_open_fails(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """OS-agnostic write failure: monkeypatch the open builtin to raise."""
    monkeypatch.setenv("AUDIT_LOG_DIR", str(tmp_path))
    get_settings.cache_clear()

    real_open = open

    def _boom(file, *args, **kwargs):
        # Only blow up when the audit module tries to write, so pytest's
        # own internal open calls still work.
        if str(file).endswith(".jsonl"):
            raise PermissionError("simulated read only filesystem")
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr("builtins.open", _boom)
    with pytest.raises(Exception):
        audit.append({"kind": "test", "value": 2})


def test_try_append_swallows_failures(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUDIT_LOG_DIR", str(tmp_path))
    get_settings.cache_clear()

    real_open = open

    def _boom(file, *args, **kwargs):
        if str(file).endswith(".jsonl"):
            raise PermissionError("simulated read only filesystem")
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr("builtins.open", _boom)
    assert audit.try_append({"kind": "test", "value": 3}) is False


def test_try_append_returns_true_on_success(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUDIT_LOG_DIR", str(tmp_path))
    get_settings.cache_clear()
    assert audit.try_append({"kind": "test", "value": 4}) is True
