SHELL := /bin/bash

venv: venv/bin/activate
venv/bin/activate:
	test -d venv || virtualenv -p python3 --prompt "(lygadget-test-venv)" --distribute venv
	touch venv/bin/activate
	( \
		source venv/bin/activate; \
		pip install -r requirements-test.txt; \
		pip install -e .; \
	)

purge:
	rm -rf venv

test: venv
	source venv/bin/activate && pytest tests

.PHONY: purge test