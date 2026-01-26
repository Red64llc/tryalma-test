# TryAlma

A Python CLI and REST API application.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

```bash
# Install dependencies
uv sync
```

## CLI Usage

```bash
# Show help
uv run tryalma --help

# Greet with default name
uv run tryalma hello

# Greet with custom name
uv run tryalma hello --name "Alice"

# Show version
uv run tryalma version
```

## API Usage

```bash
# Start the development server
uv run uvicorn tryalma.main:app --reload

# Health check
curl http://localhost:8000/api/v1/health
```

API documentation available at `http://localhost:8000/docs` when server is running.

## Web App Usage

The Document Upload UI is a Flask-based web application for uploading passport and G-28 documents with automatic data extraction.

```bash
# Start the Flask development server
uv run flask --app tryalma.webapp.app:create_app run

# Start with debug mode and auto-reload
uv run flask --app tryalma.webapp.app:create_app run --debug

# Start on a specific port
uv run flask --app tryalma.webapp.app:create_app run --port 5001

# Production mode
uv run flask --app 'tryalma.webapp.app:create_app("production")' run
```

The web app will be available at `http://localhost:5000` by default.

## Datasets

Passport and ID card images are available for testing document extraction. Quick start:

```bash
# Download datasets
uv run python datasets/scripts/download_datasets.py download

# Organize into unified structure
uv run python datasets/scripts/organize_dataset.py
```

See [datasets/README.md](datasets/README.md) for full documentation including available datasets, metadata format, and quality augmentation options.

## Testing

```bash
# Run all tests with coverage
uv run pytest

# Run tests without coverage
uv run pytest --no-cov

# Run specific test file
uv run pytest tests/unit/test_core.py

# Run with verbose output
uv run pytest -v
```
