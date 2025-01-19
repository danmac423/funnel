"""
Utility functions for Funnel.
"""

import json
import os
import re
import time
from mimetypes import guess_type
from typing import Callable

import yaml

from funnel.exceptions import BadRequestError, MethodNotAllowedError, NotFoundError
from funnel.request import Request
from funnel.response import Response
from funnel.router import Router


def mount_directories(router: Router, config: dict) -> None:
    """
    Mount directories as routes on the provided router.

    Args:
        router (Router): The router to configure.
        config (dict): The configuration containing mounted directories.
    """
    for mount in config.get("mounted_directories", []):
        base_path = mount.get("path")
        root_directory = mount.get("directory")

        handler = directory_handler_factory(root_directory, base_path)

        router._add_route(
            path=f"{base_path}/<path:subpath>",
            methods=["GET", "POST"],
            handler=handler,
        )

        router._add_route(
            path=base_path,
            methods=["GET", "POST"],
            handler=handler,
        )


def directory_handler_factory(base_directory: str, base_path: str) -> Callable:
    """
    Create a handler for serving files and directories dynamically.

    Args:
        base_directory (str): The base directory to serve.
        base_path (str): The base path to resolve URLs.

    Returns:
        Callable: A handler function.
    """
    if not os.path.isdir(base_directory):
        raise ValueError(f"Base directory not found: {base_directory}")

    base_directory = os.path.abspath(base_directory)

    def handler(request: Request):
        """
        Dynamically serve files or directories and handle JSON uploads.

        Args:
            request (Request): Incoming HTTP request.

        Returns:
            Response: HTTP response with file or directory content.
        """
        requested_path = resolve_requested_path(request.path, base_path, base_directory)

        if request.method == "GET":
            if os.path.isdir(requested_path):
                return serve_directory(requested_path, request.path)

            if os.path.isfile(requested_path):
                return serve_file(requested_path, request)

            raise NotFoundError("File or directory not found.")

        elif request.method == "POST":
            if os.path.isdir(requested_path):
                return save_json_file(request, requested_path)

            raise NotFoundError("Directory not found.")

        raise MethodNotAllowedError(f"Method {request.method} not supported.")

    return handler


def save_json_file(request: Request, directory_path: str) -> Response:
    """
    Save a JSON file to the specified directory.

    Args:
        request (Request): The HTTP request containing the JSON data.
        directory_path (str): The directory where the file should be saved.

    Returns:
        Response: A JSON response indicating success.

    Raises:
        BadRequestError: If the request is invalid or the directory is not writable.
    """

    if request.headers.get("Content-Type") != "application/json":
        raise BadRequestError("Only JSON files are allowed.")

    json_data = request.parsed_body
    if not isinstance(json_data, dict):
        raise BadRequestError("Invalid JSON data.")

    filename = request.query_params.get("filename")
    if not filename:
        filename = f"upload_{int(time.time())}.json"

    if not re.match(r"^[a-zA-Z0-9_\-\.]+\.json$", filename):
        raise BadRequestError("Invalid filename. Must be a valid JSON filename.")

    file_path = os.path.join(directory_path, filename)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(json_data, file, ensure_ascii=False, indent=4)

    return Response.json(
        status_code=201,
        reason="Created",
        json_data={"message": "File uploaded successfully", "path": file_path},
    )


def resolve_requested_path(request_path: str, base_path: str, base_directory: str) -> str:
    """
    Resolve the full path for the requested resource.

    Args:
        request_path (str): The path from the HTTP request.
        base_path (str): The base path defined in the configuration.
        base_directory (str): The base directory to resolve against.

    Returns:
        str: The resolved, normalized path.

    Raises:
        NotFoundError: If the resolved path is outside the base directory.
    """
    subpath = os.path.relpath(request_path, base_path).lstrip("/")
    requested_path = os.path.normpath(os.path.join(base_directory, subpath))

    if not requested_path.startswith(base_directory):
        raise NotFoundError("Path not found.")

    return requested_path


