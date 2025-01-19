"""User source module."""

import json
from abc import ABC, abstractmethod
from typing import Optional


class UserSource(ABC):
    """Abstract base class for user sources."""

    @abstractmethod
    def get_user(self, username: str) -> Optional[dict]:
        """Get user data. Must be implemented by subclasses."""
        raise NotImplementedError("get_user method not implemented")


class JsonUserSource(UserSource):
    """User source that reads user data from a JSON file.

    Args:
        file_path (str): Path to the JSON file.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_user(self, username: str) -> Optional[dict]:
        """Get user data from a JSON file.

        Args:
            username (str): Username to search for.

        Raises:
            FileNotFoundError: JSON file not found.
            ValueError: Invalid JSON format in the file.
            ValueError: Invalid data format in the file.
            ValueError: Invalid user format in the file.

        Returns:
            Optional[dict]: User data if found, None otherwise.
        """
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {self.file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON format in file {self.file_path}: {e}"
            )

        users = data.get("users", [])
        if not isinstance(users, list):
            raise ValueError(
                f"Invalid data format: 'users' should be a list in file{
                    self.file_path}"
            )


        for user in users:
            if not isinstance(user, dict) or "username" not in user:
                raise ValueError(
                    f"Invalid user format in file {self.file_path}: {user}"
                )

            if user["username"] == username:
                return user
        return None

