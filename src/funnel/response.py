"""
This module contains the Response class for the Funnel framework.
"""

import json

from typing import Optional


class Response:
    """
    This class represents a HTTP response.

    Attributes:
        status_code (int): HTTP status code
        reason (str): HTTP status reason
        headers (dict[str, str]): HTTP headers
        body (Any): HTTP response body

    Methods:
        set_header: Set a header
        to_http: Convert response to a HTTP response
        json: Create a JSON response
        html: Create a HTML response
    """

    def __init__(
        self,
        status_code: int = 200,
        reason: str = "OK",
        headers: Optional[dict[str, str]] = None,
        body: Optional[str | bytes] = None,
    ):
        self.status_code = status_code
        self.reason = reason
        self.headers = headers or {}
        self.body = body

    def set_header(self, key: str, value: str) -> None:
        """
        Set a header

        Args:
            key (str): Header key
            value (str): Header value
        """
        self.headers[key] = value

    def to_http(self) -> str:
        """
        Convert response to a HTTP response

        Returns:
            str: String representation of the HTTP response
        """
        self.set_header(
            "Content-Length", str(len(self.body) if self.body else 0)
        )

        body_content = (
            self.body.decode("utf-8")
            if isinstance(self.body, bytes)
            else self.body or ""
        )

        return (
            f"HTTP/1.1 {self.status_code} {self.reason}\r\n"
            + "\r\n".join(
                f"{key}: {value}" for key, value in self.headers.items()
            )
            + f"\r\n\r\n{body_content}"
        )

    @classmethod
    def json(
        cls,
        status_code: int,
        reason: str,
        json_data: dict,
        headers: Optional[dict[str, str]] = None,
    ) -> "Response":
        """
        Create a JSON response

        Args:
            status_code (int): HTTP status code
            reason (str): HTTP status reason
            data (dict): Data to be sent in the response.
            headers (Optional[dict[str, str]], optional): Headers to be sent
                in the response. Defaults to None.

        Returns:
            Response: JSON response object
        """
        headers = headers or {}
        headers["Content-Type"] = "application/json"

        json_content = json.dumps(json_data)
        return cls(status_code, reason, headers, json_content)

    @classmethod
    def html(
        cls,
        status_code: int,
        reason: str,
        html_content: str,
        headers: Optional[dict[str, str]] = None,
    ) -> "Response":
        """
        Create a HTML response

        Args:
            status_code (int): HTTP status code
            reason (str): HTTP status reason
            html_content (str): HTML content to be sent in the response
            headers (Optional[dict[str, str]], optional): Headers to be sent
                in the response. Defaults to None.

        Returns:
            Response: HTML response object
        """
        headers = headers or {}
        headers["Content-Type"] = "text/html"
        return cls(status_code, reason, headers, html_content)
