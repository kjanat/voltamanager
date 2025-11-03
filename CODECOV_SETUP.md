# Codecov Setup Guide

This project is configured to use Codecov for code coverage reporting and test analytics.

## Configuration Files

### 1. GitHub Actions Workflow (`.github/workflows/ci.yml`)

- Runs tests on push and pull requests to master/develop branches
- Tests across multiple OS (Ubuntu, Windows, macOS) with Python 3.13
- Generates coverage.xml and junit.xml files
- Uploads coverage reports to Codecov
- Uploads test results to Codecov Test Analytics

### 2. Codecov Configuration (`codecov.yml`)

- Sets coverage precision to 2 decimal places
- Defines coverage range from 70% to 100%
- Sets project and patch coverage targets
- Ignores test files and non-source directories
- Defines flags for unit tests and test results

### 3. Test Configuration (`setup.cfg`)

- Configures coverage.py settings
- Defines test discovery patterns
- Sets up coverage report formats (XML, HTML, terminal)
- Defines pytest markers for test categorization

### 4. Local Testing Script (`scripts/test_coverage.sh`)

- Run locally to generate coverage reports
- Mimics CI behavior for consistency
- Generates all required report formats

## Setup Steps

### 1. Add Codecov Token to GitHub Repository

1. Sign up at [codecov.io](https://codecov.io)
1. Add your repository to Codecov
1. Copy your repository token
1. Go to your GitHub repository settings
1. Navigate to Settings → Secrets and variables → Actions
1. Add a new repository secret named `CODECOV_TOKEN` with your token

### 2. Enable GitHub Actions

GitHub Actions should be enabled by default, but verify:

1. Go to Settings → Actions → General
1. Ensure "Allow all actions and reusable workflows" is selected

### 3. Run Tests Locally

```bash
# Using the test coverage script
./scripts/test_coverage.sh

# Or manually with pytest
uv run pytest --cov=voltamanager --cov-branch --cov-report=xml --junitxml=junit.xml
```

### 4. View Coverage Reports

After running tests locally:

- **Terminal**: Coverage summary is displayed after tests
- **HTML**: Open `htmlcov/index.html` in your browser
- **XML**: `coverage.xml` (for Codecov upload)
- **JUnit**: `junit.xml` (for test results)

## CI/CD Pipeline

The CI pipeline runs automatically on:

- Push to master or develop branches
- Pull requests to master or develop branches

Pipeline stages:

1. **Lint**: Check code formatting and style
1. **Type Check**: Run mypy and pyright
1. **Security**: Run bandit security checks
1. **Test**: Run pytest with coverage on multiple OS
1. **Build**: Build distribution packages

## Coverage Goals

- **Project Target**: Automatic (based on current coverage)
- **Patch Target**: Automatic (for new code in PRs)
- **Minimum Coverage**: 70%
- **Current Coverage**: ~88%

## Badges

Add these badges to your README:

```markdown
[![CI](https://github.com/kjanat/voltamanager/actions/workflows/ci.yml/badge.svg)](https://github.com/kjanat/voltamanager/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/kjanat/voltamanager/branch/master/graph/badge.svg?token=YOUR_TOKEN)](https://codecov.io/gh/kjanat/voltamanager)
```

## Troubleshooting

### Coverage Not Uploading

- Verify `CODECOV_TOKEN` is set in repository secrets
- Check GitHub Actions logs for upload errors
- Ensure coverage.xml is being generated

### Test Results Not Showing

- Verify junit.xml is being generated
- Check that `junit_family=legacy` is set
- Ensure test-results-action is not failing

### Low Coverage on New Code

- Write tests for new features before implementing
- Use `--cov-report=term-missing` to see uncovered lines
- Focus on testing business logic, not just happy paths

## Best Practices

1. **Write tests first**: Follow TDD when possible
1. **Maintain coverage**: Don't merge PRs that significantly reduce coverage
1. **Test edge cases**: Cover error conditions and edge cases
1. **Use markers**: Tag slow tests with `@pytest.mark.slow`
1. **Review reports**: Check HTML coverage reports for gaps
1. **Monitor trends**: Use Codecov dashboard to track coverage over time

## Resources

- [Codecov Documentation](https://docs.codecov.com)
- [Coverage.py Documentation](https://coverage.readthedocs.io)
- [Pytest Coverage Plugin](https://pytest-cov.readthedocs.io)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
