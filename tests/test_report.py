"""Tests for the report generator and its Actions integration."""

from __future__ import annotations

import json

import pytest

from src import report as rp


@pytest.fixture()
def data():
    return rp.collect()


def test_summarise_counts_each_outcome(data):
    result = rp.summarise(data)
    assert result["total"] == len(data["checks"])
    assert result["passed"] + result["failed"] + result["warnings"] == result["total"]
    assert result["status"] in {"PASS", "WARN", "FAIL"}


def test_summary_status_degrades_with_the_worst_check(data):
    data["checks"] = [rp.Check("x", "fail", "broken", 0.1)]
    assert rp.summarise(data)["status"] == "FAIL"
    data["checks"] = [rp.Check("x", "pass", "fine", 0.1)]
    assert rp.summarise(data)["status"] == "PASS"


@pytest.mark.parametrize(
    "fragment",
    [
        "# 🚀 Engineering Report",
        "## 1. Executive summary",
        "## 5. Pipeline",
        "```mermaid",
        "```python",
        "```diff",
        "```json",
        "<details>",
        "<summary>",
        "> [!NOTE]",
        "> [!TIP]",
        "> [!IMPORTANT]",
        "> [!WARNING]",
        "> [!CAUTION]",
        "- [x] ",
        "- [ ] ",
        "[^gfm]",
        "$$",
        "| :--- |",
    ],
)
def test_report_exercises_each_markdown_feature(fragment):
    assert fragment in rp.build_report()


def test_report_escapes_hostile_values():
    report = rp.build_report()
    assert "<img src=x" not in report
    assert "&lt;img src=x" in report


def test_footnote_reference_has_a_definition():
    report = rp.build_report()
    assert "[^gfm]" in report and "[^gfm]:" in report


def test_report_fits_the_job_summary_limit():
    assert len(rp.build_report().encode("utf-8")) < rp.SUMMARY_LIMIT_BYTES


def test_write_summary_appends_and_truncates(tmp_path, monkeypatch):
    target = tmp_path / "summary.md"
    target.write_text("existing\n", encoding="utf-8")
    rp.write_summary("added\n", target)
    assert target.read_text(encoding="utf-8") == "existing\nadded\n"

    monkeypatch.setattr(rp, "SUMMARY_LIMIT_BYTES", 4)
    rp.write_summary("way too long", target)
    assert target.read_text(encoding="utf-8") == "existing\nadded\nway "


def test_main_writes_all_three_outputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    summary = tmp_path / "summary.md"
    output = tmp_path / "output.txt"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))

    assert rp.main([]) == 0

    assert "# 🚀 Engineering Report" in summary.read_text(encoding="utf-8")
    assert (tmp_path / "report.md").exists()
    assert json.loads((tmp_path / "report-result.json").read_text())["status"] in {"PASS", "WARN"}
    assert "status=" in output.read_text(encoding="utf-8")


def test_main_can_skip_the_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    assert rp.main(["--no-summary"]) == 0
    assert not summary.exists()
