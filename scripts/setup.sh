#!/bin/bash
set -e
PIPENV_VENV_IN_PROJECT=1 pipenv install --dev
pre-commit install
echo -e "\e[1mProject has been setup successfully\e[0m"
