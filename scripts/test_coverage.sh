#!/usr/bin/env bash
# Script to run tests with coverage locally (mimics CI behavior)

set -e

echo "Running tests with coverage and JUnit XML output..."
echo "================================================"

# Run pytest with all coverage options
uv run pytest \
    --cov=voltamanager \
    --cov-branch \
    --cov-report=xml \
    --cov-report=term-missing \
    --cov-report=html \
    --junitxml=junit.xml \
    -o junit_family=legacy \
    "$@"

echo ""
echo "================================================"
echo "Coverage report generated:"
echo "  - XML: coverage.xml (for Codecov)"
echo "  - HTML: htmlcov/index.html (for viewing)"
echo "  - JUnit: junit.xml (for test results)"
echo ""

# Show coverage summary
echo "Coverage Summary:"
uv run coverage report --precision=2

echo ""
echo "To view HTML coverage report, run:"
echo "  open htmlcov/index.html  # macOS"
echo "  xdg-open htmlcov/index.html  # Linux"
echo "  start htmlcov/index.html  # Windows"
