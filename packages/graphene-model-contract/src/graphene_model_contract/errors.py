"""Stable public failure codes; messages never include native traces or paths."""


class ContractError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)
