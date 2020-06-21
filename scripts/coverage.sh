#!/bin/bash
set -e
coverage run -m pytest -c pytest.ini -v
coverage report -m
coverage xml
