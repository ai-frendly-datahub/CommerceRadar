.PHONY: install test sample graph

install:
	pip install -e .[dev]

test:
	pytest -q

sample:
	python scripts/run_sample_search.py

graph:
	python scripts/build_sample_graph.py
