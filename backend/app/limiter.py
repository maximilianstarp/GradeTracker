"""Shared Flask-Limiter instance.

Kept in its own module (rather than created inside create_app) so route
modules can import it directly to decorate individual endpoints without a
circular import back to app/__init__.py.
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour"],
    # Explicit (rather than the implicit default) so flask-limiter doesn't
    # warn on every start - see the storage-backend note in app/__init__.py.
    storage_uri="memory://",
)
