.PHONY: help clean test test-all test-unit test-integration test-async test-db coverage lint format mypy docs build install dev-install

# Default target
help:
	@echo "ToyyibPay Python SDK - Development Commands"
	@echo ""
	@echo "Installation:"
	@echo "  make install       Install package in production mode"
	@echo "  make dev-install   Install package in development mode with all dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test          Run all tests with coverage"
	@echo "  make test-unit     Run unit tests only"
	@echo "  make test-integration  Run integration tests only"
	@echo "  make test-async    Run async tests only"
	@echo "  make test-db       Run database tests only"
	@echo "  make test-all      Run tests on all Python versions with tox"
	@echo "  make coverage      Generate coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint          Run linters (black, isort, flake8)"
	@echo "  make format        Format code with black and isort"
	@echo "  make mypy          Run type checking with mypy"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs          Build documentation"
	@echo "  make docs-serve    Build and serve documentation locally"
	@echo ""
	@echo "Build & Release:"
	@echo "  make build         Build distribution packages"
	@echo "  make clean         Clean build artifacts"
	@echo "  make release-test  Upload to TestPyPI"
	@echo "  make release       Upload to PyPI (use with caution!)"

# Installation
install:
	pip install -e .

dev-install:
	pip install -e ".[dev,postgres,flask,fastapi]"
	pre-commit install

# Cleaning
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .tox/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# Testing
test:
	pytest

test-unit:
	pytest -m unit

test-integration:
	pytest -m integration

test-async:
	pytest -m async

test-db:
	pytest -m db

test-smoke:
	pytest -m smoke -v

test-all:
	tox

test-parallel:
	pytest -n auto

# Coverage
coverage:
	pytest --cov=toyyibpay --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

coverage-report:
	coverage report

coverage-html:
	coverage html
	@echo "Opening coverage report in browser..."
	@python -m webbrowser htmlcov/index.html

# Code Quality
lint:
	black --check toyyibpay tests
	isort --check-only toyyibpay tests
	flake8 toyyibpay tests
	mypy toyyibpay

format:
	black toyyibpay tests
	isort toyyibpay tests

mypy:
	mypy toyyibpay

# Documentation
docs:
	cd docs && sphinx-build -b html . _build/html

docs-serve: docs
	@echo "Serving documentation at http://localhost:8000"
	cd docs/_build/html && python -m http.server

docs-clean:
	rm -rf docs/_build

# Build & Distribution
build: clean
	python -m build

check-build: build
	twine check dist/*

# Release (be careful!)
release-test: check-build
	twine upload --repository testpypi dist/*

release: check-build
	@echo "WARNING: About to upload to PyPI. Press Ctrl+C to cancel."
	@sleep 5
	twine upload dist/*

# Development helpers
watch-tests:
	pytest-watch

run-example-flask:
	cd examples && python flask_example.py

run-example-fastapi:
	cd examples && uvicorn fastapi_example:app --reload

# Git hooks
pre-commit:
	pre-commit run --all-files

# Environment
env:
	@echo "Creating virtual environment..."
	python -m venv venv
	@echo "Activate with: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)"

# Database
db-create:
	@echo "Creating test database..."
	createdb toyyibpay_test

db-drop:
	@echo "Dropping test database..."
	dropdb toyyibpay_test

db-reset: db-drop db-create
	@echo "Database reset complete"

# Dependencies
deps-update:
	pip list --outdated
	@echo ""
	@echo "Run 'pip install --upgrade <package>' to update specific packages"

deps-tree:
	pipdeptree

# Security
security-check:
	pip-audit
	bandit -r toyyibpay/

# Performance
benchmark:
	pytest tests/benchmarks/ --benchmark-only

profile:
	pytest tests/ --profile

# Debugging
debug-test:
	pytest -vvs --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb

# CI/CD helpers
ci-test:
	pytest -v --tb=short

ci-lint:
	make lint

ci-build:
	make build

# Version management
version:
	@python -c "import toyyibpay; print(f'ToyyibPay SDK v{toyyibpay.__version__}')"

# Requirements
requirements:
	pip freeze > requirements-lock.txt

requirements-update:
	pip install --upgrade -r requirements.txt -r requirements-dev.txt