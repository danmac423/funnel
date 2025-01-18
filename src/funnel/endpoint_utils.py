import json
import os

from funnel.exceptions import BadRequestError, NotFoundError
from funnel.funnel import HTTPServer
from funnel.request import Request


def remove_file(server: HTTPServer, request: Request):
    mounted_directories = server.get_mounted_directories()
    removed = False

    if not isinstance(request.parsed_body, dict):
        raise BadRequestError("Body: Invalid request body (Not a dict).")

    in_path = request.parsed_body["path"]

    for dir in mounted_directories:
        dir = os.path.abspath(dir)
        if dir[-1] != os.path.sep:
            dir += os.path.sep
        requested_path = os.path.abspath(os.path.join(dir, in_path))

        if not requested_path.startswith(dir):
            continue

        if os.path.isfile(requested_path):
            os.remove(requested_path)
            removed = True
    if not removed:
        raise NotFoundError("File not found.")


def save_json(server: HTTPServer, request: Request) -> None:
    mounted_directories = server.get_mounted_directories()

    target_path_str = request.query_params.get("path")
    if not target_path_str:
        raise BadRequestError("Missing 'path' query parameter.")

    target_path = os.path.abspath(target_path_str)


    if not any(
        os.path.commonpath([target_path, os.path.abspath(d)]) == os.path.abspath(d)
        for d in mounted_directories
    ):
        raise BadRequestError("Target path is not within a mounted directory.")

    file_data = request.body
    if file_data is None:
        raise BadRequestError("Request body is empty.")

    try:
        json_data = json.loads(file_data)
    except json.JSONDecodeError as e:
        raise BadRequestError(f"Invalid JSON format: {e}")

    try:
        with open(target_path, "w", encoding="utf-8") as file:
            json.dump(json_data, file, indent=4)
    except Exception as e:
        raise BadRequestError(f"Failed to save file: {e}")