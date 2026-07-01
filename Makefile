.PHONY: v2-setup v2-lint v2-typecheck v2-test v2-ingest v2-seed v2-eval-run v2-eval v2-eval-full v2-eval-report v2-ci-gate v2-watchdog-run v2-watchdog-eval v2-phase3-demo

v2-setup:
	pip install -e ".[v2-runtime,v2-dev]"

v2-lint:
	ruff check clubos2/ tests_v2/ && ruff format --check clubos2/ tests_v2/

v2-typecheck:
	mypy clubos2/

v2-test:
	pytest tests_v2/

v2-ingest:
	python -m clubos2.rag.ingest

v2-seed:
	python -m clubos2.semantic_layer.seed

v2-eval-run:
	python -m clubos2.eval.runner --golden v1 --prompt-version v1

v2-eval:
	python -m clubos2.eval.pipeline --golden v1 --prompt-version v4 --skip-ragas

v2-eval-full:
	python -m clubos2.eval.pipeline --golden v1 --prompt-version v4

v2-eval-report:
	python -m clubos2.eval.reporter --run-id $(RUN_ID)

v2-ci-gate:
	python scripts/v2_ci_gate.py

v2-watchdog-run:
	python -m clubos2.watchdog.orchestrator

v2-watchdog-eval:
	python -m pytest tests_v2/ -k "watchdog" -v

v2-phase3-demo:
	bash scripts/v2_demo_phase3.sh
