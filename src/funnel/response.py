import json

from typing import Optional, Any


class Response:
    def __init__(
        self,
        status_code: int = 200,
        reason: str = "OK",
        headers: Optional[dict[str, str]] = None,
        body: Optional[Any] = None,
    ):
        self.status_code = status_code
        self.reason = reason
        self.headers = headers or {}
        self.body = body or {}

    def set_header(self, key: str, value: str) -> None:
        self.headers[key] = value

    def to_http(self) -> str:
        if isinstance(self.body, dict):
            body_content = json.dumps(self.body)
            self.set_header("Content-Type", "application/json")
        elif isinstance(self.body, str):
            body_content = self.body
        else:
            body_content = ""

        self.set_header("Content-Length", str(len(body_content)))

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
        data: Optional[dict] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> "Response":
        return cls(status_code, reason, headers, data)

    @classmethod
    def html(
        cls,
        status_code: int,
        reason: str,
        html_content: str,
        headers: Optional[dict[str, str]] = None,
    ) -> "Response":
        headers = headers or {}
        headers["Content-Type"] = "text/html"
        return cls(status_code, reason, headers, html_content)
