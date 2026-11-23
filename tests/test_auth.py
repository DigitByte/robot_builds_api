from time import time

import jwt
import pytest


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/me"),
        ("put", "/me"),
        ("patch", "/me"),
        ("get", "/admin/ping"),
        ("get", "/robot-builds"),
        ("post", "/robot-builds"),
        ("get", "/robot-builds/1"),
        ("patch", "/robot-builds/1"),
        ("delete", "/robot-builds/1"),
    ],
)
def test_missing_header(client, method, path):
    assert getattr(client, method)(path).status_code == 401


def test_rejected_tokens(client, app, account):
    user, headers = account()
    key = app.config["JWT_SECRET_KEY"]
    claims = {"sub": str(user["id"]), "exp": int(time()) + 300}
    token = headers["Authorization"].split()[1]
    header, payload, sig = token.split(".")
    tampered = ".".join([header, payload, ("A" if sig[0] != "A" else "B") + sig[1:]])
    for bad in [
        tampered,
        "broken",
        jwt.encode({"sub": "1"}, key),
        jwt.encode({**claims, "sub": "abc"}, key),
        jwt.encode({**claims, "sub": "999"}, key),
    ]:
        result = client.get("/me", headers={"Authorization": f"Bearer {bad}"})
        assert result.status_code == 401
        assert result.json["error"]["code"] == "INVALID_TOKEN"
    expired = jwt.encode({**claims, "exp": int(time()) - 1}, key)
    result = client.get("/me", headers={"Authorization": f"Bearer {expired}"})
    assert result.status_code == 401
    assert result.json["error"]["code"] == "TOKEN_EXPIRED"
