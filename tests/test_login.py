from time import time

import jwt


def test_login(account, client, app):
    user, headers = account()
    claims = jwt.decode(
        headers["Authorization"].split()[1],
        app.config["JWT_SECRET_KEY"],
        algorithms=["HS256"],
    )
    assert claims["sub"] == str(user["id"])
    assert claims["role"] == "user"
    assert 895 <= claims["exp"] - time() <= 900
    failures = [
        client.post("/login", json={"email": email, "password": "incorrect"})
        for email in [user["email"], "missing"]
    ]
    assert all(r.status_code == 401 for r in failures)
    assert failures[0].json == failures[1].json
