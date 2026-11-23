def test_owner_and_admin_access(client, account, app):
    owner, auth = account("owner")
    other, guest = account("other")
    assert (
        client.post(
            "/robot-builds",
            headers=auth,
            json={"name": "Scout", "user_id": other["id"]},
        ).status_code
        == 400
    )
    created = client.post("/robot-builds", headers=auth, json={"name": "Scout"})
    assert created.status_code == 201
    build = created.json["robot_build"]
    assert build["user_id"] == owner["id"]
    path = f"/robot-builds/{build['id']}"
    assert client.get("/robot-builds", headers=auth).json["robot_builds"] == [build]
    assert client.get(path, headers=auth).json["robot_build"] == build
    assert client.get("/robot-builds", headers=guest).json["robot_builds"] == []
    for method in ("get", "patch", "delete"):
        assert getattr(client, method)(path, headers=guest).status_code == 404
    assert (
        client.patch(path, headers=auth, json={"description": "Line follower"}).json[
            "robot_build"
        ]["description"]
        == "Line follower"
    )
    assert (
        client.patch(path, headers=auth, json={"user_id": other["id"]}).status_code
        == 400
    )
    assert app.test_cli_runner().invoke(args=["promote-admin", "other"]).exit_code == 0
    assert len(client.get("/robot-builds", headers=guest).json["robot_builds"]) == 1
    assert client.get(path, headers=guest).status_code == 200
    assert (
        client.patch(path, headers=guest, json={"name": "Scout II"}).status_code == 200
    )
    assert client.delete(path, headers=guest).status_code == 204
    assert client.get(path, headers=auth).status_code == 404


def test_track_project_through_stages(client, account):
    _, headers = account()
    created = client.post("/robot-builds", headers=headers, json={"name": "Crawler"})
    project = created.json["robot_build"]
    assert project["stage"] == "Planned"
    path = f"/robot-builds/{project['id']}"
    for stage in ["Building", "Testing", "Complete"]:
        assert client.patch(path, headers=headers, json={"stage": stage}).status_code == 200
        assert client.get("/robot-builds", headers=headers).json["robot_builds"][0]["stage"] == stage
    assert client.patch(path, headers=headers, json={"stage": "Unknown"}).status_code == 400
    assert client.get(path, headers=headers).json["robot_build"]["stage"] == "Complete"
