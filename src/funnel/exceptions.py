from typing import Optional


class FunnelError(Exception):
    status_code = 500
    error_message = "An internal server error occurred."
    additional_data: Optional[dict] = None

    def to_json(self) -> dict:
        error_data = {
            "error": self.error_message,
            "status_code": self.status_code,
        }

        if self.additional_data:
            error_data.update(self.additional_data)

        return error_data


class BadRequestError(FunnelError):
    status_code = 400
    error_message = "Invalid request payload. Please check the data format."


class InvalidHostError(FunnelError):
    status_code = 400
    error_message = "Invalid host header. Please check the host and try again."


class MissingAuthorizationError(FunnelError):
    status_code = 400
    error_message = "Missing authorization header."


class UnauthorizedError(FunnelError):
    status_code = 401
    error_message = "Invalid credentials or token."


class ForbiddenError(FunnelError):
    status_code = 403
    error_message = "Access to the requested resource is forbidden."


class NotFoundError(FunnelError):
    status_code = 404
    error_message = "The requested resource was not found."


class MethodNotAllowedError(FunnelError):
    status_code = 405
    error_message = "Method not allowed."
