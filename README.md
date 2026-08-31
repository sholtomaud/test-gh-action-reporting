# GitHub Markdown Report Action

A Python program that renders a rich GitHub-flavoured Markdown report and publishes it
straight into the GitHub Actions **job summary** (`$GITHUB_STEP_SUMMARY`) — no Actions
toolkit, no JavaScript, no third-party dependencies.

```
collect()  →  build_report()  →  ┌─ $GITHUB_STEP_SUMMARY   (rendered on the run page)
 data          Markdown          ├─ report.md              (uploaded artifact)
                                 └─ report-result.json     (downstream job input)
```

## Layout

| Path | Purpose |
| :--- | :--- |
| [src/markdown.py](src/markdown.py) | Composable Markdown block helpers + escaping |
| [src/report.py](src/report.py) | Collects data, renders the report, writes the outputs |
| [tests/](tests/) | 46 tests covering the helpers and the Actions integration |
| [.github/workflows/report.yml](.github/workflows/report.yml) | Publishes the summary, uploads artifacts, passes results downstream |
| [.github/workflows/test.yml](.github/workflows/test.yml) | pytest on Python 3.10 – 3.13 |

## Run locally

```bash
python -m src.report            # writes report.md + report-result.json
python -m src.report --stdout   # also print the Markdown
python -m pytest                # run the suite
```

Without `GITHUB_STEP_SUMMARY` set, the generator writes local files only. To preview the
exact Actions path:

```bash
GITHUB_STEP_SUMMARY=summary.md python -m src.report
```

## Run in Actions

Push to `main`, open a PR, or use **Actions → Report → Run workflow**. The report appears
on the run's Summary page and as the `markdown-report` artifact.

## Formatting the report exercises

Headings · paragraphs · emphasis (bold, italic, strikethrough) · inline code · blockquotes ·
all five alert callouts (`NOTE`, `TIP`, `IMPORTANT`, `WARNING`, `CAUTION`) · ordered,
unordered and task lists · aligned tables · text progress bars · fenced code blocks with
`python`, `diff`, `json` and `text` highlighting · Mermaid flowchart and pie chart ·
`<details>` disclosure sections · shields.io badges · LaTeX math · links · footnotes ·
horizontal rules · escaped untrusted input · a machine-readable JSON payload.

## How publishing works

The whole mechanism is two lines:

```python
summary = os.environ.get("GITHUB_STEP_SUMMARY")
Path(summary).open("a", encoding="utf-8").write(markdown)
```

Details worth knowing:

- **Append, don't overwrite.** Each step gets a summary file; overwriting discards what
  earlier steps in the same job wrote.
- **Never hard-code the path.** GitHub supplies it per step at runtime.
- **1 MiB limit.** `write_summary()` warns and truncates rather than letting GitHub drop
  the summary silently.
- **Escape untrusted values.** `markdown.escape()` neutralises `|`, `<`, `>` and newlines
  so injected content renders as data. Wrap intentional markup in `markdown.Raw`.

## Extending it

Replace the stubbed checks in `collect()` with real data — test results, an AWS inventory,
security findings, benchmark numbers. `build_report()` and the workflow YAML stay the same.

```python
def collect():
    return {
        "generated_at": datetime.now(timezone.utc),
        "checks": [Check(name, status, detail, seconds) for ... in my_results],
        "components": [...],
        "environment": {...},
    }
```
