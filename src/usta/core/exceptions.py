class PortalCanceledError(RuntimeError):
    """Raised when the user cancels or rejects the XDG Desktop Portal screen selection dialog."""

    pass


class ScreenCaptureError(RuntimeError):
    """Capture cannot continue until the user retries or fixes the underlying problem."""


class ScreenCapturePermissionError(ScreenCaptureError):
    """The current application process does not have screen-recording access."""
