"""Tests for export_result()."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from alice_agent.export import export_result

QUERY = "Конкуренты DDVB на рынке брендинга"
ANSWER = "Агентства A, Б, В..."


class TestExportJson:

    def test_creates_file(self, tmp_path):
        out = tmp_path / "result.json"
        export_result(query=QUERY, answer=ANSWER, path=out)
        assert out.exists()

    def test_valid_json(self, tmp_path):
        out = tmp_path / "result.json"
        export_result(query=QUERY, answer=ANSWER, path=out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["query"] == QUERY
        assert data["answer"] == ANSWER
        assert "timestamp" in data

    def test_utf8_encoding(self, tmp_path):
        out = tmp_path / "result.json"
        export_result(query=QUERY, answer=ANSWER, path=out)
        raw = out.read_bytes()
        assert "DDVB".encode("utf-8") in raw

    def test_creates_parent_dirs(self, tmp_path):
        out = tmp_path / "nested" / "deep" / "result.json"
        export_result(query=QUERY, answer=ANSWER, path=out)
        assert out.exists()


class TestExportMarkdown:

    def test_creates_file(self, tmp_path):
        out = tmp_path / "result.md"
        export_result(query=QUERY, answer=ANSWER, path=out)
        assert out.exists()

    def test_contains_query_as_heading(self, tmp_path):
        out = tmp_path / "result.md"
        export_result(query=QUERY, answer=ANSWER, path=out)
        content = out.read_text(encoding="utf-8")
        assert f"# {QUERY}" in content

    def test_contains_answer(self, tmp_path):
        out = tmp_path / "result.md"
        export_result(query=QUERY, answer=ANSWER, path=out)
        content = out.read_text(encoding="utf-8")
        assert ANSWER in content

    def test_contains_timestamp(self, tmp_path):
        out = tmp_path / "result.md"
        export_result(query=QUERY, answer=ANSWER, path=out)
        content = out.read_text(encoding="utf-8")
        # ISO 8601 timestamp present
        assert "T" in content and "Z" in content or "+" in content


class TestExportErrors:

    def test_unsupported_extension_raises(self, tmp_path):
        out = tmp_path / "result.txt"
        with pytest.raises(ValueError, match="Неподдерживаемый формат"):
            export_result(query=QUERY, answer=ANSWER, path=out)

    def test_no_extension_raises(self, tmp_path):
        out = tmp_path / "result"
        with pytest.raises(ValueError):
            export_result(query=QUERY, answer=ANSWER, path=out)
