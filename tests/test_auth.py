import pytest
import jwt
import base64
from funnel.auth import Auth
from unittest.mock import patch


def test_generate_token():
    payload = {"username": "test_user"}
    token = Auth.generate_token(payload)
    assert isinstance(token, str)

    decoded = jwt.decode(token, Auth.SECRET_KEY, algorithms=["HS256"])
    assert decoded["username"] == payload["username"]
    assert "exp" in decoded
    assert "iat" in decoded


def test_verify_token():
    payload = {"username": "john_doe"}
    token = Auth.generate_token(payload)
    decoded_payload = Auth.verify_token(token)
    assert decoded_payload is not None
    assert isinstance(decoded_payload, dict)
    assert len(decoded_payload) == 3
    assert decoded_payload["username"] == payload["username"]
    assert isinstance(decoded_payload["exp"], int)
    assert isinstance(decoded_payload["iat"], int)


def test_verify_token_expired():
    payload = {"username": "john_doe"}
    token = Auth.generate_token(payload, expiration_hours=-1)
    with pytest.raises(ValueError) as e:
        Auth.verify_token(token)
    assert str(e.value) == "Token has expired. Please log in again."


def test_verify_token_invalid():
    payload = {"username": "john_doe"}
    token = Auth.generate_token(payload)
    token = token + "invalid"
    with pytest.raises(ValueError) as e:
        Auth.verify_token(token)
    assert str(e.value) == "Invalid token. Please log in again."


@patch("funnel.logging_helper.get_user_from_file")
def test_authenticate_user_bearer(mock_get_user):
    mock_get_user.return_value = {"username": "john_doe"}

    payload = {"username": "john_doe"}
    token = Auth.generate_token(payload, expiration_hours=1)

    user = Auth.authenticate_user_bearer(token, "users.json")
    assert user["username"] == payload["username"]


@patch("funnel.logging_helper.get_user_from_file")
def test_authenticate_user_bearer_user_not_found(mock_get_user):
    mock_get_user.return_value = None

    payload = {"username": "unknown_user"}
    token = Auth.generate_token(payload, expiration_hours=1)

    with pytest.raises(ValueError) as e:
        Auth.authenticate_user_bearer(token, "users.json")
    assert str(e.value) == "User not found"


@patch("funnel.logging_helper.get_user_from_file")
def test_authenticate_user_basic(mock_get_user):
    mock_get_user.retun_value = {
        "username": "john_doe", "password": "admin123"
    }

    auth_header = "Basic " + base64.b64encode(
        b"john_doe:admin123").decode("utf-8")
    user = Auth.authenticate_user_basic(auth_header, "users.json")
    assert user["username"] == "john_doe"


@patch("funnel.logging_helper.get_user_from_file")
def test_authenticate_user_basic_wrong_credentials(mock_get_user):
    mock_get_user.retun_value = {
        "username": "john_doe", "password": "admin123"
    }

    auth_header = "Basic " + base64.b64encode(
        b"john_doe:wrong_pass").decode("utf-8")
    with pytest.raises(ValueError) as e:
        Auth.authenticate_user_basic(auth_header, "users.json")
    assert str(e.value) == "Invalid Basic Auth header: Invalid credentials"


@patch("funnel.logging_helper.get_user_from_file")
def test_authenticate_user_basic_user_not_found(mock_get_user):
    mock_get_user.retun_value = {
        "username": "john_doe", "password": "admin123"
    }

    auth_header = "Basic " + base64.b64encode(
        b"wrong_user:wrong_pass").decode("utf-8")
    with pytest.raises(ValueError) as e:
        Auth.authenticate_user_basic(auth_header, "users.json")
    assert str(e.value) == "Invalid Basic Auth header: User not found"
