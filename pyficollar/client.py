"""High-level Pythonic client for the TryFi (Fi collar) API."""

from __future__ import annotations
from pathlib import Path
from typing import Any

from .const import CHECK_EMAIL_ENDPOINT, CURRENT_USER_ENDPOINT, LOGIN_ENDPOINT
from .exceptions import FiAuthError, FiError
from .models import (
    ActivitySummary,
    Device,
    Pet,
    PetLiveState,
    Place,
    RestSummary,
    User,
    Walk,
)
from .queries import OPERATION_TYPES, OPERATIONS
from .transport import FiTransport


class FiClient:
    """Client for interacting with TryFi smart collar API."""

    def __init__(
        self,
        session_id: str | None = None,
        api_key: str | None = None,
        session_file: str | Path | None = None,
        transport: FiTransport | None = None,
    ) -> None:
        self.session_file = Path(session_file).expanduser().resolve() if session_file else None
        self.transport = transport or FiTransport(api_key=api_key)

        if self.session_file and self.session_file.is_file():
            self.load_session(self.session_file)
        elif session_id:
            self.transport.set_session(session_id=session_id)

    @property
    def is_authenticated(self) -> bool:
        """Check whether the client currently holds an active session."""
        return self.transport.is_authenticated

    @property
    def current_user_id(self) -> str | None:
        """Return the current logged in user ID."""
        return self.transport.user_id

    def check_email(self, email: str) -> bool:
        """Check if an email address is registered with TryFi."""
        endpoint = f"{CHECK_EMAIL_ENDPOINT}?email={email.strip().lower()}"
        res = self.transport.request("GET", endpoint)
        return bool(res.get("exists", False))

    def login(
        self,
        email: str,
        password: str,
        sync_locale_to_account: bool = True,
        save_session: bool = True,
    ) -> dict[str, Any]:
        """Authenticate with email and password and store session credentials."""
        payload = {
            "email": email.strip(),
            "password": password,
            "sync_locale_to_account": sync_locale_to_account,
        }
        res = self.transport.request("POST", LOGIN_ENDPOINT, data=payload)

        session_id = res.get("sessionId")
        user_id = res.get("userId")
        res_email = res.get("email") or email

        if not session_id:
            raise FiAuthError(f"Login failed: missing sessionId in response ({res})")

        self.transport.set_session(session_id=session_id, user_id=user_id, email=res_email)

        if save_session and self.session_file:
            self.save_session(self.session_file)

        return res

    def save_session(self, filepath: str | Path | None = None) -> None:
        """Save active session credentials to disk."""
        target_path = Path(filepath).expanduser().resolve() if filepath else self.session_file
        if not target_path:
            raise ValueError("No session file path specified to save session.")
        self.transport.save_session(target_path)
        self.session_file = target_path

    def load_session(self, filepath: str | Path) -> bool:
        """Load session credentials from disk."""
        path = Path(filepath).expanduser().resolve()
        success = self.transport.load_session(path)
        if success:
            self.session_file = path
        return success

    def execute_graphql(
        self,
        operation_name: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute one of the captured GraphQL operations by name."""
        query = OPERATIONS.get(operation_name)
        if not query:
            raise ValueError(f"Unknown operation '{operation_name}'. Available: {list(OPERATIONS.keys())}")
        op_type = OPERATION_TYPES.get(operation_name, "query")
        return self.transport.execute_graphql(
            query=query,
            operation_name=operation_name,
            variables=variables,
            op_type=op_type,
        )

    def execute_raw_graphql(
        self,
        query: str,
        operation_name: str | None = None,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an arbitrary raw GraphQL query string."""
        return self.transport.execute_graphql(
            query=query,
            operation_name=operation_name,
            variables=variables,
        )

    # -------------------------------------------------------------------------
    # High-level domain methods
    # -------------------------------------------------------------------------

    def get_current_user(self) -> User:
        """Fetch current user account details including households and pets."""
        res = self.execute_graphql("CurrentUserPetsAndDevices")
        current_user = res.get("data", {}).get("currentUser")
        if not current_user:
            raise FiError("No currentUser found in CurrentUserPetsAndDevices response")
        return User.from_dict(current_user)

    def get_pets(self) -> list[Pet]:
        """Fetch all pets linked to the user's households."""
        res = self.execute_graphql("AllUserPets")
        current_user = res.get("data", {}).get("currentUser") or {}
        user_households = current_user.get("userHouseholds") or []

        pets: list[Pet] = []
        for uh in user_households:
            hh = uh.get("household") or {}
            for p in hh.get("pets") or []:
                pets.append(Pet.from_dict(p))
        return pets

    def get_pet(self, pet_id: str) -> Pet:
        """Fetch profile for a specific pet."""
        res = self.execute_graphql("UserPetProfile", variables={"petId": pet_id})
        pet_data = res.get("data", {}).get("pet")
        if not pet_data:
            raise FiError(f"Pet with ID {pet_id} not found")
        return Pet.from_dict(pet_data)

    def get_pet_live_state(self, pet_id: str) -> PetLiveState:
        """Fetch real-time location, GPS, safe place, battery, and connection status."""
        res = self.execute_graphql("PetLiveState", variables={"petId": pet_id})
        live_data = res.get("data", {}).get("petLiveState")
        if not live_data:
            raise FiError(f"No live state returned for pet {pet_id}")
        return PetLiveState.from_dict(live_data, pet_id=pet_id)

    def get_pet_activity(self, pet_id: str) -> ActivitySummary:
        """Fetch today's step activity, goals, and streak."""
        res = self.execute_graphql("HomescreenActivityInfo", variables={"petId": pet_id})
        pet_data = res.get("data", {}).get("pet")
        if not pet_data:
            raise FiError(f"No activity info returned for pet {pet_id}")
        return ActivitySummary.from_dict(pet_data)

    def get_pet_rest(self, pet_id: str) -> RestSummary:
        """Fetch pet sleep, nap, and rest summary."""
        res = self.execute_graphql("HomescreenPetRestInfo", variables={"petId": pet_id})
        pet_data = res.get("data", {}).get("pet")
        if not pet_data:
            raise FiError(f"No rest info returned for pet {pet_id}")
        return RestSummary.from_dict(pet_data)

    def get_pet_places(self, pet_id: str) -> list[Place]:
        """Fetch safe places configured for the pet's household."""
        res = self.execute_graphql("GetPetPlaces", variables={"petId": pet_id})
        household = res.get("data", {}).get("pet", {}).get("household") or {}
        places_data = household.get("places") or []
        places = [Place.from_dict(p) for p in places_data]
        return [p for p in places if p is not None]

    def get_last_walk(
        self,
        pet_id: str,
        map_width: int = 382,
        map_height: int = 364,
        map_scale: int = 2,
        style: str = "ACTIVITY_CARD",
        color_scheme: str = "DARK",
    ) -> Walk | None:
        """Fetch the most recent walk activity including distance, steps, and route."""
        variables = {
            "petId": pet_id,
            "mapWidth": map_width,
            "mapHeight": map_height,
            "mapScale": map_scale,
            "style": style,
            "colorScheme": color_scheme,
            "minimumPadding": {"top": 56, "right": 16, "bottom": 56, "left": 126},
        }
        res = self.execute_graphql("LastWalkWithMap", variables=variables)
        activities = res.get("data", {}).get("pet", {}).get("activityFeed", {}).get("activities") or []
        if not activities:
            return None
        return Walk.from_dict(activities[0])

    def get_device(self, module_id: str) -> Device:
        """Fetch detailed hardware and operational information for a collar module."""
        res = self.execute_graphql("GetDevice", variables={"moduleId": module_id})
        device_data = res.get("data", {}).get("device")
        if not device_data:
            raise FiError(f"Device {module_id} not found")
        dev = Device.from_dict(device_data)
        if not dev:
            raise FiError(f"Could not parse device data for {module_id}")
        return dev

    def set_led(self, module_id: str, led_enabled: bool) -> Device:
        """Turn collar LED light on or off."""
        variables = {
            "input": {
                "moduleId": module_id,
                "ledEnabled": led_enabled,
            }
        }
        res = self.execute_graphql("UpdateDeviceOperationParams", variables=variables)
        updated = res.get("data", {}).get("updateDeviceOperationParams")
        if not updated:
            raise FiError(f"Failed to update LED state for module {module_id}")
        dev = Device.from_dict(updated)
        if not dev:
            raise FiError("Could not parse updated device data")
        return dev

    def set_lost_dog_mode(self, pet_id: str, enabled: bool) -> Device:
        """Turn collar Lost Dog Mode on (LOST_DOG) or off (NORMAL)."""
        mode = "LOST_DOG" if enabled else "NORMAL"
        variables = {
            "input": {
                "petId": pet_id,
                "mode": mode,
            }
        }
        res = self.execute_graphql("SetPetOperationParamsMode", variables=variables)
        pet_data = res.get("data", {}).get("setPetOperationParamsMode") or {}
        dev_data = pet_data.get("device")
        if not dev_data:
            raise FiError(f"Failed to set lost mode for pet {pet_id}")
        dev = Device.from_dict(dev_data)
        if not dev:
            raise FiError("Could not parse updated device data")
        return dev

    def enable_lost_dog_mode(self, pet_id: str) -> Device:
        """Turn collar Lost Dog Mode on (LOST_DOG)."""
        return self.set_lost_dog_mode(pet_id, True)

    def disable_lost_dog_mode(self, pet_id: str) -> Device:
        """Turn collar Lost Dog Mode off (set to NORMAL)."""
        return self.set_lost_dog_mode(pet_id, False)

    def extend_quick_report_mode(self, pet_id: str) -> int:
        """Extend Quick Report Mode TTL for maximum GPS update frequency."""
        res = self.execute_graphql("EnableOrExtendQuickReportMode", variables={"petId": pet_id})
        result = res.get("data", {}).get("enableOrExtendQuickReportModeForPet") or {}
        ttl = result.get("ttlSeconds", 120)
        return int(ttl)
