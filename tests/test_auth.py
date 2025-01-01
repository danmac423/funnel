import pytest
import jwt
import json
import base64
import datetime
from funnel.auth import Auth
from funnel.user_source import JsonUserSource
from funnel.exceptions import UnauthorizedError, BadRequestError

USER_DATA = {"users": [{"username": "test_user", "password": "test_pass"}]}

@pytest.fixture
def user_source(tmp_path):
    """Fixture to create a temporary JSON file with user data."""
    file_path = tmp_path / "users.json"
    file_path.write_text(json.dumps(USER_DATA))
    return JsonUserSource(file_path)


@pytest.fixture(autouse=True)
def mock_secret_key(mocker):
    """Automatically mock SECRET_KEY for all tests."""
    mocker.patch("funnel.auth.os.getenv", return_value="mocked_secret_key")


@pytest.fixture
def auth(user_source):
    """Fixture to create an Auth instance."""
    auth = Auth()
    auth.configure_user_source(user_source)
    return auth


def test_configure_user_source(auth, mocker):
    mock_source = mocker.MagicMock()
    auth.configure_user_source(mock_source)
    assert auth.user_source == mock_source


def test_generate_token(auth):
    payload = {"username": "test_user"}
    token = auth.generate_token(payload)
    decoded = jwt.decode(token, Auth.SECRET_KEY, algorithms=["HS256"])
    assert decoded["username"] == "test_user"
    assert "exp" in decoded
    assert "iat" in decoded


def test_decode_token(auth):
    payload = {
        "username": "test_user",
        "exp": datetime.datetime.now(datetime.timezone.utc) +
            datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, Auth.SECRET_KEY, algorithm="HS256")
    decoded = auth.decode_token(token)
    assert decoded["username"] == "test_user"


def test_decode_token_expired(auth):
    payload = {
        "username": "testuser",
        "exp": datetime.datetime.now(datetime.timezone.utc) -
            datetime.timedelta(hours=1)
        }
    token = jwt.encode(payload, Auth.SECRET_KEY, algorithm="HS256")
    with pytest.raises(
        ValueError, match="Token has expired. Please log in again."
    ):
        auth.decode_token(token)


def test_decode_token_invalid(auth):
    invalid_token = "invalid_token"
    with pytest.raises(
        ValueError, match="Invalid token. Please log in again."
    ):
        auth.decode_token(invalid_token)


def test_authenticate_user_bearer(auth):
    payload = {
        "username": "test_user",
        "exp": datetime.datetime.now(datetime.timezone.utc) +
            datetime.timedelta(hours=1)
        }
    token = jwt.encode(payload, Auth.SECRET_KEY, algorithm="HS256")
    auth.authenticate_user_bearer(token)


def test_authenticate_user_bearer_invalid(auth):
    token = jwt.encode({
        "username": "unknown_user"
        }, Auth.SECRET_KEY, algorithm="HS256")
    with pytest.raises(ValueError, match="User not found"):
        auth.authenticate_user_bearer(token)


def test_authenticate_user_bearer_no_source(auth):
    payload = {
        "username": "test_user",
        "exp": datetime.datetime.now(datetime.timezone.utc) +
            datetime.timedelta(hours=1)
        }
    token = jwt.encode(payload, Auth.SECRET_KEY, algorithm="HS256")
    auth.user_source = None
    with pytest.raises(AttributeError, match="User source not configured"):
        auth.authenticate_user_bearer(token)


def test_authenticate_user_basic(auth):
    credentials = base64.b64encode(b"test_user:test_pass").decode("utf-8")
    auth.authenticate_user_basic(credentials)


def test_authenticate_user_basic_invalid(auth):
    credentials = base64.b64encode(b"test_user:wrong_pass").decode("utf-8")
    with pytest.raises(ValueError, match="Invalid credentials"):
        auth.authenticate_user_basic(credentials)


def test_authenticate_user_basic_missing_colon():
    auth = Auth()

    encoded_credentials = base64.b64encode(b"usernamepassword").decode("utf-8")

    with pytest.raises(
        ValueError, match="Invalid credentials: not enough values to unpack"
    ):
        auth.authenticate_user_basic(encoded_credentials)


