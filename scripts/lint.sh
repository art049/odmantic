#!/bin/bash
set -e
flake8 src/ tests/
find "$(pwd)/src" -type f -name "\"*.py\"" ! -name "\"*test_*\"" \
    -exec python -m mypy {} +
