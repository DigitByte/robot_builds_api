import secrets
from pathlib import Path

import pytest
from flask_migrate import upgrade

from robot_builds_api import create_app


@pytest.fixture
def app(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "JWT_SECRET_KEY": secrets.token_hex(32),
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
        }
    )
    with app.app_context():
        upgrade(directory=str(Path(__file__).resolve().parents[1] / "migrations"))
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def account(client):
    def create(email="dev@example.com"):
        data = {"email": email, "password": "test-password"}
        user = client.post("/registration", json=data).json["user"]
        token = client.post("/login", json=data).json["access_token"]
        return user, {"Authorization": f"Bearer {token}"}

    return create
