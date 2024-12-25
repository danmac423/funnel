import jwt
import datetime
import base64
from functools import wraps
from funnel.exceptions import UnauthorizedError
from funnel.request import Request
from typing import Callable
from funnel.logging_helper import get_user_from_file


class Auth:
    SECRET_KEY = "abc123"

    @staticmethod
    def generate_token(payload: dict, expiration_hours: int = 1) -> str:
        """Generates a JWT token with the given payload and expiration time.

        Args:
            payload (dict): User data (username) to be stored in the token.
            expiration_hours (int, optional): Expiration time in hours. Defaults to 1.

        Returns:
            str: JWT token
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        payload["exp"] = now + datetime.timedelta(hours=expiration_hours)
        payload["iat"] = now
        return jwt.encode(payload, Auth.SECRET_KEY, algorithm="HS256")

    @staticmethod
    def authenticate_user_bearer(token: str, user_file: str) -> dict:
        """Authenticate a user using a Bearer token.

        Args:
            token (str): JWT token
            user_file (str): Path to the file containing user data

        Raises:
            ValueError: User not found

        Returns:
            dict: User data
        """
        payload = Auth.verify_token(token)

        username = payload.get("username")
        user = get_user_from_file(username, user_file)  # change

        if not user:
            raise ValueError("User not found")

        return user

    @staticmethod
    def authenticate_user_basic(auth_header: str, user_file: str) -> dict:
        """Authenticate a user using Basic Auth.

        Args:
            auth_header (str): Authorization header
            user_file (str): Path to the file containing user data

        Returns:
            dict: User data
        """
        try:
            encoded_credentials = auth_header.split(" ")[1]
            credentials = base64.b64decode(encoded_credentials).decode("utf-8")
            username, password = credentials.split(":")

            user = get_user_from_file(username, user_file)
            if not user or password != user.get("password"):
                raise ValueError("Invalid credentials")

            return user
        except Exception as e:
            raise ValueError(f"Invalid Basic Auth header: {e}")

    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify the given JWT token.

        Args:
            token (str): JWT token

        Returns:
            dict: Decoded payload
        """
        try:
            payload = jwt.decode(token, Auth.SECRET_KEY, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired. Please log in again.")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token. Please log in again.")

    @staticmethod
    def authenticate(user_file: str, type: str = "Bearer"):
        """Decorator to authenticate users using Bearer or Basic Auth.

        Args:
            user_file (str): Path to the file containing user data
            type (str, optional): Type of authentication. Defaults to "Bearer".
        """

        def decorator(func: Callable):
            @wraps(func)
            def wrapper(request: Request, *args, **kwargs):
                auth_header = request.headers.get("Authorization")
                if not auth_header:
                    raise UnauthorizedError("Unauthorized: Missing or invalid token")

                if type == "Bearer":
                    if not auth_header.startswith("Bearer "):
                        raise UnauthorizedError(
                            "Unauthorized: Missing or invalid token"
                        )

                    token = auth_header.split(" ")[1]

                    if not token:
                        raise UnauthorizedError(
                            "Unauthorized: Missing or invalid token"
                        )
                    try:
                        user = Auth.authenticate_user_bearer(token, user_file)
                        request.user = user
                    except ValueError as e:
                        raise UnauthorizedError(f"Authorization failed: {e}")

                elif type == "Basic":
                    if not auth_header.startswith("Basic "):
                        raise UnauthorizedError(
                            "Unauthorized: Missing Basic Auth header"
                        )

                    try:
                        user = Auth.authenticate_user_basic(auth_header, user_file)
                        request.user = user
                    except ValueError as e:
                        raise UnauthorizedError(f"Basic authentication failed: {e}")

                return func(request, *args, **kwargs)

            return wrapper

        return decorator
