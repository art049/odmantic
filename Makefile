PYTHON_VERSIONS = \
	3.6 \
	3.8 \

PYTHON_DEV_VERSION = 3.8

.PHONY: $(addprefix env-,$(PYTHON_VERSIONS))
$(addprefix env-,$(PYTHON_VERSIONS)):
	$(eval PY_VERSION := $(subst env-,,$@))
	$(eval PY := $(shell which python$(PY_VERSION)))
	@if [ -z "$(PY)" ]; then echo "\e[31mpython$(PY_VERSION) not found\e[0m" ; exit 1; fi
	@poetry env use $(PY)

.PRECIOUS: poetry.lock.%
poetry.lock.%: pyproject.toml
	@($(MAKE) env-$*)
	@-cp -f $@ poetry.lock
	@poetry install
	@cp -f poetry.lock $@

.PHONY: setup
setup: $(addprefix poetry.lock.,$(PYTHON_VERSIONS))
	@$(eval VENV_PATH := $(shell poetry env list --full-path | cut -f1 --delimiter=" " | grep py$(PYTHON_DEV_VERSION)))
	@ln -sf $(VENV_PATH) ./.venv
	@echo "Successfuly linked python$(PYTHON_DEV_VERSION) ($(VENV_PATH)) to the local virtualenv (.venv)"

test-%: poetry.lock.% env-%
	@echo "\e[1m\e[96mRunning tests with python$*\e[0m"
	@poetry run pytest -q -rs -c pytest.ini

.PHONY: test
test: $(addprefix test-,$(PYTHON_VERSIONS))

.PHONY: mongo-test-server
mongo-test-server:
	docker run --net=host --name odmantic-mongo-test -d mongo:4.2

.PHONY: lint
lint:
	pre-commit run --all-files

.PHONY: format
format:
	poetry run isort -y
	poetry run black ./

.PHONY: docs-server
docs-server:
	poetry run mkdocs serve
