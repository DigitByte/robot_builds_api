from robot_builds_api.extensions import db
from robot_builds_api.models import User


def test_current_database_role(app, client, account):
    user, auth = account()
    assert client.get("/admin/ping", headers=auth).status_code == 403
    cli = app.test_cli_runner()
    assert cli.invoke(args=["promote-admin", user["email"]]).exit_code == 0
    assert client.get("/admin/ping", headers=auth).status_code == 200
    admin_token = client.post(
        "/login", json={"email": user["email"], "password": "test-password"}
    ).json["access_token"]
    with app.app_context():
        db.session.get(User, user["id"]).role = "user"
        db.session.commit()
    assert (
        client.get(
            "/admin/ping", headers={"Authorization": f"Bearer {admin_token}"}
        ).status_code
        == 403
    )
    assert cli.invoke(args=["promote-admin", "missing"]).exit_code != 0
