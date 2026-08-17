def register(client, username="testuser", email="test@example.com", password="testpass123"):
    return client.post(
        "/api/auth/register", json={"username": username, "email": email, "password": password}
    )


class TestRegister:
    def test_register_returns_token_and_user(self, client, sent_codes):
        resp = register(client)
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["token"]
        assert body["user"]["email"] == "test@example.com"
        assert body["user"]["username"] == "testuser"
        assert body["user"]["email_verified"] is False
        assert "password" not in body["user"]

    def test_sends_verification_code_on_register(self, client, sent_codes):
        register(client)
        assert len(sent_codes) == 1
        assert sent_codes[0]["to"] == "test@example.com"
        assert sent_codes[0]["purpose"] == "verify_email"
        assert len(sent_codes[0]["code"]) == 6

    def test_username_normalized_and_case_insensitive_duplicate(self, client):
        register(client, username="TestUser")
        resp = register(client, username="testuser", email="other@example.com")
        assert resp.status_code == 409

    def test_invalid_username_rejected(self, client):
        resp = register(client, username="ab")
        assert resp.status_code == 400

    def test_email_normalized_and_case_insensitive_duplicate(self, client):
        register(client, email="Test@Example.com")
        resp = register(client, username="other", email="test@example.com")
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

    def test_login_works_before_email_is_verified(self, client):
        register(client)
        resp = client.post(
            "/api/auth/login", json={"email": "test@example.com", "password": "testpass123"}
        )
        assert resp.status_code == 200
        assert resp.get_json()["user"]["email_verified"] is False

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

    def test_update_username_requires_current_password(self, client, auth_header):
        resp = client.patch("/api/auth/me", json={"username": "newname"}, headers=auth_header)
        assert resp.status_code == 401

    def test_update_username_with_correct_password(self, client, auth_header):
        resp = client.patch(
            "/api/auth/me",
            json={"username": "newname", "current_password": "testpass123"},
            headers=auth_header,
        )
        assert resp.status_code == 200
        assert resp.get_json()["username"] == "newname"

    def test_update_username_to_existing_one_rejected(self, client, auth_header):
        register(client, username="taken", email="taken@example.com")
        resp = client.patch(
            "/api/auth/me",
            json={"username": "taken", "current_password": "testpass123"},
            headers=auth_header,
        )
        assert resp.status_code == 409

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
        register(client, username="other", email="taken@example.com")
        resp = client.patch(
            "/api/auth/me",
            json={"email": "taken@example.com", "current_password": "testpass123"},
            headers=auth_header,
        )
        assert resp.status_code == 409

    def test_update_email_does_not_change_it_until_verified(self, client, auth_header, sent_codes):
        resp = client.patch(
            "/api/auth/me",
            json={"email": "new@example.com", "current_password": "testpass123"},
            headers=auth_header,
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["email"] == "test@example.com"
        assert body["pending_email"] == "new@example.com"

        change_codes = [c for c in sent_codes if c["purpose"] == "change_email"]
        assert len(change_codes) == 1
        assert change_codes[0]["to"] == "new@example.com"

        # Old email still logs in, new one doesn't exist yet.
        assert (
            client.post(
                "/api/auth/login", json={"email": "test@example.com", "password": "testpass123"}
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/api/auth/login", json={"email": "new@example.com", "password": "testpass123"}
            ).status_code
            == 401
        )

    def test_resubmitting_current_email_cancels_pending_change(self, client, auth_header):
        client.patch(
            "/api/auth/me",
            json={"email": "new@example.com", "current_password": "testpass123"},
            headers=auth_header,
        )
        resp = client.patch(
            "/api/auth/me",
            json={"email": "test@example.com", "current_password": "testpass123"},
            headers=auth_header,
        )
        assert resp.status_code == 200
        assert resp.get_json()["pending_email"] is None


class TestVerifyEmail:
    def test_verify_with_correct_code(self, client, auth_header, sent_codes):
        code = sent_codes[0]["code"]
        resp = client.post("/api/auth/verify-email", json={"code": code}, headers=auth_header)
        assert resp.status_code == 200
        assert resp.get_json()["email_verified"] is True

    def test_verify_with_wrong_code_fails(self, client, auth_header):
        resp = client.post("/api/auth/verify-email", json={"code": "000000"}, headers=auth_header)
        assert resp.status_code == 400

    def test_verify_locks_out_after_too_many_attempts(self, client, auth_header):
        for _ in range(5):
            client.post("/api/auth/verify-email", json={"code": "000000"}, headers=auth_header)
        resp = client.post("/api/auth/verify-email", json={"code": "000000"}, headers=auth_header)
        assert resp.status_code == 400
        assert "Too many attempts" in resp.get_json()["error"]

    def test_verify_already_verified_rejected(self, client, auth_header, sent_codes):
        code = sent_codes[0]["code"]
        client.post("/api/auth/verify-email", json={"code": code}, headers=auth_header)
        resp = client.post("/api/auth/verify-email", json={"code": code}, headers=auth_header)
        assert resp.status_code == 400


class TestVerifyEmailChange:
    def test_verify_email_change_applies_new_address(self, client, auth_header, sent_codes):
        client.patch(
            "/api/auth/me",
            json={"email": "new@example.com", "current_password": "testpass123"},
            headers=auth_header,
        )
        code = next(c["code"] for c in sent_codes if c["purpose"] == "change_email")

        resp = client.post(
            "/api/auth/verify-email-change", json={"code": code}, headers=auth_header
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["email"] == "new@example.com"
        assert body["pending_email"] is None
        assert body["email_verified"] is True

        assert (
            client.post(
                "/api/auth/login", json={"email": "new@example.com", "password": "testpass123"}
            ).status_code
            == 200
        )

    def test_verify_email_change_without_pending_change_rejected(self, client, auth_header):
        resp = client.post(
            "/api/auth/verify-email-change", json={"code": "000000"}, headers=auth_header
        )
        assert resp.status_code == 400


class TestResendCode:
    def test_resend_before_cooldown_rejected(self, client, auth_header):
        resp = client.post("/api/auth/resend-code", headers=auth_header)
        assert resp.status_code == 429

    def test_resend_without_pending_verification_rejected(self, client, auth_header, sent_codes):
        code = sent_codes[0]["code"]
        client.post("/api/auth/verify-email", json={"code": code}, headers=auth_header)
        resp = client.post("/api/auth/resend-code", headers=auth_header)
        assert resp.status_code == 400


class TestForgotAndResetPassword:
    def test_forgot_password_sends_code_for_known_email(self, client, auth_header, sent_codes):
        resp = client.post("/api/auth/forgot-password", json={"email": "test@example.com"})
        assert resp.status_code == 200
        reset_codes = [c for c in sent_codes if c["purpose"] == "password_reset"]
        assert len(reset_codes) == 1

    def test_forgot_password_same_response_for_unknown_email(self, client):
        resp = client.post("/api/auth/forgot-password", json={"email": "nobody@example.com"})
        assert resp.status_code == 200

    def test_reset_password_with_correct_code(self, client, auth_header, sent_codes):
        client.post("/api/auth/forgot-password", json={"email": "test@example.com"})
        code = next(c["code"] for c in sent_codes if c["purpose"] == "password_reset")

        resp = client.post(
            "/api/auth/reset-password",
            json={"email": "test@example.com", "code": code, "new_password": "brandnew123"},
        )
        assert resp.status_code == 200

        assert (
            client.post(
                "/api/auth/login",
                json={"email": "test@example.com", "password": "brandnew123"},
            ).status_code
            == 200
        )

    def test_reset_password_with_wrong_code_rejected(self, client, auth_header):
        client.post("/api/auth/forgot-password", json={"email": "test@example.com"})
        resp = client.post(
            "/api/auth/reset-password",
            json={"email": "test@example.com", "code": "000000", "new_password": "brandnew123"},
        )
        assert resp.status_code == 400

    def test_reset_password_for_unknown_email_rejected(self, client):
        resp = client.post(
            "/api/auth/reset-password",
            json={"email": "nobody@example.com", "code": "123456", "new_password": "brandnew123"},
        )
        assert resp.status_code == 400


class TestDeleteMe:
    def test_delete_requires_auth(self, client):
        assert client.delete("/api/auth/me").status_code == 401

    def test_delete_requires_correct_password(self, client, auth_header):
        resp = client.delete(
            "/api/auth/me", json={"current_password": "wrongpass"}, headers=auth_header
        )
        assert resp.status_code == 401

    def test_delete_removes_account(self, client, auth_header):
        resp = client.delete(
            "/api/auth/me", json={"current_password": "testpass123"}, headers=auth_header
        )
        assert resp.status_code == 204

        assert client.get("/api/auth/me", headers=auth_header).status_code == 401
        assert (
            client.post(
                "/api/auth/login",
                json={"email": "test@example.com", "password": "testpass123"},
            ).status_code
            == 401
        )

    def test_delete_cascades_owned_data(self, client, auth_header):
        modul = client.post(
            "/api/module",
            json={"name": "Analysis", "credits": 6, "studiengang_ids": []},
            headers=auth_header,
        ).get_json()

        client.delete("/api/auth/me", json={"current_password": "testpass123"}, headers=auth_header)

        # A fresh account re-using the same email must not see leftover rows.
        register(client, email="test@example.com", password="testpass123")
        login = client.post(
            "/api/auth/login", json={"email": "test@example.com", "password": "testpass123"}
        ).get_json()
        new_header = {"Authorization": f"Bearer {login['token']}"}
        resp = client.get(f"/api/module/{modul['id']}", headers=new_header)
        assert resp.status_code == 404
