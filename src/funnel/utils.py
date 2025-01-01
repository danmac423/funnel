import os
import yaml

from mimetypes import guess_type

from funnel.response import Response
from funnel.exceptions import NotFoundError


def directory_handler_factory(directory: str):
    """
    Create a handler for serving files and directories.

    Args:
        directory (str): The directory or file to serve.

    Returns:
        Callable: A handler function.
    """

    def handler(request):
        normalized_path = os.path.normpath(directory)

        if os.path.isdir(normalized_path):
            entries = os.listdir(normalized_path)
            links = []
            for entry in sorted(entries):
                entry_path = os.path.normpath(
                    os.path.join(request.path, entry)
                )
                links.append(f'<li><a href="{entry_path}">{entry}</a></li>')
            html_content = (
                f"<html><body><h1>Index of {normalized_path}</h1>"
                f"<ul>{''.join(links)}</ul></body></html>"
            )
            return Response.html(
                status_code=200, reason="OK", html_content=html_content
            )

        elif os.path.isfile(normalized_path):
            try:
                with open(normalized_path, "rb") as file:
                    content = file.read()

                content_type, _ = guess_type(normalized_path)
                content_type = "application/octet-stream"

                return Response(
                    status_code=200,
                    reason="OK",
                    headers={"Content-Type": content_type},
                    body=content,
                )
            except Exception as e:
                raise NotFoundError(
                    f"Error reading file: {normalized_path}"
                ) from e

        else:
            raise NotFoundError(
                f"File or directory not found: {normalized_path}"
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
    except IsADirectoryError:
        raise IsADirectoryError(f"{file_path} is a directory")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}")
