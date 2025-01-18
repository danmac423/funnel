"""
This module provides a class to represent and parse an HTTP request.
"""

import json
import os
import urllib.parse
from typing import Optional

from funnel.exceptions import BadRequestError


class Request:
    """
    Represents a parsed HTTP request.

    Attributes:
        method (str): HTTP method (e.g., GET, POST).
        path (str): Requested path.
        protocol (str): HTTP protocol version.
        headers (Dict[str, str]): HTTP headers.
        query_params (Dict[str, str]): Parsed query parameters from the URL.
        body (Optional[str]): Raw body of the request.
        parsed_body (Optional[Union[Dict, str]]): Parsed body as JSON or
            form data.

    Methods:
        _parse_request_line: Parse the request line from the HTTP request.
        _parse_headers: Parse the headers from the HTTP request.
        _parse_query_params: Parse the query parameters from the URL.
        _parse_body: Parse the body from the HTTP request.
        _parse_body_content: Parse the body content as JSON or form
    """

    def __init__(self, raw_request: str):
        """
        Initialize and parse the HTTP request.

        Args:
            raw_request (str): The raw HTTP request string.
        """
        self.raw_request = raw_request
        self.method, self.path, self.protocol = self._parse_request_line()
        self.headers = self._parse_headers()
        self.query_params = self._parse_query_params()
        self.body = self._parse_body()
        self.parsed_body = self._parse_body_content()

    def _parse_request_line(self) -> tuple[str, str, str]:
        """
        Parse the request line from the HTTP request.

        Returns:
            tuple[str, str, str]: Method, path, and protocol.

        Raises:
            BadRequestError: If the request line is invalid.
        """
        lines = self.raw_request.split("\r\n")
        if not lines or len(lines[0].split(" ")) < 3:
            raise BadRequestError("Invalid request line.")
        method, path, protocol = lines[0].split(" ")

        normalized_path = os.path.normpath(path)
        return method, normalized_path, protocol

    def _parse_headers(self) -> dict[str, str]:
        """
        Parse the headers from the HTTP request.

        Returns:
            dict[str, str]: Parsed headers.

        Raises:
            BadRequestError: If the headers are invalid
        """

        lines = self.raw_request.split("\r\n")
        headers = {}
        for line in lines[1:]:
            if not line.strip():
                break
            if ":" not in line:
                raise BadRequestError("Invalid headers in request.")
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if not key or not value:
                raise BadRequestError("Header key or value cannot be empty.")

            if key in headers:
                raise BadRequestError(
                    f"Multiple headers with same key: {key}."
                )
            else:
                headers[key] = value

        if "Host" not in headers or not headers["Host"]:
            raise BadRequestError("Missing or empty Host header.")

        return headers

    def _parse_query_params(self) -> dict[str, str]:
        """
        Parse the query parameters from the URL.

        Returns:
            dict[str, str]: Parsed query parameters.

        Raises:
            BadRequestError: If the query parameters are invalid.
        """
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            return dict(
                urllib.parse.parse_qsl(parsed_url.query, strict_parsing=True)
            )
        except Exception as e:
            raise BadRequestError(f"Invalid query parameters: {e}.")

    def _parse_body(self) -> Optional[str]:
        """
        Parse the body from the HTTP request.

        Returns:
            Optional[str]: Raw body of the request.

        Raises:
            BadRequestError: If the body is invalid.
        """
        body_start = self.raw_request.find("\r\n\r\n")
        if body_start == -1:
            if self.method in {"POST"}:
                raise BadRequestError("Missing body separator in the request.")
            return None

        body = self.raw_request[body_start + 4 :].strip()

        content_length = self.headers.get("Content-Length")
        if content_length:
            try:
                expected_length = int(content_length)
                if len(body) != expected_length:
                    raise BadRequestError(
                        "Content-Length does not match body length."
                        + f"Expected {expected_length} but got {len(body)}."
                    )
            except ValueError:
                raise BadRequestError("Invalid Content-Length header.")

        if self.method in {"POST"} and not body:
            raise BadRequestError("Missing body content in request.")

        if self.method in {"GET", "DELETE"}:
            return body if body else None

        return body if body else None

    def _parse_body_content(self) -> Optional[dict | str]:
        """
        Parse the body content as JSON or form data.

        Returns:
            Optional[dict | str]: Parsed body content.

        Raises:
            BadRequestError: If the body content is invalid.
        """
        content_type = self.headers.get("Content-Type", "").lower()
        try:
            if content_type == "application/json" and self.body:
                return json.loads(self.body)
            elif (
                content_type == "application/x-www-form-urlencoded"
                and self.body
            ):
                return dict(
                    urllib.parse.parse_qsl(self.body, strict_parsing=True)
                )
            return self.body
        except json.JSONDecodeError as e:
            raise BadRequestError(f"Invalid JSON in request body: {str(e)}")
        except ValueError as e:
            raise BadRequestError(
                f"Invalid form data in request body: {str(e)}"
            )
