"""Exception hierarchy shared across collectors, analyzers, and reporting."""


class LinuxOptError(Exception):
    """Base class for all linux_opt errors."""


class CollectionError(LinuxOptError):
    """Raised when a collector fails to gather data from the system."""

    def __init__(self, source: str, message: str):
        self.source = source
        super().__init__(f"[{source}] {message}")


class PermissionDeniedError(CollectionError):
    """Raised when a collector lacks permission to read a required source."""


class UnsupportedPlatformError(LinuxOptError):
    """Raised when a feature is invoked on a non-Linux or unsupported platform."""


class AnalysisError(LinuxOptError):
    """Raised when an analyzer cannot process collected data."""


class ReportGenerationError(LinuxOptError):
    """Raised when a report renderer fails to produce output."""
