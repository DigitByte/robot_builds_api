from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import current_app, g, request

from .extensions import db
from .models import User


def error(code, message, status, fields=None):
    detail = {"code": code, "message": message}
    if fields is not None:
        detail["fields"] = fields
    return {"error": detail}, status


def issue_token(user):
    config = current_app.config
    expiry = datetime.now(timezone.utc) + timedelta(
        minutes=config["JWT_ACCESS_LIFETIME_MINUTES"]
    )
    return jwt.encode(
        {"sub": str(user.id), "role": user.role, "exp": expiry},
        config["JWT_SECRET_KEY"],
        algorithm="HS256",
    )


def require_auth(view):
    @wraps(view)
    def authenticated(*args, **kwargs):
        parts = request.headers.get("Authorization", "").split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return error("UNAUTHORIZED", "A bearer token is required.", 401)
        try:
            claims = jwt.decode(
                parts[1],
                current_app.config["JWT_SECRET_KEY"],
                algorithms=["HS256"],
                options={"require": ["exp", "sub"]},
            )
            subject = claims["sub"]
            if (
                not isinstance(subject, str)
                or not subject.isascii()
                or not subject.isdecimal()
            ):
                raise ValueError
            user_id = int(subject)
            if not 1 <= user_id <= 2**63 - 1:
                raise ValueError
        except jwt.ExpiredSignatureError:
            return error("TOKEN_EXPIRED", "Access token has expired.", 401)
        except (jwt.InvalidTokenError, ValueError, TypeError, OverflowError):
            return error("INVALID_TOKEN", "Invalid access token.", 401)
        user = db.session.get(User, user_id)
        if user is None:
            return error("INVALID_TOKEN", "Invalid access token.", 401)
        g.current_user_id = user_id
        g.current_user = user
        return view(*args, **kwargs)

    return authenticated
