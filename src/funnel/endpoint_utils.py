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
