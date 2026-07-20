from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception with a consistent error envelope."""

    def __init__(self, status_code: int, message: str, error_code: str = "APP_ERROR"):
        super().__init__(status_code=status_code, detail={"message": message, "error_code": error_code})


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(status.HTTP_404_NOT_FOUND, message, "NOT_FOUND")


class ConflictError(AppException):
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(status.HTTP_409_CONFLICT, message, "CONFLICT")


class ValidationAppError(AppException):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, message, "VALIDATION_ERROR")


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, message, "UNAUTHORIZED")


class ForbiddenError(AppException):
    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(status.HTTP_403_FORBIDDEN, message, "FORBIDDEN")


class BadRequestError(AppException):
    def __init__(self, message: str = "Bad request"):
        super().__init__(status.HTTP_400_BAD_REQUEST, message, "BAD_REQUEST")


class PaymentRequiredError(AppException):
    def __init__(self, message: str = "Payment required"):
        super().__init__(status.HTTP_402_PAYMENT_REQUIRED, message, "PAYMENT_REQUIRED")


class ConfigurationError(AppException):
    def __init__(self, message: str = "Server misconfiguration"):
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, message, "CONFIGURATION_ERROR")
