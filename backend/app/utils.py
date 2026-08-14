from flask import jsonify

from app.models import db


def error(message: str, status: int = 400):
    return jsonify({"error": message}), status


def get_owned(model, id_, user_id):
    """Fetch a row by primary key, scoped to the owning user.

    Returns None (route should respond 404) if the row doesn't exist or
    belongs to a different user - deliberately the same response either way,
    so a request never reveals whether another user's row exists.
    """
    row = db.session.get(model, id_)
    if row is None or row.user_id != user_id:
        return None
    return row
