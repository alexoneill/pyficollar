"""Compatibility shim for pyficollar."""

from __future__ import annotations
import warnings

from pyficollar import (
    API_BASE_URL,
    ActivitySummary,
    Device,
    FiAuthError,
    FiClient,
    FiDeviceError,
    FiError,
    FiGraphQLError,
    FiNetworkError,
    FiTransport,
    Household,
    LedColor,
    LedColorEnum,
    Location,
    OPERATIONS,
    Pet,
    PetLiveState,
    Place,
    Position,
    RestSummary,
    User,
    Walk,
    __all__,
    __version__,
)

warnings.warn(
    "Importing from 'fi' is deprecated. Please import from 'pyficollar' instead.",
    DeprecationWarning,
    stacklevel=2,
)
