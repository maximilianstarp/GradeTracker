def register(client, name="Test User", email="test@example.com", password="testpass123"):
    return client.post(
        "/api/auth/register", json={"name": name, "email": email, "password": password}
    )


class TestRegister:
    def test_register_returns_token_and_user(self, client):
        resp = register(client)
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["token"]
        assert body["user"]["email"] == "test@example.com"
        assert body["user"]["name"] == "Test User"
        assert "password" not in body["user"]

    def test_email_normalized_and_case_insensitive_duplicate(self, client):
        register(client, email="Test@Example.com")
        resp = register(client, email="test@example.com")
        assert resp.status_code == 409

    def test_invalid_email_rejected(self, client):
        resp = register(client, email="not-an-email")
        assert resp.status_code == 400

    def test_short_password_rejected(self, client):
        resp = register(client, password="short")
        assert resp.status_code == 400


class TestLogin:
    def test_login_succeeds_with_correct_credentials(self, client):
        register(client)
        resp = client.post(
            "/api/auth/login", json={"email": "test@example.com", "password": "testpass123"}
        )
        assert resp.status_code == 200
        assert resp.get_json()["token"]

    def test_login_fails_with_wrong_password(self, client):
        register(client)
        resp = client.post(
            "/api/auth/login", json={"email": "test@example.com", "password": "wrongpass"}
        )
        assert resp.status_code == 401

    def test_login_fails_for_unknown_email(self, client):
        resp = client.post(
            "/api/auth/login", json={"email": "nobody@example.com", "password": "whatever123"}
        )
        assert resp.status_code == 401


class TestMe:
    def test_me_requires_auth(self, client):
        assert client.get("/api/auth/me").status_code == 401

    def test_me_returns_current_user(self, client, auth_header):
        resp = client.get("/api/auth/me", headers=auth_header)
        assert resp.status_code == 200
        assert resp.get_json()["email"] == "test@example.com"

    def test_update_name_requires_current_password(self, client, auth_header):
        resp = client.patch("/api/auth/me", json={"name": "New Name"}, headers=auth_header)
        assert resp.status_code == 401

    def test_update_name_with_correct_password(self, client, auth_header):
        resp = client.patch(
            "/api/auth/me",
            json={"name": "New Name", "current_password": "testpass123"},
            headers=auth_header,
        )
        assert resp.status_code == 200
        assert resp.get_json()["name"] == "New Name"

    def test_update_password_then_login_with_new_password(self, client, auth_header):
        client.patch(
            "/api/auth/me",
            json={"current_password": "testpass123", "new_password": "newpass456"},
            headers=auth_header,
        )
        resp = client.post(
            "/api/auth/login", json={"email": "test@example.com", "password": "newpass456"}
        )
        assert resp.status_code == 200

    def test_update_email_to_existing_one_rejected(self, client, auth_header):
        register(client, email="taken@example.com", password="somepass123")
        resp = client.patch(
            "/api/auth/me",
            json={"email": "taken@example.com", "current_password": "testpass123"},
            headers=auth_header,
        )
        assert resp.status_code == 409
