"""Unit tests for health endpoint."""

from flask.testing import FlaskClient


class TestHealthEndpoint:
    """Tests for /api/v1/health endpoint."""

    def test_health_returns_200(self, client: FlaskClient) -> None:
        """Test health endpoint returns 200 status."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_returns_healthy_status(self, client: FlaskClient) -> None:
        """Test health endpoint returns healthy status in body."""
        response = client.get("/api/v1/health")
        data = response.get_json()
        assert data == {"status": "healthy"}

    def test_health_content_type(self, client: FlaskClient) -> None:
        """Test health endpoint returns JSON content type."""
        response = client.get("/api/v1/health")
        assert "application/json" in response.content_type
