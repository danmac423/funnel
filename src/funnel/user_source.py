from abc import ABC, abstractmethod
import json

class UserSource(ABC):

    @abstractmethod
    def get_user(self, username: str) -> dict:
        pass


class JsonUserSource(UserSource):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_user(self, username: str) -> dict:
        with open(self.file_path, "r") as f:
            users = json.load(f).get("users", [])
        for user in users:
            if user["username"] == username:
                return user

