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
