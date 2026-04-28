.PHONY: install test sample graph report

install:
	pip install -e .[dev]

test:
	pytest -q

sample:
	python scripts/run_sample_search.py

graph:
	python scripts/build_sample_graph.py

report:
	python scripts/build_report_artifacts.py
