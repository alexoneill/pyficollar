"""Exceptions for the TryFi Python API client."""

from __future__ import annotations
from typing import Any


class FiError(Exception):
    """Base exception for all TryFi client errors."""


class FiAuthError(FiError):
    """Raised when authentication fails or session expires."""


class FiGraphQLError(FiError):
    """Raised when a GraphQL request fails or contains GraphQL errors."""

    def __init__(self, message: str, errors: list[dict[str, Any]] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []


class FiNetworkError(FiError):
    """Raised when a network transport or HTTP communication error occurs."""


class FiDeviceError(FiError):
    """Raised when an operation on a Fi collar device fails."""
