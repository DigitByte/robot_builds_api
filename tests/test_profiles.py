import pytest


@pytest.mark.parametrize("method", ["patch", "put"])
def test_profile_isolation(client, account, method):
    alice, auth = account("alice")
    bob, other = account("bob")
    update = getattr(client, method)
    assert client.get("/me", headers=auth).json["user"] == alice
    for field in ("id", "password_hash", "created_at", "role"):
        assert (
            update(
                "/me", headers=auth, json={field: bob["id"], "email": "new"}
            ).status_code
            == 400
        )
    for value in [None, " ", 1, "a" * 256]:
        assert update("/me", headers=auth, json={"email": value}).status_code == 400
    assert update("/me", headers=auth, json={"email": "bob"}).status_code == 409
    updated = update("/me", headers=auth, json={"email": " new "})
    assert updated.status_code == 200
    assert updated.json["user"] == {**alice, "email": "new"}
    assert client.get("/me", headers=other).json["user"] == bob
