"""
This module contains custom exceptions for the Funnel framework.
"""

from typing import Optional

from funnel.response import Response


class FunnelError(Exception):
    """
    Base class for all custom exceptions in the Funnel framework.

    Attributes:
        status_code (int): HTTP status code
        error_reason (str): HTTP status reason
        error_message (str): Error message
        additional_data (dict[str, str]): Additional error data

    Methods:
        to_dict: Convert error to a dictionary
        to_http_response: Convert error to a HTTP response
    """

    status_code = 500
    error_reason = "Internal Server Error"
    error_message = "An internal server error occurred."
    additional_data: Optional[dict[str, str]] = None

    def __init__(
        self,
        message: Optional[str] = None,
        additional_data: Optional[dict] = None,
    ):
        if message:
            self.error_message = message
        if additional_data:
            if not self.additional_data:
                self.additional_data = {}
            self.additional_data.update(additional_data)

    def to_dict(self) -> dict:
        """
        Convert error to a dictionary

        Returns:
            dict: Dictionary representation of the error
        """
        error_data = {
            "error": self.error_message,
            "status_code": self.status_code,
        }

        if self.additional_data:
            error_data.update(self.additional_data)

        return error_data

    def to_http_response(self) -> Response:
        """
        Convert error to a HTTP response

        Returns:
            Response: HTTP response object
        """

        return Response.json(
            status_code=self.status_code,
            reason=self.error_reason,
            json_data=self.to_dict(),
        )


class BadRequestError(FunnelError):
    """
    Exception for bad request errors
    """

    status_code = 400
    error_reason = "Bad Request"
    error_message = "Invalid request format"


class UnauthorizedError(FunnelError):
    """
    Exception for unauthorized errors
    """

    status_code = 401
    error_reason = "Unauthorized"
    error_message = "Authentication required"


class ForbiddenError(FunnelError):
    """
    Exception for bad forbidden errors
    """

    status_code = 403
    error_reason = "Forbidden"
    error_message = "Access denied"


class NotFoundError(FunnelError):
    """
    Exception for bad not found errors
    """

    status_code = 404
    error_reason = "Not Found"
    error_message = "Resource not found"


class MethodNotAllowedError(FunnelError):
    """
    Exception for method not allowed errors
    """

    status_code = 405
    error_reason = "Method Not Allowed"
    error_message = "Method not allowed for this resource"


class RangeNotSatisfiable(FunnelError):
    """
    Exception for method not allowed errors
    """

    status_code = 416
    error_reason = "Range Not Satisfiable"
    error_message = "Requested range not satisfiable"
