import logging
import os

from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from sqlalchemy import text

from app.limiter import limiter
from app.models import db

logger = logging.getLogger("app")

_DEFAULT_SECRET_KEY = "dev-secret-change-me-in-production"


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)

    app.config.from_mapping(
        # Local default matches the `db` service in docker-compose.yml so
        # `docker compose up` works out of the box; override for anything
        # beyond local use.
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", "postgresql+psycopg://grade_tracker:grade_tracker@localhost:5432/grade_tracker"
        ),
        # Recover transparently from connections Postgres has dropped (e.g.
        # after idling past its timeout) instead of surfacing a stale-connection
        # error on the next request; recycle before typical proxy/DB timeouts.
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True, "pool_recycle": 1800},
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JSON_SORT_KEYS=False,
        SECRET_KEY=os.environ.get("SECRET_KEY", _DEFAULT_SECRET_KEY),
    )
    if config:
        app.config.from_mapping(config)

    # Set by the deploy workflow / prod compose override only - local runs
    # (docker-compose.yml, `flask run`, tests) never set this, so the
    # documented "docker compose up --build" quick-start keeps working with
    # the insecure default. A real deployment must set it explicitly.
    # docker-compose.yml passes ALLOWED_ORIGINS/APP_ENV/SENTRY_DSN through as
    # `${VAR:-}`, which sets the container's env var to an EMPTY STRING when
    # unset on the host - not truly absent. `os.environ.get(key, default)`
    # only falls back to `default` when the key is missing entirely, so an
    # empty string would otherwise defeat the local-dev defaults below.
    # `or` treats "" the same as unset for all three.
    app_env = os.environ.get("APP_ENV") or "development"
    if app_env == "production" and app.config["SECRET_KEY"] == _DEFAULT_SECRET_KEY:
        raise RuntimeError(
            "APP_ENV=production but SECRET_KEY is still the insecure default - "
            "set a real SECRET_KEY (see .env.example)."
        )

    sentry_dsn = os.environ.get("SENTRY_DSN")
    if sentry_dsn:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration

        sentry_sdk.init(dsn=sentry_dsn, integrations=[FlaskIntegration()], traces_sample_rate=0.1)

    # "*" (the default) is fine for local dev; a real deployment should set
    # ALLOWED_ORIGINS to the frontend's actual origin(s), comma-separated.
    allowed_origins = os.environ.get("ALLOWED_ORIGINS") or "*"
    if allowed_origins == "*":
        if app_env == "production":
            logger.warning(
                "ALLOWED_ORIGINS is unset in production - CORS is wide open. "
                "Set it to the frontend's origin(s)."
            )
        origins = "*"
    else:
        origins = [o.strip() for o in allowed_origins.split(",") if o.strip()]

    CORS(
        app,
        resources={r"/api/*": {"origins": origins}},
        allow_headers=["Content-Type", "Authorization"],
    )

    db.init_app(app)
    Migrate(app, db)

    # In-memory storage: fine for a single-instance beta. Once running
    # behind multiple workers/hosts that need to agree on the same limits,
    # point RATELIMIT_STORAGE_URI (see flask-limiter docs) at Redis instead.
    app.config.setdefault("RATELIMIT_ENABLED", not app.testing)
    limiter.init_app(app)

    from app.routes.auth import bp as auth_bp
    from app.routes.studiengaenge import bp as studiengaenge_bp
    from app.routes.module import bp as module_bp
    from app.routes.kombimodule import bp as kombimodule_bp
    from app.routes.submissions import bp as submissions_bp
    from app.routes.stats import bp as stats_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(studiengaenge_bp)
    app.register_blueprint(module_bp)
    app.register_blueprint(kombimodule_bp)
    app.register_blueprint(submissions_bp)
    app.register_blueprint(stats_bp)

    @app.get("/api/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
        except Exception:
            logger.exception("Health check failed: database unreachable")
            return jsonify({"status": "error", "detail": "database unreachable"}), 503
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "not_found"}), 404

    return app
