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
