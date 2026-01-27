"""Shared test fixtures."""

import pytest
from flask.testing import FlaskClient
from typer.testing import CliRunner

from tryalma.cli import app as cli_app
from tryalma.webapp.app import create_app


@pytest.fixture
def client() -> FlaskClient:
    """Create a Flask test client."""
    app = create_app("testing")
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Typer CLI runner."""
    return CliRunner()


@pytest.fixture
def cli() -> "typer.Typer":
    """Return the CLI app for testing."""
    return cli_app
