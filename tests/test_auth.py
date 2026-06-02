from unittest.mock import patch


async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_register_success(client):
    with patch("api.routes.auth.send_verification_email") as mock_email:
        response = await client.post(
            "/auth/register", json={"email": "test@example.com", "password": "password123"}
        )
    assert response.status_code == 201
    assert response.json()["message"] == "인증 이메일을 발송했습니다"
    mock_email.assert_called_once_with("test@example.com")


async def test_register_duplicate_email(client):
    with patch("api.routes.auth.send_verification_email"):
        await client.post("/auth/register", json={"email": "dup@example.com", "password": "pass123"})
        response = await client.post(
            "/auth/register", json={"email": "dup@example.com", "password": "pass123"}
        )
    assert response.status_code == 409


async def test_verify_email_success(client):
    from core.security import create_email_token

    with patch("api.routes.auth.send_verification_email"):
        await client.post(
            "/auth/register", json={"email": "verify@example.com", "password": "pass123"}
        )
    token = create_email_token("verify@example.com")
    response = await client.post("/auth/verify-email", json={"token": token})
    assert response.status_code == 200


async def test_verify_email_invalid_token(client):
    response = await client.post("/auth/verify-email", json={"token": "totally-invalid"})
    assert response.status_code == 400


async def _register_and_verify(client, email: str, password: str = "pass1234"):
    with patch("api.routes.auth.send_verification_email"):
        await client.post("/auth/register", json={"email": email, "password": password})
    from core.security import create_email_token
    token = create_email_token(email)
    await client.post("/auth/verify-email", json={"token": token})


async def test_login_success(client):
    await _register_and_verify(client, "login@test.com")
    response = await client.post(
        "/auth/login", json={"email": "login@test.com", "password": "pass1234"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.cookies.get("refresh_token") is not None


async def test_login_wrong_password(client):
    await _register_and_verify(client, "wrongpw@test.com")
    response = await client.post(
        "/auth/login", json={"email": "wrongpw@test.com", "password": "badpass"}
    )
    assert response.status_code == 401


async def test_login_unverified_user(client):
    with patch("api.routes.auth.send_verification_email"):
        await client.post(
            "/auth/register", json={"email": "unverified@test.com", "password": "pass1234"}
        )
    response = await client.post(
        "/auth/login", json={"email": "unverified@test.com", "password": "pass1234"}
    )
    assert response.status_code == 403


async def test_refresh_token_rotation(client):
    await _register_and_verify(client, "refresh@test.com")
    await client.post("/auth/login", json={"email": "refresh@test.com", "password": "pass1234"})

    refresh_resp = await client.post("/auth/refresh")
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()
    assert refresh_resp.cookies.get("refresh_token") is not None


async def test_logout_invalidates_refresh_token(client):
    await _register_and_verify(client, "logout@test.com")
    await client.post("/auth/login", json={"email": "logout@test.com", "password": "pass1234"})

    logout_resp = await client.post("/auth/logout")
    assert logout_resp.status_code == 200

    # After logout, refresh must fail
    refresh_resp = await client.post("/auth/refresh")
    assert refresh_resp.status_code == 401
