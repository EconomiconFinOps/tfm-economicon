from app.schemas.auth import LoginRequest


def test_login_request_accepts_email_and_password():
    payload = LoginRequest(email="operator@finops.local", password="secret")

    assert payload.email == "operator@finops.local"
    assert payload.password == "secret"
