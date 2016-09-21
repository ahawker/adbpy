.PHONY: all test tox clean-pyc

all: clean-pyc test

venv-activate:
	$(eval PWD := $(shell pwd))
	test -d $(PWD)/.venv || virtualenv $(PWD)/.venv --no-site-packages --distribute
	. $(PWD)/.venv/bin/activate; pip install -Ur requirements.txt
	touch $(PWD)/.venv/bin/activate

venv: venv-activate

test: venv
	py.test tests

tox:
	tox

travis-install:
	pip install -q -r requirements/test.txt

travis: travis-install
	TOXENV=py($echo $TRAVIS_PYTHON_VERSION) | tr -d .) tox

clean-pyc:
	find . -name '__pycache__' -type d -exec rm -r {} +
	find . -iname '*.pyc' -exec rm -f {} +
	find . -iname '*.pyo' -exec rm -f {} +
	find . -iname '*.~' -exec rm -f {} +
