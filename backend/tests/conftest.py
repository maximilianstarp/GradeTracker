import pytest

from app import create_app
from app.models import db as _db


@pytest.fixture()
def app():
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True})
    yield app
    with app.app_context():
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_header(client):
    """Registers a fresh user and returns an Authorization header dict for it."""
    resp = client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": "test@example.com", "password": "testpass123"},
    )
    token = resp.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}
