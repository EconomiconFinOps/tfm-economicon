import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest


def test_login_request_accepts_email_and_password():
    payload = LoginRequest(email="operator@example.com", password="secret")

    assert payload.email == "operator@example.com"
    assert payload.password == "secret"


def test_login_request_rejects_empty_password():
    with pytest.raises(ValidationError):
        LoginRequest(email="operator@example.com", password="")


@pytest.mark.parametrize("password", ["  literal password  ", "   "], ids=["padded", "spaces"])
def test_login_request_preserves_nonempty_password_literally(password):
    payload = LoginRequest(email="operator@example.com", password=password)

    assert payload.password == password
