"""Guards the env-var handling in create_app() - in particular
docker-compose.yml's `${VAR:-}` substitution, which sets an EMPTY STRING in
the container when a var is unset on the host rather than leaving it truly
absent. `os.environ.get(key, default)` doesn't fall back to `default` for an
empty string, only for a missing key - a real regression that once made
ALLOWED_ORIGINS="" resolve to an empty CORS origins list (blocking every
browser request) instead of the intended wide-open "*" default.
"""
from app import create_app
from app.models import db as _db


def _client(app):
    with app.app_context():
        _db.create_all()
    return app.test_client()


class TestEnvVarDefaults:
    def test_empty_allowed_origins_behaves_like_unset(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_ORIGINS", "")
        app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True})
        client = _client(app)

        # A wide-open "*" config reflects whichever Origin was sent (Flask-CORS'
        # standard behavior) rather than the literal string "*" - so the real
        # regression test is that TWO arbitrary, previously-unseen origins both
        # get allowed, proving nothing is being filtered.
        for origin in ("http://example.com", "http://anything-else.test"):
            resp = client.post(
                "/api/auth/login",
                json={"email": "nobody@example.com", "password": "whatever123"},
                headers={"Origin": origin},
            )
            assert resp.headers.get("Access-Control-Allow-Origin") == origin

    def test_configured_allowed_origins_are_applied(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_ORIGINS", "http://example.com, http://other.com")
        app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True})

        client = _client(app)
        resp = client.post(
            "/api/auth/login",
            json={"email": "nobody@example.com", "password": "whatever123"},
            headers={"Origin": "http://example.com"},
        )
        assert resp.headers.get("Access-Control-Allow-Origin") == "http://example.com"

        # An origin outside the configured list must not be reflected back.
        resp = client.post(
            "/api/auth/login",
            json={"email": "nobody@example.com", "password": "whatever123"},
            headers={"Origin": "http://not-allowed.test"},
        )
        assert resp.headers.get("Access-Control-Allow-Origin") != "http://not-allowed.test"

    def test_empty_app_env_does_not_trigger_production_checks(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "")
        monkeypatch.delenv("SECRET_KEY", raising=False)
        # Must not raise - an empty APP_ENV (docker-compose default) is local
        # dev, not production, and shouldn't trip the SECRET_KEY fail-fast.
        create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True})
