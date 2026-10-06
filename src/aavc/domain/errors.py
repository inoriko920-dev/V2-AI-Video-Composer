class AAVCError(Exception):
    """Base application error."""


class ValidationError(AAVCError):
    pass


class ImportError(AAVCError):
    pass


class MediaProbeError(AAVCError):
    pass


class PersistenceError(AAVCError):
    pass


class ToolExecutionError(AAVCError):
    pass


class ProviderError(AAVCError):
    pass


class RenderError(AAVCError):
    pass


class ConfigurationError(AAVCError):
    pass


class SecurityError(AAVCError):
    pass
