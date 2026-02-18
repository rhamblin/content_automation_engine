class AuthenticationError(Exception):
    """Raised when authentication fails (invalid/missing/expired token)."""

    def __init__(self, detail: str = "Authentication required"):
        self.detail = detail
        super().__init__(self.detail)


class AuthorizationError(Exception):
    """Raised when an authenticated user lacks permission for the action."""

    def __init__(self, detail: str = "Insufficient permissions"):
        self.detail = detail
        super().__init__(self.detail)
