from abc import ABC, abstractmethod
import json
from typing import Optional

class UserSource(ABC):

    @abstractmethod
    def get_user(self, username: str) -> Optional[dict]:
        pass


class JsonUserSource(UserSource):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_user(self, username: str) -> Optional[dict]:
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

