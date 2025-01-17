"""
Utility functions for Funnel.
"""

import os
from mimetypes import guess_type
from typing import Callable

import yaml

from funnel.exceptions import NotFoundError
from funnel.response import Response
from funnel.router import Router
from funnel.request import Request

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
            methods=["GET"],
            handler=handler,
        )

        router._add_route(
            path=base_path,
            methods=["GET"],
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

    def handler(request):
        """
        Dynamically serve files or directories.

        Args:
            request (Request): Incoming HTTP request.

        Returns:
            Response: HTTP response with file or directory content.
        """
        requested_path = resolve_requested_path(
            request.path, base_path, base_directory
        )

        if os.path.isdir(requested_path):
            return serve_directory(requested_path, request.path)

        if os.path.isfile(requested_path):
            return serve_file(requested_path)

        raise NotFoundError("File or directory not found.")

    return handler


def resolve_requested_path(
    request_path: str, base_path: str, base_directory: str
) -> str:
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
            f"<html><body><h1>Index of {request_path}</h1>"
            f"<ul>{''.join(links)}</ul></body></html>"
        )
        return Response.html(
            status_code=200, reason="OK", html_content=html_content
        )
    except Exception:
        raise NotFoundError(f"Error reading folder: {directory_path}")


def serve_file(file_path: str) -> Response:
    """
    Generate a response for serving a file.

    Args:
        file_path (str): The file to serve.

    Returns:
        Response: Response with the file content and headers.
    """
    try:
        with open(file_path, "rb") as file:
            content = file.read()

        content_type, _ = guess_type(file_path)
        if not content_type:
            content_type = "application/octet-stream"

        filename = os.path.basename(file_path)
        headers = {
            "Content-Type": content_type,
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(content)),
        }

        return Response(
            status_code=200, reason="OK", headers=headers, body=content
        )

    except Exception as e:
        raise NotFoundError(f"Error reading file: {file_path}") from e


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

def remove_file(server, request: Request):
    mounted_directories = server.get_mounted_directories()
    removed = False
    for dir in mounted_directories:
        dir = os.path.abspath(dir) + os.path.sep
        
        in_path = request.parsed_body["path"]
        requested_path = os.path.abspath(os.path.join(dir, in_path))
        
        if not requested_path.startswith(dir):
            continue

        if os.path.isfile(requested_path):
            os.remove(requested_path)
            removed = True
    if not removed:
        raise NotFoundError("File not found.")