def test_authenticate_user_basic_no_source(auth):
    credentials = base64.b64encode(b"test_user:test_pass").decode("utf-8")
    auth.user_source = None
    with pytest.raises(AttributeError, match="User source not configured"):
        auth.authenticate_user_basic(credentials)


def test_authenticate_decorator_bearer(auth, mocker):
    request = mocker.MagicMock()
    token = jwt.encode({
        "username": "test_user"
    }, Auth.SECRET_KEY, algorithm="HS256")
    request.headers = {"Authorization": f"Bearer {token}"}

    @auth.authenticate("Bearer")
    def protected_route(req):
        return "Access granted"

    assert protected_route(request) == "Access granted"


def test_authenticate_decorator_bearer_invalid_header(auth, mocker):
    request = mocker.MagicMock()
    request.headers = {"Authorization": "Invalid token_example"}

    @auth.authenticate("Bearer")
    def protected_route(req):
       return "Access granted"

    with pytest.raises(
        BadRequestError,
        match="BadRequestError: Missing or invalid Bearer Auth header"
        ):
        protected_route(request)


def test_authenticate_decorator_bearer_missing_token(auth, mocker):
    request = mocker.MagicMock()
    request.headers = {"Authorization": "Bearer "}

    @auth.authenticate("Bearer")
    def protected_route(req):
        return "Access granted"

    with pytest.raises(
        UnauthorizedError, match="Unauthorized: Missing or invalid token"
        ):
        protected_route(request)


def test_authenticate_decorator_bearer_error(auth, mocker):
    request = mocker.MagicMock()
    request.headers = {"Authorization": "Bearer invalid_token"}

    mocker.patch.object(
        auth,
        "authenticate_user_bearer",
        side_effect=ValueError("Invalid user")
    )

    @auth.authenticate("Bearer")
    def protected_route(req):
        return "Access granted"

    with pytest.raises(
        UnauthorizedError, match="Authorization failed: Invalid user"
        ):
        protected_route(request)


def test_authenticate_decorator_basic(auth, mocker):
    request = mocker.MagicMock()
    credentials = base64.b64encode(b"test_user:test_pass").decode("utf-8")
    request.headers = {"Authorization": f"Basic {credentials}"}

    auth.user_source.get_user = mocker.MagicMock(
        return_value=USER_DATA["users"][0]
    )

    @auth.authenticate("Basic")
    def protected_route(req):
        return "Access granted"

    assert protected_route(request) == "Access granted"


def test_authenticate_decorator_basic_invalid_header(auth, mocker):
    request = mocker.MagicMock()
    request.headers = {"Authorization": "Invalid token_example"}

    @auth.authenticate("Basic")
    def protected_route(req):
       return "Access granted"

    with pytest.raises(
        BadRequestError,
        match="BadRequestError: Missing or invalid Basic Auth header"
    ):
        protected_route(request)


def test_authenticate_decorator_basic_error(auth, mocker):
    request = mocker.MagicMock()
    request.headers = {"Authorization": "Basic invalid_credentials"}

    mocker.patch.object(
        auth,
        "authenticate_user_basic",
        side_effect=ValueError("Invalid credentials")
    )

    @auth.authenticate("Basic")
    def protected_route(req):
        return "Access granted"

    with pytest.raises(
        UnauthorizedError, match="Authorization failed: Invalid credentials"
    ):
        protected_route(request)


def test_authenticate_decorator_no_header(auth, mocker):
    request = mocker.MagicMock()
    request.headers = {}

    @auth.authenticate("Bearer")
    def protected_route(req):
        return "Access granted"

    with pytest.raises(
        BadRequestError,
        match="BadRequestError: Missing or invalid Auth header"
    ):
        protected_route(request)


def test_authenticate_no_user_source(mocker):
    auth = Auth()

    request = mocker.MagicMock()
    request.headers = {"Authorization": "Bearer some_token"}

    @auth.authenticate("Bearer")
    def protected_route(req):
        return "Access granted"

    with pytest.raises(AttributeError, match="User source not configured"):
        protected_route(request)
