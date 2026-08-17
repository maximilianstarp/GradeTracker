import os

from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate

from app.models import db


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
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me-in-production"),
    )
    if config:
        app.config.from_mapping(config)

    CORS(
        app,
        resources={r"/api/*": {"origins": "*"}},
        allow_headers=["Content-Type", "Authorization"],
    )

    db.init_app(app)
    Migrate(app, db)

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
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "not_found"}), 404

    return app
