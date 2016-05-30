.PHONY: all test tox clean-pyc

all: clean-pyc test

test:
	py.test

tox:
	tox

clean-pyc:
	find . -name '__pycache__' -type d -exec rm -r {} +
	find . -iname '*.pyc' -exec rm -f {} +
	find . -iname '*.pyo' -exec rm -f {} +
	find . -iname '*.~' -exec rm -f {} +
