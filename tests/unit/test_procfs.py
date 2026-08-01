"""Unit tests for utils/procfs.py's defensive readers.

Uses tmp_path-backed files instead of mocking or reading real /proc, since
/proc content is non-deterministic and Linux-only -- these helpers just
read arbitrary paths, so a plain file exercises the same code paths.
"""

from __future__ import annotations

import pytest

from linux_opt.core.exceptions import PermissionDeniedError
from linux_opt.utils import procfs


def test_read_text_missing_file_returns_none(tmp_path):
    assert procfs.read_text(tmp_path / "does-not-exist") is None


def test_read_text_existing_file(tmp_path):
    f = tmp_path / "value"
    f.write_text("hello\n")
    assert procfs.read_text(f) == "hello\n"


def test_read_lines_splits_on_newline(tmp_path):
    f = tmp_path / "lines"
    f.write_text("a\nb\nc")
    assert procfs.read_lines(f) == ["a", "b", "c"]


def test_read_lines_missing_file_returns_empty_list(tmp_path):
    assert procfs.read_lines(tmp_path / "missing") == []


def test_read_int_parses_valid_integer(tmp_path):
    f = tmp_path / "n"
    f.write_text("42\n")
    assert procfs.read_int(f) == 42


def test_read_int_returns_none_on_garbage(tmp_path):
    f = tmp_path / "n"
    f.write_text("not-a-number")
    assert procfs.read_int(f) is None


def test_read_int_missing_file_returns_none(tmp_path):
    assert procfs.read_int(tmp_path / "missing") is None


def test_read_kv_file_parses_colon_separated_pairs(tmp_path):
    f = tmp_path / "meminfo"
    f.write_text("MemTotal:       16384 kB\nMemFree:        8192 kB\n")
    result = procfs.read_kv_file(f)
    assert result == {"MemTotal": "16384 kB", "MemFree": "8192 kB"}


def test_read_kv_file_ignores_lines_without_separator(tmp_path):
    f = tmp_path / "odd"
    f.write_text("no-colon-here\nKey: value\n")
    assert procfs.read_kv_file(f) == {"Key": "value"}


def test_list_dir_lists_entries_sorted(tmp_path):
    (tmp_path / "b").mkdir()
    (tmp_path / "a").mkdir()
    assert procfs.list_dir(tmp_path) == ["a", "b"]


def test_list_dir_missing_directory_returns_empty_list(tmp_path):
    assert procfs.list_dir(tmp_path / "missing") == []


def test_read_text_raises_permission_denied_error(tmp_path, monkeypatch):
    f = tmp_path / "blocked"
    f.write_text("secret")

    def _raise_permission_error(*args, **kwargs):
        raise PermissionError("denied")

    monkeypatch.setattr("pathlib.Path.read_text", _raise_permission_error)
    with pytest.raises(PermissionDeniedError):
        procfs.read_text(f)
