.PHONY: v2-setup v2-lint v2-typecheck v2-test v2-ingest v2-seed

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
