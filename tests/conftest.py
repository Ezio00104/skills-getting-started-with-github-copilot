"""Pytest configuration and shared fixtures for FastAPI tests."""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Provide a TestClient instance for making API requests."""
    return TestClient(app)
