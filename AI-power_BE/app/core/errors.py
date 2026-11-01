class DomainError(Exception):
    """Base class for expected service-layer errors."""


class DuplicateResourceError(DomainError):
    pass


class ResourceNotFoundError(DomainError):
    pass


class InvalidInputError(DomainError):
    pass


class AuthenticationError(DomainError):
    pass


class DependencyUnavailableError(DomainError):
    pass


class AIAnalysisError(DomainError):
    pass


class InvalidAIResponseError(AIAnalysisError):
    pass


class AIServiceUnavailableError(AIAnalysisError):
    pass


class AIProviderRateLimitError(AIAnalysisError):
    pass


class AIProviderError(AIAnalysisError):
    pass
