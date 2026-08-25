from app.schemas.auth import LoginRequest


def test_login_request_accepts_email_and_password():
    payload = LoginRequest(email="operator@example.com", password="secret")

    assert payload.email == "operator@example.com"
    assert payload.password == "secret"
