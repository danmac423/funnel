"""Module to handle authentication and authorization."""

import base64
import datetime
import os
from functools import wraps
from typing import Callable

import jwt
from dotenv import load_dotenv

from funnel.exceptions import BadRequestError, UnauthorizedError
from funnel.request import Request
from funnel.user_source import UserSource

load_dotenv()


class Auth:
    """Class to handle authentication and authorization."""

    SECRET_KEY = os.getenv("SECRET_KEY")

    def __init__(self):
        self.user_source = None

    def configure_user_source(self, source: UserSource):
        """Configure the user source for authentication.

        Args:
            source (UserSource): User source object
        """
        self.user_source = source

    @staticmethod
    def generate_token(payload: dict, expiration_hours: int = 1) -> str:
        """Generates a JWT token with the given payload and expiration time.

        Args:
            payload (dict): User data (username) to be stored in the token.
            expiration_hours (int, optional): Expiration time in hours.
                Defaults to 1.

        Returns:
            str: JWT token
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        payload["exp"] = now + datetime.timedelta(hours=expiration_hours)
        payload["iat"] = now
        return jwt.encode(payload, Auth.SECRET_KEY, algorithm="HS256")

    def authenticate_user_bearer(self, token: str):
        """Authenticate a user using a Bearer token.

        Args:
            token (str): JWT token

        Raises:
            ValueError: User not found
            AttributeError: User source not configured

        Returns:
            dict: User data
        """
        payload = Auth.decode_token(token)

        username = payload.get("username")

        if not self.user_source:
            raise AttributeError("User source not configured")

        user = self.user_source.get_user(username)

        if not user:
            raise ValueError("User not found")

    def authenticate_user_basic(self, encoded_credentials: str):
        """Authenticate a user using Basic Auth.

        Args:
            encoded_credentials (str): Base64 encoded credentials

        Raises:
            ValueError: Invalid credentials
            AttributeError: User source not configured

        Returns:
            dict: User data
        """
        try:
            credentials = base64.b64decode(encoded_credentials).decode("utf-8")
            username, password = credentials.split(":")
        except Exception as e:
            raise ValueError(f"Invalid credentials: {e}")

        if not self.user_source:
            raise AttributeError("User source not configured")

        user = self.user_source.get_user(username)
        if not user or password != user.get("password"):
            raise ValueError("Invalid credentials")

    @staticmethod
    def decode_token(token: str) -> dict:
        """Verify the given JWT token.

        Args:
            token (str): JWT token

        Raises:
            ValueError: Token has expired or is invalid

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

    def authenticate(self, type: str = "Bearer"):
        """Decorator to authenticate users using Bearer or Basic Auth.

        Args:
            type (str, optional): Type of authentication. Defaults to "Bearer".
        """

        def decorator(func: Callable):
            @wraps(func)
            def wrapper(request: Request, *args, **kwargs):
                """Wrapper function to authenticate users.

                Args:
                    request (Request): HTTP request object

                Returns:
                    Any: Response from the decorated function
                """
                if not self.user_source:
                    raise AttributeError("User source not configured")

                auth_header = request.headers.get("Authorization")
                if not auth_header:
                    raise BadRequestError("BadRequestError: Missing or invalid Auth header")

                if type == "Bearer":
                    if not auth_header.startswith("Bearer "):
                        raise BadRequestError(
                            "BadRequestError: Missing or invalid Bearer Auth header"
                        )

                    token = auth_header.split(" ")[1]

                    if not token:
                        raise UnauthorizedError("Unauthorized: Missing or invalid token")
                    try:
                        self.authenticate_user_bearer(token)
                    except ValueError as e:
                        raise UnauthorizedError(f"Authorization failed: {e}")

                elif type == "Basic":
                    if not auth_header.startswith("Basic "):
                        raise BadRequestError(
                            "BadRequestError: Missing or invalid Basic Auth header"
                        )

                    try:
                        encoded_credentials = auth_header.split(" ")[1]
                        self.authenticate_user_basic(encoded_credentials)
                    except ValueError as e:
                        raise UnauthorizedError(f"Authorization failed: {e}")

                return func(request, *args, **kwargs)

            return wrapper

        return decorator
