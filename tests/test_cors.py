"""
Test CORS configuration for the API.
"""
import pytest
from fastapi.testclient import TestClient
from main import app


class TestCORS:
    """Test CORS headers in API responses."""

    def test_cors_middleware_registered(self):
        """Test that CORS middleware is registered."""
        # Check that the middleware is in the app
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_classes

    def test_cors_allow_origins_configuration(self):
        """Test that CORS is configured with localhost origins."""
        # Find the CORS middleware
        cors_middleware = None
        for middleware in app.user_middleware:
            if middleware.cls.__name__ == "CORSMiddleware":
                cors_middleware = middleware
                break

        assert cors_middleware is not None
        assert cors_middleware.kwargs is not None

        # Check the allowed origins
        allowed_origins = cors_middleware.kwargs.get("allow_origins")
        assert allowed_origins is not None

        # Should include localhost and 127.0.0.1
        assert "http://localhost" in allowed_origins
        assert "http://127.0.0.1" in allowed_origins

    def test_cors_allow_credentials(self):
        """Test that CORS allows credentials."""
        cors_middleware = None
        for middleware in app.user_middleware:
            if middleware.cls.__name__ == "CORSMiddleware":
                cors_middleware = middleware
                break

        assert cors_middleware is not None
        assert cors_middleware.kwargs.get("allow_credentials") is True

    def test_cors_allow_all_methods(self):
        """Test that CORS allows all methods."""
        cors_middleware = None
        for middleware in app.user_middleware:
            if middleware.cls.__name__ == "CORSMiddleware":
                cors_middleware = middleware
                break

        assert cors_middleware is not None
        allowed_methods = cors_middleware.kwargs.get("allow_methods")
        assert allowed_methods == ["*"]

    def test_cors_allow_all_headers(self):
        """Test that CORS allows all headers."""
        cors_middleware = None
        for middleware in app.user_middleware:
            if middleware.cls.__name__ == "CORSMiddleware":
                cors_middleware = middleware
                break

        assert cors_middleware is not None
        allowed_headers = cors_middleware.kwargs.get("allow_headers")
        assert allowed_headers == ["*"]

