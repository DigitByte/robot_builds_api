from flask import Blueprint, g, request
from sqlalchemy.exc import IntegrityError

from .auth_utils import error, issue_token, require_auth
from .extensions import db
from .models import RobotBuild, User

api = Blueprint("api", __name__)


def payload():
    value = request.get_json(silent=True)
    return value if isinstance(value, dict) else {}


def clean_string(value, maximum):
    if isinstance(value, str):
        value = value.strip()
        if 1 <= len(value) <= maximum:
            return value
    return None


def invalid(message, fields):
    return error("VALIDATION_ERROR", message, 400, fields)


def profile(user):
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at.isoformat() + "Z",
    }


def save_profile(user, status):
    email = user.email
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        if db.session.scalar(db.select(User.id).where(User.email == email)):
            return error("EMAIL_TAKEN", "Email is already registered.", 409)
        raise
    return {"user": profile(user)}, status


@api.post("/registration")
def register():
    data = payload()
    email = clean_string(data.get("email"), 255)
    password = data.get("password")
    fields = {}
    if email is None:
        fields["email"] = "Enter an email between 1 and 255 characters."
    if password is None:
        fields["password"] = "Password is required."
    elif not isinstance(password, str) or not 8 <= len(password) <= 128:
        fields["password"] = "Enter a password between 8 and 128 characters."
    if fields:
        return invalid("Invalid registration data.", fields)
    user = User(email=email, role="user")
    user.set_password(password)
    db.session.add(user)
    return save_profile(user, 201)


@api.post("/login")
def login():
    data = payload()
    email = clean_string(data.get("email"), 255)
    password = data.get("password")
    user = db.session.scalar(db.select(User).where(User.email == email))
    if (
        not user
        or not isinstance(password, str)
        or not 8 <= len(password) <= 128
        or not user.check_password(password)
    ):
        return error("INVALID_CREDENTIALS", "Invalid email or password.", 401)
    return {"access_token": issue_token(user)}


@api.route("/me", methods=["GET", "PATCH", "PUT"])
@require_auth
def me():
    user = g.current_user
    if request.method == "GET":
        return {"user": profile(user)}
    data = payload()
    email = clean_string(data.get("email"), 255)
    fields = {key: "Field cannot be updated." for key in data.keys() - {"email"}}
    if email is None:
        fields["email"] = "Enter an email between 1 and 255 characters."
    if fields:
        return invalid("Invalid profile data.", fields)
    user.email = email
    return save_profile(user, 200)


@api.get("/admin/ping")
@require_auth
def admin_ping():
    if g.current_user.role != "admin":
        return error("FORBIDDEN", "Administrator access required.", 403)
    return {"message": "pong"}


def visible_builds():
    query = db.select(RobotBuild)
    if g.current_user.role != "admin":
        query = query.where(RobotBuild.user_id == g.current_user_id)
    return query


def build_json(build):
    return {
        "id": build.id,
        "name": build.name,
        "description": build.description,
        "user_id": build.user_id,
        "created_at": build.created_at.isoformat() + "Z",
    }


def save_build(build, creating=False):
    data = payload()
    fields = {
        key: "Field cannot be set." for key in data.keys() - {"name", "description"}
    }
    name = clean_string(data.get("name"), 255)
    if (creating or "name" in data) and name is None:
        fields["name"] = "Enter a name between 1 and 255 characters."
    if data.get("description") is not None and not isinstance(data["description"], str):
        fields["description"] = "Enter text or null."
    if not data and not creating:
        fields["body"] = "Supply a name or description."
    if fields:
        return invalid("Invalid build data.", fields)
    if name is not None:
        build.name = name
    if "description" in data:
        build.description = data["description"]
    if creating:
        db.session.add(build)
    db.session.commit()
    return {"robot_build": build_json(build)}, 201 if creating else 200


@api.route("/robot-builds", methods=["GET", "POST"])
@require_auth
def builds():
    if request.method == "POST":
        return save_build(RobotBuild(user_id=g.current_user_id), creating=True)
    rows = db.session.scalars(visible_builds().order_by(RobotBuild.id))
    return {"robot_builds": [build_json(row) for row in rows]}


@api.route("/robot-builds/<int:build_id>", methods=["GET", "PATCH", "DELETE"])
@require_auth
def build_detail(build_id):
    build = None
    if build_id <= 2**63 - 1:
        build = db.session.scalar(visible_builds().where(RobotBuild.id == build_id))
    if build is None:
        return error("NOT_FOUND", "Build not found.", 404)
    if request.method == "GET":
        return {"robot_build": build_json(build)}
    if request.method == "PATCH":
        return save_build(build)
    db.session.delete(build)
    db.session.commit()
    return "", 204
