import os
import yaml

from funnel.response import Response
from funnel.exceptions import NotFoundError


def directory_handler_factory(directory: str):
    """
    Create a handler for serving files from a directory.

    Args:
        directory (str): The directory to serve files from.

    Returns:
        Callable: A handler function.
    """

    def handler(request):
        requested_path = directory
        if os.path.isdir(requested_path):
            entries = os.listdir(requested_path)
            links = [
                f'<li><a href="{entry}">{entry}</a></li>'
                for entry in sorted(entries)
            ]
            html_content = (
                f"<html><body><h1>Index of {requested_path}</h1>"
                f"<ul>{''.join(links)}</ul></body></html>"
            )
            return Response.html(
                status_code=200, reason="OK", html_content=html_content
            )
        elif os.path.isfile(requested_path):
            with open(requested_path, "rb") as file:
                content = file.read()
            return Response(
                status_code=200,
                reason="OK",
                headers={"Content-Type": "application/octet-stream"},
                body=content,
            )
        else:
            raise NotFoundError(
                f"File or directory not found: {requested_path}"
            )

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
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}")