def serve_directory(directory_path: str, request_path: str) -> Response:
    """
    Generate a response for serving a directory listing.

    Args:
        directory_path (str): The directory to list.
        request_path (str): The original request path.

    Returns:
        Response: HTML response containing the directory listing.
    """
    try:
        entries = sorted(os.listdir(directory_path))
        links = [
            f"<li><a href='{os.path.join(request_path, entry)}'>{entry}</a></li>"  # noqa
            for entry in entries
        ]
        html_content = (
            f"<html><body><h1>Index of {request_path}</h1><ul>{''.join(links)}</ul></body></html>"
        )
        return Response.html(status_code=200, reason="OK", html_content=html_content)
    except Exception:
        raise NotFoundError(f"Error reading folder: {directory_path}")


def load_config(file_path: str) -> dict:
    """
    Load server configuration from a YAML file.

    Args:
        file_path (str): Path to the YAML configuration file.

    Returns:
        dict: Loaded configuration.
    """
    try:
        with open(file_path, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    except IsADirectoryError:
        raise IsADirectoryError(f"{file_path} is a directory")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}")


def serve_file(file_path: str, request: Request) -> Response:
    """
    Generate a response for serving a file with optional Range support.

    Args:
        file_path (str): The file to serve.
        request (Request): The HTTP request containing optional Range header.

    Returns:
        Response: Response with the requested file content or a range.
    """
    try:
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        range_header = request.headers.get("Range")
        if range_header:
            start, end = parse_range_header(range_header, file_size)

            content = read_file_range(file_path, start, end)
            headers = generate_range_headers(start, end, file_size, filename, content)

            return Response(
                status_code=206, reason="Partial Content", headers=headers, body=content
            )

        with open(file_path, "rb") as file:
            content = file.read()
        headers = generate_full_file_headers(filename, content)
        return Response(status_code=200, reason="OK", headers=headers, body=content)
    except FileNotFoundError:
        raise NotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise BadRequestError(f"Error reading file: {e}")


def parse_range_header(range_header: str, file_size: int) -> tuple[int, int]:
    """
    Parse and validate the Range header.

    Args:
        range_header (str): The Range header from the request.
        file_size (int): The total size of the file.

    Returns:
        tuple[int, int]: Start and end byte positions.

    Raises:
        BadRequestError: If the Range header is invalid or out of bounds.
    """
    range_match = re.match(r"bytes=(\d*)-(\d*)", range_header)
    if not range_match:
        raise BadRequestError("Invalid Range header format.")
    start, end = range_match.groups()
    start = int(start) if start else 0
    end = int(end) if end else file_size - 1

    if start >= file_size or start > end:
        raise BadRequestError("Invalid byte range.")
    return start, min(end, file_size - 1)


def read_file_range(file_path: str, start: int, end: int) -> bytes:
    """
    Read a specific byte range from a file.

    Args:
        file_path (str): Path to the file.
        start (int): Start byte position.
        end (int): End byte position.

    Returns:
        bytes: The content of the specified range.
    """
    with open(file_path, "rb") as file:
        file.seek(start)
        return file.read(end - start + 1)


def generate_range_headers(
    start: int, end: int, file_size: int, filename: str, content: bytes
) -> dict:
    """
    Generate HTTP headers for a ranged response.

    Args:
        start (int): Start byte position.
        end (int): End byte position.
        file_size (int): Total size of the file.
        filename (str): Name of the file.
        content (bytes): Content of the range.

    Returns:
        dict: HTTP headers.
    """
    return {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Length": str(len(content)),
        "Content-Type": guess_type(filename)[0] or "application/octet-stream",
    }


def generate_full_file_headers(filename: str, content: bytes) -> dict:
    """
    Generate HTTP headers for a full file response.

    Args:
        filename (str): Name of the file.
        content (bytes): Content of the file.

    Returns:
        dict: HTTP headers.
    """
    return {
        "Content-Type": guess_type(filename)[0] or "application/octet-stream",
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Length": str(len(content)),
    }