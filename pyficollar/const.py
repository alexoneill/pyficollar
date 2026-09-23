"""Constants and configuration for the TryFi API."""

from __future__ import annotations
from enum import Enum

API_BASE_URL: str = "https://api.tryfi.com"
GRAPHQL_ENDPOINT: str = f"{API_BASE_URL}/graphql"
LOGIN_ENDPOINT: str = f"{API_BASE_URL}/auth/login"
CHECK_EMAIL_ENDPOINT: str = f"{API_BASE_URL}/auth/checkemail"
CURRENT_USER_ENDPOINT: str = f"{API_BASE_URL}/auth/currentuser"

API_KEY: str = "3d5be34970274eebb103e5e9987e739e"
APOLLO_CLIENT_NAME: str = "com.barkinglabs.fi-apollo-ios"
APOLLO_CLIENT_VERSION: str = "3.142.0-20656"
DEFAULT_USER_AGENT: str = "Fi/20656 CFNetwork/3896.100.1.2.1 Darwin/27.0.0"
DEFAULT_LOCALE_REGION: str = "en_US"

DEFAULT_HEADERS: dict[str, str] = {
    "Accept": "*/*",
    "Content-Type": "application/json",
    "User-Agent": DEFAULT_USER_AGENT,
    "X-Api-Key": API_KEY,
    "apollographql-client-name": APOLLO_CLIENT_NAME,
    "apollographql-client-version": APOLLO_CLIENT_VERSION,
    "X-Locale-Region": DEFAULT_LOCALE_REGION,
}


class LedColorEnum(Enum):
    RED = (2, "ff4242", "Red")
    GREEN = (3, "3cba0f", "Green")
    BLUE = (4, "0071ff", "Blue")
    PURPLE = (5, "ff2fcc", "Purple")
    YELLOW = (6, "ffff01", "Yellow")
    CYAN = (7, "00ffff", "Cyan")
    WHITE = (8, "ffffff", "White")

    def __init__(self, code: int, hex_code: str, display_name: str) -> None:
        self.code = code
        self.hex_code = hex_code
        self.display_name = display_name

    @classmethod
    def from_code(cls, code: int) -> LedColorEnum | None:
        for item in cls:
            if item.code == code:
                return item
        return None
