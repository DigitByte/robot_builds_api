import pytest
from flask_migrate import upgrade
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from robot_builds_api.extensions import db


def test_migrated_schema(app):
    with app.app_context():
        assert (
            db.session.scalar(text("SELECT version_num FROM alembic_version")) == "0001"
        )
        assert db.session.scalar(text("PRAGMA foreign_keys")) == 1
        (fk,) = inspect(db.engine).get_foreign_keys("robot_builds")
        assert (
            fk["constrained_columns"],
            fk["referred_table"],
            fk["referred_columns"],
        ) == (["user_id"], "users", ["id"])
        db.session.execute(
            text("INSERT INTO users(email,password_hash) VALUES ('fixture','unused')")
        )
        db.session.commit()
        upgrade()
        assert (
            db.session.scalar(text("SELECT role FROM users WHERE email='fixture'"))
            == "user"
        )
        for owner in [None, 99]:
            with pytest.raises(IntegrityError):
                db.session.execute(
                    text(
                        "INSERT INTO robot_builds(name,user_id) VALUES ('test', :owner)"
                    ),
                    {"owner": owner},
                )
            db.session.rollback()
