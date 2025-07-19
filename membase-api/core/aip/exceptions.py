"""AIP-specific exceptions."""


class AIPException(Exception):
    """Base exception for AIP-related errors."""
    pass


class AgentNotFoundError(AIPException):
    """Raised when an agent is not found."""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        super().__init__(f"Agent '{agent_id}' not found or not active")


class AgentTimeoutError(AIPException):
    """Raised when agent operation times out."""
    def __init__(self, agent_id: str, operation: str, timeout: int):
        self.agent_id = agent_id
        self.operation = operation
        self.timeout = timeout
        super().__init__(f"Agent '{agent_id}' operation '{operation}' timed out after {timeout} seconds")


class RouterInitializationError(AIPException):
    """Raised when router fails to initialize."""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Router initialization failed: {reason}")