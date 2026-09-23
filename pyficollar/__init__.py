"""TryFi Python API Client.

Reconstructed from TryFi mobile app network traces.
"""

from __future__ import annotations

from .client import FiClient
from .const import (
    API_BASE_URL,
    LedColorEnum,
)
from .exceptions import (
    FiAuthError,
    FiDeviceError,
    FiError,
    FiGraphQLError,
    FiNetworkError,
)
from .models import (
    ActivitySummary,
    Device,
    Household,
    LedColor,
    Location,
    Pet,
    PetLiveState,
    Place,
    Position,
    RestSummary,
    User,
    Walk,
)
from .queries import OPERATIONS
from .transport import FiTransport
try:
    from ._version import __version__, __version_tuple__
except ImportError:
    try:
        from importlib.metadata import version, PackageNotFoundError

        __version__ = version("pyficollar")
        __version_tuple__ = (0, 0, 0, "unknown")
    except PackageNotFoundError:
        __version__ = "0.0.0.dev0"
        __version_tuple__ = (0, 0, 0, "dev0")

__all__ = [
    "FiClient",
    "FiTransport",
    "FiError",
    "FiAuthError",
    "FiGraphQLError",
    "FiNetworkError",
    "FiDeviceError",
    "Pet",
    "Device",
    "PetLiveState",
    "ActivitySummary",
    "RestSummary",
    "Walk",
    "Place",
    "Location",
    "Position",
    "User",
    "Household",
    "LedColor",
    "LedColorEnum",
    "OPERATIONS",
    "API_BASE_URL",
]
