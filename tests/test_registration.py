import pytest

from robot_builds_api.extensions import db
from robot_builds_api.models import User


def test_registration(client, app):
    data = {"email": " dev@example.com ", "password": "test-password", "role": "admin"}
    result = client.post("/registration", json=data)
    assert result.status_code == 201
    profile = result.json["user"]
    assert set(profile) == {"id", "email", "created_at"}
    assert profile["created_at"].endswith("Z")
    assert profile["email"] == "dev@example.com"
    with app.app_context():
        user = db.session.get(User, profile["id"])
        assert user.role == "user"
        assert user.password_hash != data["password"]
        assert user.check_password(data["password"])
        assert not user.check_password("wrong-password")
    duplicate = client.post("/registration", json=data)
    assert duplicate.status_code == 409
    assert duplicate.json["error"]["code"] == "EMAIL_TAKEN"


@pytest.mark.parametrize(
    "field,value",
    [
        ("email", None),
        ("email", " "),
        ("email", 7),
        ("email", "e" * 256),
        ("password", None),
        ("password", 123),
        ("password", "p" * 7),
        ("password", "p" * 129),
    ],
)
def test_invalid_fields(client, field, value):
    data = {"email": "dev", "password": "password"}
    data[field] = value
    result = client.post("/registration", json=data)
    assert result.status_code == 400
    assert field in result.json["error"]["fields"]


def test_missing_fields(client):
    assert set(client.post("/registration", json={}).json["error"]["fields"]) == {
        "email",
        "password",
    }
