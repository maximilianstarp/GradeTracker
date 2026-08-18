"""Rate limiting is disabled under TESTING (see app/__init__.py) so the rest
of the suite isn't accidentally rate-limited by fast, repeated requests.
This file explicitly re-enables it against an isolated app instance to
verify the limiter is actually wired up and enforced.
"""
import pytest

from app import create_app
from app.models import db as _db


@pytest.fixture()
def limited_client():
    app = create_app(
        {"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True, "RATELIMIT_ENABLED": True}
    )
    with app.app_context():
        _db.create_all()
    yield app.test_client()
    with app.app_context():
        _db.drop_all()


class TestRateLimiting:
    def test_login_is_rate_limited_per_ip(self, limited_client):
        payload = {"email": "nobody@example.com", "password": "whatever123"}

        responses = [limited_client.post("/api/auth/login", json=payload).status_code for _ in range(11)]

        assert responses.count(401) == 10  # the configured "10 per minute" limit
        assert responses[-1] == 429

    def test_register_is_rate_limited_per_ip(self, limited_client):
        def register(i):
            return limited_client.post(
                "/api/auth/register",
                json={"username": f"user{i}", "email": f"user{i}@example.com", "password": "somepass123"},
            ).status_code

        responses = [register(i) for i in range(6)]

        assert responses.count(201) == 5  # the configured "5 per hour" limit
        assert responses[-1] == 429
