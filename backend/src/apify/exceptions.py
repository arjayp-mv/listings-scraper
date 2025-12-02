# =============================================================================
# Apify Domain - Custom Exceptions
# =============================================================================
# Purpose: Apify-specific error handling
# Public API: ApifyError, ApifyTimeoutError, ApifyRateLimitError
# =============================================================================


class ApifyError(Exception):
    """Base exception for Apify-related errors."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ApifyTimeoutError(ApifyError):
    """Actor run exceeded timeout."""
    pass


class ApifyRateLimitError(ApifyError):
    """API rate limit exceeded."""
    pass


class ApifyActorError(ApifyError):
    """Actor failed during execution."""
    pass
