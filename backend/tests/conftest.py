import pytest

from app import create_app
from app.models import db as _db


@pytest.fixture()
def app():
    # Tests use an isolated in-memory SQLite database per test, built straight
    # from the current models via create_all() - fast and self-contained.
    # Real deployments (Postgres) get their schema from the Alembic
    # migrations in backend/migrations/ instead (see `flask db upgrade`).
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True})
    with app.app_context():
        _db.create_all()
    yield app
    with app.app_context():
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def sent_codes(monkeypatch):
    """Captures verification/reset codes instead of emailing them, so tests
    can read the plaintext code straight off this list."""
    codes = []

    def fake_send(to, purpose, code):
        codes.append({"to": to, "purpose": purpose, "code": code})

    monkeypatch.setattr("app.routes.auth.send_verification_code", fake_send)
    return codes


@pytest.fixture()
def auth_header(client, sent_codes):
    """Registers a fresh user and returns an Authorization header dict for it."""
    resp = client.post(
        "/api/auth/register",
        json={"username": "testuser", "email": "test@example.com", "password": "testpass123"},
    )
    token = resp.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}
