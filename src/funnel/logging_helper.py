import json


def load_users(file_path: str) -> list:
    with open(file_path, "r") as file:
        data = json.load(file)
    return data["users"]


def get_user_from_file(username: str, file_path: str) -> dict:
    users = load_users(file_path)
    for user in users:
        if user["username"] == username:
            return user
    raise ValueError("User not found")
