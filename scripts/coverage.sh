#!/bin/bash
set -e
coverage run -m pytest -c pytest.ini
coverage xml
