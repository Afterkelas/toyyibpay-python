# ToyyibPay Python SDK - Testing Guide

This guide explains how to run tests for the ToyyibPay Python SDK.

## Quick Start

### Install Development Dependencies

```bash
# Install the package with all development dependencies
pip install -e ".[dev]"

# Or install test dependencies only
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
# Using pytest directly
pytest

# Using make
make test

# With coverage
make coverage
```

## Test Structure

```
tests/
├── conftest.py           # Pytest configuration and shared fixtures
├── test_client.py        # Tests for synchronous client
├── test_async_client.py  # Tests for async client
├── test_models.py        # Tests for Pydantic models
├── test_webhooks.py      # Tests for webhook handling
├── test_database.py      # Tests for database operations
├── test_utils.py         # Tests for utility functions
├── test_config.py        # Tests for configuration
├── test_http_client.py   # Tests for HTTP client
└── README.md            # This file
```

## Running Specific Tests

### By Test Type

```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# Async tests
pytest -m async

# Database tests
pytest -m db

# Slow tests
pytest -m slow
```

### By File

```bash
# Test specific file
pytest tests/test_client.py

# Test specific class
pytest tests/test_client.py::TestToyyibPayClient

# Test specific method
pytest tests/test_client.py::TestToyyibPayClient::test_create_bill_success
```

### By Pattern

```bash
# Run tests matching pattern
pytest -k "bill"

# Exclude tests matching pattern
pytest -k "not async"
```

## Test Coverage

### Generate Coverage Report

```bash
# Terminal report
pytest --cov=toyyibpay --cov-report=term-missing

# HTML report
pytest --cov=toyyibpay --cov-report=html
open htmlcov/index.html

# XML report (for CI)
pytest --cov=toyyibpay --cov-report=xml
```

### Coverage Requirements

- Minimum coverage: 95%
- Branch coverage enabled
- Excludes: tests, __init__.py, migrations

## Testing with Multiple Python Versions

We use `tox` to test across Python 3.8, 3.9, 3.10, 3.11, and 3.12.

```bash
# Test all environments
tox

# Test specific Python version
tox -e py39

# Test with specific extras
tox -e py39-postgres
tox -e py39-flask
tox -e py39-fastapi

# Run linting
tox -e lint

# Run type checking
tox -e mypy
```

## Database Tests

Database tests require PostgreSQL. For testing, we use SQLite in-memory database by default.

### Local PostgreSQL Testing

```bash
# Set database URL
export DATABASE_URL="postgresql://user:pass@localhost/toyyibpay_test"

# Run database tests
pytest -m db
```

### Test Database Setup

```bash
# Create test database
make db-create

# Drop test database
make db-drop

# Reset test database
make db-reset
```

## Mocking and Fixtures

### Common Fixtures

- `test_config` - Test configuration
- `client` - Synchronous client instance
- `async_client` - Async client instance
- `sample_bill_data` - Sample bill creation data
- `sample_callback_data` - Sample webhook data
- `db_session` - Database session
- `payment_store` - Payment store instance

### Mocking HTTP Requests

```python
def test_create_bill(client, mock_httpx_client):
    mock_client, mock_response = mock_httpx_client
    mock_response.json.return_value = {"BillCode": "ABC123"}
    
    bill = client.create_bill(...)
    assert bill.bill_code == "ABC123"
```

## Debugging Tests

### Run with Debugging

```bash
# Drop into debugger on failure
pytest --pdb

# Use IPython debugger
pytest --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb

# Verbose output
pytest -vvs

# Show local variables
pytest -l
```

### Using Make

```bash
# Debug specific test
make debug-test
```

## Continuous Integration

Tests are automatically run on:
- Push to main branch
- Pull requests
- Scheduled daily runs

### CI Test Command

```bash
# Simpler output for CI
pytest -v --tb=short
```

## Performance Testing

### Benchmarks

```bash
# Run benchmarks
pytest tests/benchmarks/ --benchmark-only

# Compare benchmarks
pytest tests/benchmarks/ --benchmark-compare

# Save benchmark results
pytest tests/benchmarks/ --benchmark-save=baseline
```

### Profiling

```bash
# Profile tests
pytest --profile

# Generate profile report
pytest --profile-svg
```

## Writing Tests

### Test Structure

```python
import pytest
from toyyibpay import Client

class TestFeature:
    """Test feature description."""
    
    @pytest.mark.unit
    def test_something(self, client):
        """Test specific behavior."""
        # Arrange
        data = {"key": "value"}
        
        # Act
        result = client.method(data)
        
        # Assert
        assert result.success is True
```

### Best Practices

1. **Use markers** - Mark tests appropriately (unit, integration, async, etc.)
2. **Use fixtures** - Reuse common test setup
3. **Mock external services** - Don't make real API calls in unit tests
4. **Test edge cases** - Include error cases and boundary conditions
5. **Keep tests focused** - One test should test one thing
6. **Use descriptive names** - Test names should explain what they test

### Adding New Tests

1. Create test file following naming convention: `test_*.py`
2. Import necessary modules and fixtures
3. Write test class and methods
4. Use appropriate markers
5. Run tests to ensure they pass
6. Check coverage hasn't decreased

## Troubleshooting

### Common Issues

1. **Import errors** - Ensure package is installed: `pip install -e .`
2. **Database errors** - Check DATABASE_URL is set correctly
3. **Async test errors** - Ensure using `pytest-asyncio` and `@pytest.mark.asyncio`
4. **Coverage too low** - Add tests for uncovered lines shown in report

### Getting Help

- Check test output for detailed error messages
- Run with `-vvs` for verbose output
- Use `--pdb` to debug failing tests
- Check CI logs for environment-specific issues

## Contributing

When adding new features:

1. Write tests first (TDD)
2. Ensure all tests pass
3. Maintain or increase coverage
4. Update test documentation if needed
5. Run `make lint` before committing
