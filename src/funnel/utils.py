"""
Utility functions for Funnel.
"""

import os
import yaml

from mimetypes import guess_type

from funnel.response import Response
from funnel.exceptions import NotFoundError
from funnel.router import Router


def mount_directories(router: Router, config: dict):
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


def directory_handler_factory(base_directory: str, base_path: str):
    """
    Create a handler for serving files and directories dynamically.

    Args:
        base_directory (str): The base directory to serve.
        base_path (str): The base path to resolve URLs.

    Returns:
        Callable: A handler function.
    """
    base_directory = os.path.abspath(base_directory)

    def handler(request):
        """
        Dynamically serve files or directories.

        Args:
            request (Request): Incoming HTTP request.

        Returns:
            Response: HTTP response with file or directory content.
        """

        subpath = os.path.relpath(request.path, base_path).lstrip("/")
        requested_path = os.path.join(base_directory, subpath)
        requested_path = os.path.normpath(requested_path)

        if not requested_path.startswith(base_directory):
            raise NotFoundError("Path not found.")

        if os.path.isdir(requested_path):
            entries = os.listdir(requested_path)
            hrefs = [
                f'<a href="{os.path.join(request.path, entry)}">{entry}</a>'
                for entry in sorted(entries)
            ]
            links = [f"<li>{href}</li>" for href in hrefs]
            html_content = (
                f"<html><body><h1>Index of {request.path}</h1>"
                f"<ul>{''.join(links)}</ul></body></html>"
            )
            return Response.html(
                status_code=200, reason="OK", html_content=html_content
            )

        elif os.path.isfile(requested_path):
            try:
                with open(requested_path, "rb") as file:
                    content = file.read()
                content_type, _ = guess_type(requested_path)
                if not content_type:
                    content_type = "application/octet-stream"

                filename = os.path.basename(requested_path)
                content_disposition = f'attachment; filename="{filename}"'

                return Response(
                    status_code=200,
                    reason="OK",
                    headers={
                        "Content-Type": content_type,
                        "Content-Disposition": content_disposition,
                        "Content-Length": str(len(content)),
                    },
                    body=content,
                )
            except Exception as e:
                raise NotFoundError(
                    f"Error reading file: {requested_path}"
                ) from e

        raise NotFoundError("File or directory not found.")

    return handler


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
