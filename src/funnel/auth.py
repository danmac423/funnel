import jwt
import datetime
from functools import wraps
from funnel.exceptions import UnauthorizedError
from funnel.request import Request
from typing import Callable
from funnel.logging_helper import get_user_from_file


class Auth:
    SECRET_KEY = "abc123"

    @staticmethod
    def generate_token(payload: dict, expiration_hours: int = 1) -> str:
        payload["exp"] = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            hours=expiration_hours
        )
        payload["iat"] = datetime.datetime.now(datetime.UTC)
        return jwt.encode(payload, Auth.SECRET_KEY, algorithm="HS256")

    @staticmethod
    def authenticate_user(token: str, user_file: str):
        payload = Auth.verify_token(token)

        username = payload.get("username")
        user = get_user_from_file(username, user_file)

        if payload.get("role") != user.get("role") or payload.get(
            "password"
        ) != user.get("password"):
            raise ValueError("Invalid permissions")

        return user

    @staticmethod
    def verify_token(token: str) -> dict:
        try:
            payload = jwt.decode(token, Auth.SECRET_KEY, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired. Please log in again.")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token. Please log in again.")

    @staticmethod
    def verify_token_decorator(user_file: str):
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(request: Request, *args, **kwargs):
                auth_header = request.headers.get("Authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    raise UnauthorizedError("Unauthorized: Missing or invalid token")

                token = auth_header.split(" ")[1]

                if not token:
                    raise UnauthorizedError("Unauthorized: Missing or invalid token")

                token = auth_header.split(" ")[1]
                try:
                    user = Auth.authenticate_user(token, user_file)
                    request.user = user
                except ValueError as e:
                    raise UnauthorizedError(f"Authorization failed: {e}")

                return func(request, *args, **kwargs)

            return wrapper

        return decorator
