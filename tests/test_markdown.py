"""Unit tests for the Markdown block helpers."""

from __future__ import annotations

import pytest

from src import markdown as md


def test_escape_neutralises_table_breaking_and_html():
    escaped = md.escape('a | b <img src=x> & "c"')
    assert "\\|" in escaped
    assert "&lt;img" in escaped
    assert "&amp;" in escaped


def test_escape_turns_newlines_into_breaks():
    assert md.escape("one\ntwo") == "one<br>two"


def test_raw_values_pass_through_unescaped():
    assert md.escape(md.Raw("**bold** | pipe")) == "**bold** | pipe"


def test_table_renders_header_separator_and_alignment():
    out = md.table(["A", "B"], [[1, 2]], align=["left", "right"])
    assert out.splitlines() == ["| A | B |", "| :--- | ---: |", "| 1 | 2 |"]


def test_table_rejects_ragged_rows():
    with pytest.raises(ValueError):
        md.table(["A", "B"], [[1]])


@pytest.mark.parametrize("kind", md.ALERT_TYPES)
def test_every_alert_type_renders(kind):
    assert md.alert(kind, "body").startswith(f"> [!{kind}]")


def test_alert_rejects_unknown_type():
    with pytest.raises(ValueError):
        md.alert("PANIC", "body")


def test_code_block_grows_the_fence_past_inner_backticks():
    out = md.code_block("here is ``` a fence", "text")
    assert out.startswith("````text")
    assert out.endswith("````")


def test_task_list_marks_done_items():
    assert md.task_list([(True, "a"), (False, "b")]) == "- [x] a\n- [ ] b"


def test_bar_is_clamped_and_proportional():
    assert "100%" in str(md.bar(4.2))
    assert "0%" in str(md.bar(-1))
    assert "50%" in str(md.bar(0.5))


def test_mermaid_is_dedented():
    out = md.mermaid("\n    flowchart LR\n        A --> B\n")
    assert out == "```mermaid\nflowchart LR\n    A --> B\n```"


def test_details_wraps_body_in_disclosure_element():
    out = md.details("Summary", "body", open=True)
    assert out.startswith("<details open>\n<summary>Summary</summary>")
    assert out.endswith("</details>")


def test_heading_level_is_validated():
    assert md.heading("Hi", 3) == "### Hi"
    with pytest.raises(ValueError):
        md.heading("Hi", 7)


def test_document_separates_blocks_with_blank_lines():
    doc = md.Document().add(md.heading("A"), "", md.paragraph("b"))
    assert doc.render() == "# A\n\nb\n"


def test_badge_escapes_slashes_and_dashes():
    url = str(md.badge("checks", "4/5", "blue"))
    assert "checks-4%2F5-blue" in url
    assert "-" not in md.badge("a-b", "c", "blue").split("/badge/")[1].split("-c-")[0].replace("--", "")
