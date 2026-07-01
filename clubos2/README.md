# ClubOS 2.0 — Agentic AI Layer

`clubos2` is the Python package namespace hosting the agentic AI layer for ClubOS 2.0. It is designed to extend ClubOS v1 additively, meaning it lives alongside v1 and does not modify the working production v1 codebase.

## Directory Structure

```text
clubos2/
├── gateway/           # LLM Gateway with structured output and cost/token loggers
├── observability/     # Tracing configurations (e.g. LangSmith)
├── semantic_layer/    # Unified business metric dictionary and database schemas
│   └── migrations/    # Database schema migrations
├── rag/               # Retrieval Augmented Generation code
│   └── skills/        # Versioned skill markdown files for context grounding
├── tools/             # Action tools (metric queries, knowledge search)
├── agents/            # Scout, Watchdog, Investigator, and Briefer agent implementations
└── guardrails/        # Input/output validation and safety guardrails
```

## Installation

To install the v2 dependencies and register the `clubos2` editable namespace in your Python environment:

```bash
# From the repository root
pip install -e ".[v2-runtime,v2-dev]"
```

*Note: This will not impact the base v1 installation path. The v2 package can coexist in the same virtual environment (`clubosvenv`).*

## Testing

To run the v2 specific test suite:

```bash
make v2-test
```

*Note: If `make` is not installed on your system, you can run the tools directly using the virtual environment executables:*
- **Linting & Formatting**: `./clubosvenv/bin/ruff check clubos2/ tests_v2/ && ./clubosvenv/bin/ruff format --check clubos2/ tests_v2/`
- **Type Checking**: `./clubosvenv/bin/mypy clubos2/`
- **Testing**: `./clubosvenv/bin/pytest tests_v2/`

## Evaluation

ClubOS 2.0 uses a three-layer eval architecture: deterministic fabrication-rate,
deterministic behavioural compliance, and (optional) LLM-judged RAGAS metrics.
The deterministic layers gate CI; RAGAS is methodology-complete and run on demand.

```bash
make v2-eval        # deterministic layers only — fast, free, no API cost
make v2-eval-full   # includes RAGAS LLM-judged scoring (requires paid tier credentials)
make v2-ci-gate     # compare current eval output against eval/reports/baseline.json
```

Full methodology: `docs/eval_methodology.md`

## Import Usage

Because each folder contains `__init__.py` files and the package is installed in editable mode, you can import submodules cleanly from anywhere in the codebase:

```python
from clubos2.agents.scout import run_scout
```
