def test_root_and_health_routes(client):
    root_response = client.get("/")
    health_response = client.get("/healthz")

    assert root_response.status_code == 200
    assert "TODO Application" in root_response.json()["message"]
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "ok"


def test_ready_route_checks_database_and_mocked_cache(client):
    response = client.get("/readyz")

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "ok"


def test_user_scope_route(client, auth_headers):
    response = client.get("/api/access/user", headers=auth_headers("user"))

    assert response.status_code == 200, response.text
    assert response.json()["scope"] == "user"
    assert response.json()["current_user"]["username"] == "user_demo"


def test_me_route_returns_current_user(client, auth_headers):
    response = client.get("/api/users/me", headers=auth_headers("user"))

    assert response.status_code == 200, response.text
    assert response.json()["username"] == "user_demo"
    assert response.json()["role"] == "user"


def test_update_avatar_route_mocks_cloudinary(client, auth_headers, monkeypatch):
    async def fake_upload_avatar(file_bytes: bytes, user_id: int) -> str:
        assert file_bytes == b"fake-image"
        return f"https://cdn.example.test/avatar-{user_id}.png"

    monkeypatch.setattr("src.services.users.upload_avatar", fake_upload_avatar)

    response = client.patch(
        "/api/users/me/avatar",
        headers=auth_headers("user"),
        files={"file": ("avatar.png", b"fake-image", "image/png")},
    )

    assert response.status_code == 200, response.text
    assert response.json()["avatar_url"].startswith("https://cdn.example.test/")


def test_update_avatar_rejects_non_image_file(client, auth_headers):
    response = client.patch(
        "/api/users/me/avatar",
        headers=auth_headers("user"),
        files={"file": ("avatar.txt", b"not image", "text/plain")},
    )

    assert response.status_code == 415, response.text
    assert response.json()["detail"] == "Only image files are allowed"


def test_todo_crud_routes(client, auth_headers):
    headers = auth_headers("user")

    list_response = client.get("/api/todos/", headers=headers)
    assert list_response.status_code == 200, list_response.text
    assert len(list_response.json()) == 1

    create_response = client.post(
        "/api/todos/",
        headers=headers,
        json={
            "title": "Write tests",
            "description": "Cover API routes",
            "completed": False,
        },
    )
    assert create_response.status_code == 201, create_response.text
    todo_id = create_response.json()["id"]

    get_response = client.get(f"/api/todos/{todo_id}", headers=headers)
    assert get_response.status_code == 200, get_response.text
    assert get_response.json()["title"] == "Write tests"

    update_response = client.put(
        f"/api/todos/{todo_id}",
        headers=headers,
        json={
            "title": "Write integration tests",
            "description": "Cover all routes",
            "completed": False,
        },
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["title"] == "Write integration tests"

    patch_response = client.patch(
        f"/api/todos/{todo_id}",
        headers=headers,
        json={"completed": True},
    )
    assert patch_response.status_code == 200, patch_response.text
    assert patch_response.json()["completed"] is True

    delete_response = client.delete(f"/api/todos/{todo_id}", headers=headers)
    assert delete_response.status_code == 204, delete_response.text

    missing_response = client.get(f"/api/todos/{todo_id}", headers=headers)
    assert missing_response.status_code == 404


def test_todo_routes_do_not_expose_other_users_todos(client, auth_headers, seeded_users):
    response = client.get(
        "/api/todos/2",
        headers=auth_headers("user"),
    )

    assert response.status_code == 404, response.text


def test_moderator_can_list_all_todos(client, auth_headers):
    response = client.get("/api/access/moderator/todos", headers=auth_headers("moderator"))

    assert response.status_code == 200, response.text
    assert len(response.json()) == 2


def test_user_cannot_open_moderator_route(client, auth_headers):
    response = client.get("/api/access/moderator/todos", headers=auth_headers("user"))

    assert response.status_code == 403, response.text


def test_admin_can_list_users_and_change_role(client, auth_headers, seeded_users):
    headers = auth_headers("admin")

    list_response = client.get("/api/access/admin/users", headers=headers)
    assert list_response.status_code == 200, list_response.text
    assert len(list_response.json()) == 4

    change_response = client.patch(
        f"/api/access/admin/users/{seeded_users['user'].id}/role",
        headers=headers,
        json={"role": "moderator"},
    )
    assert change_response.status_code == 200, change_response.text
    assert change_response.json()["role"] == "moderator"


def test_user_cannot_open_admin_route(client, auth_headers):
    response = client.get("/api/access/admin/users", headers=auth_headers("user"))

    assert response.status_code == 403, response.text


def test_admin_change_role_returns_404_for_missing_user(client, auth_headers):
    response = client.patch(
        "/api/access/admin/users/999/role",
        headers=auth_headers("admin"),
        json={"role": "moderator"},
    )

    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "User not found"
