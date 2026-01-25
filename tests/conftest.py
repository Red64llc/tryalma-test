"""Shared test fixtures."""

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from tryalma.cli import app as cli_app
from tryalma.main import app as fastapi_app


@pytest.fixture
def client() -> TestClient:
    """Create a FastAPI test client."""
    return TestClient(fastapi_app)


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Typer CLI runner."""
    return CliRunner()


@pytest.fixture
def cli() -> "typer.Typer":
    """Return the CLI app for testing."""
    return cli_app
