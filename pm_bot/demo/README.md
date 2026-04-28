# PMBOT Demo Layer

This directory contains a deterministic local demo runner for the validated fixture-only and paper-only PMBOT pipeline.

Files:

- `demo_market_bundle.v1.json`: local references to fixtures, expected outputs, and module entry points used by the demo.
- `run_paper_research_demo.py`: recomputes the validated PMBOT pipeline locally and renders either JSON or Markdown.
- `expected_paper_research_demo.v1.json`: expected deterministic JSON output.
- `expected_paper_research_demo.v1.md`: expected deterministic Markdown output.

Safety boundary:

- local files only
- no live API
- no network usage
- no wallet or private key handling
- no real trading
- no runtime wiring
