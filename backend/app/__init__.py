import os

from flask import Flask, jsonify
from flask_cors import CORS

from app.models import db


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    os.makedirs(app.instance_path, exist_ok=True)
    default_db_path = os.path.join(app.instance_path, "grades.db")

    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", f"sqlite:///{default_db_path}"),
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

    with app.app_context():
        db.create_all()

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "not_found"}), 404

    return app
