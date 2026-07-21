"""ShipGate error hierarchy with exit codes."""


class ShipGateError(Exception):
    """Base ShipGate error."""

    exit_code = 4
    title = "internal error"

    def __init__(
        self,
        message: str,
        *,
        hint: str | None = None,
        path: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint
        self.path = path

    def format(self) -> str:
        parts = [f"shipgate: {self.title}: {self.message}"]
        if self.path:
            parts.append(f"path: {self.path}")
        if self.hint:
            parts.append(f"hint: {self.hint}")
        return "\n".join(parts)


class UsageError(ShipGateError):
    exit_code = 2
    title = "usage error"


class ConfigError(ShipGateError):
    exit_code = 2
    title = "config error"


class CatalogError(ShipGateError):
    exit_code = 2
    title = "catalog error"


class PlanningError(ShipGateError):
    exit_code = 2
    title = "planning error"


class InstallError(ShipGateError):
    exit_code = 3
    title = "install error"


class ExecutionError(ShipGateError):
    exit_code = 3
    title = "execution error"


class NormalizationError(ShipGateError):
    exit_code = 4
    title = "normalization error"
