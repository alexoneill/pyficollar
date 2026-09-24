"""Data models for TryFi API responses."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Position:
    latitude: float
    longitude: float

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Position | None:
        if not data:
            return None
        lat = data.get("latitude")
        lng = data.get("longitude")
        if lat is None or lng is None:
            return None
        return cls(latitude=float(lat), longitude=float(lng))


@dataclass
class Place:
    id: str
    name: str
    address: str | None = None
    position: Position | None = None
    radius: float | None = None
    city_state: str | None = None
    is_quick_zone: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Place | None:
        if not data:
            return None
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            address=data.get("address"),
            position=Position.from_dict(data.get("position")),
            radius=data.get("radius"),
            city_state=data.get("cityState"),
            is_quick_zone=bool(data.get("isQuickZone", False)),
        )


@dataclass
class Location:
    date: str | None = None
    error_radius: float | None = None
    position: Position | None = None
    place: Place | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Location | None:
        if not data:
            return None
        return cls(
            date=data.get("date"),
            error_radius=data.get("errorRadius"),
            position=Position.from_dict(data.get("position")),
            place=Place.from_dict(data.get("place")),
        )


@dataclass
class LedColor:
    led_color_code: int
    hex_code: str
    name: str

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> LedColor | None:
        if not data:
            return None
        return cls(
            led_color_code=int(data.get("ledColorCode", 0)),
            hex_code=data.get("hexCode", ""),
            name=data.get("name", ""),
        )


@dataclass
class Device:
    id: str
    module_id: str
    model_id: str | None = None
    model_name: str | None = None
    carrier: str | None = None
    battery_percent: int | None = None
    has_power_supply: bool | None = None
    mode: str | None = None
    led_enabled: bool = False
    led_off_at: str | None = None
    led_color: LedColor | None = None
    available_led_colors: list[LedColor] = field(default_factory=list)
    is_stale: bool = False
    connection_type: str | None = None
    charging_base_name: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Device | None:
        if not data:
            return None

        power_state = data.get("powerState") or {}
        operation_params = data.get("operationParams") or {}
        last_conn = data.get("lastConnectionState") or {}
        charging_base = last_conn.get("chargingBase") or {}

        available_colors = [
            LedColor.from_dict(c)
            for c in data.get("availableLedColors", [])
            if c is not None
        ]

        return cls(
            id=data.get("id", data.get("moduleId", "")),
            module_id=data.get("moduleId", data.get("id", "")),
            model_id=data.get("modelId"),
            model_name=data.get("model"),
            carrier=data.get("carrier"),
            battery_percent=power_state.get("batteryPercent"),
            has_power_supply=power_state.get("hasPowerSupply"),
            mode=operation_params.get("mode"),
            led_enabled=bool(operation_params.get("ledEnabled", False)),
            led_off_at=operation_params.get("ledOffAt"),
            led_color=LedColor.from_dict(data.get("ledColor")),
            available_led_colors=[c for c in available_colors if c is not None],
            is_stale=bool(last_conn.get("isStale", False)),
            connection_type=last_conn.get("__typename"),
            charging_base_name=charging_base.get("name"),
            raw_data=data,
        )


@dataclass
class PetLiveState:
    pet_id: str
    is_online: bool
    online_state: str | None = None
    is_stale: bool = False
    out_of_battery: bool = False
    lost_mode: str | None = None
    backhaul: str | None = None
    location: Location | None = None
    location_name: str | None = None
    at_safe_zone: Place | None = None
    last_report_timestamp: str | None = None
    next_update_expected_by: str | None = None
    battery_percent: int | None = None
    has_power_supply: bool | None = None
    led_color: LedColor | None = None
    available_led_colors: list[LedColor] = field(default_factory=list)
    module_id: str | None = None
    model_name: str | None = None
    is_walking: bool = False
    ongoing_steps: int = 0
    ongoing_distance_meters: float = 0.0
    raw_data: dict[str, Any] = field(default_factory=dict)

    @property
    def latitude(self) -> float | None:
        if self.location and self.location.position:
            return self.location.position.latitude
        return None

    @property
    def longitude(self) -> float | None:
        if self.location and self.location.position:
            return self.location.position.longitude
        return None

    @property
    def is_at_home(self) -> bool:
        if self.at_safe_zone and "home" in self.at_safe_zone.name.lower():
            return True
        if self.location_name and "home" in self.location_name.lower():
            return True
        return False

    @property
    def is_lost(self) -> bool:
        """Return True if pet is in Lost Dog Mode."""
        if not self.lost_mode:
            return False
        return self.lost_mode.upper() not in ("LDM_DISABLED", "DISABLED", "NONE", "FALSE", "OFF")

    @classmethod
    def from_dict(cls, data: dict[str, Any], pet_id: str = "") -> PetLiveState:
        device_summary = data.get("primaryDevice") or {}
        ongoing_act = data.get("ongoingActivity") or {}

        available_colors = [
            LedColor.from_dict(c)
            for c in device_summary.get("availableLedColors", [])
            if c is not None
        ]

        return cls(
            pet_id=pet_id,
            is_online=bool(data.get("isOnline", False)),
            online_state=data.get("onlineState"),
            is_stale=bool(data.get("isStale", False)),
            out_of_battery=bool(data.get("outOfBattery", False)),
            lost_mode=data.get("lostMode"),
            backhaul=data.get("backhaul"),
            location=Location.from_dict(data.get("location")),
            location_name=data.get("locationName"),
            at_safe_zone=Place.from_dict(data.get("atSafeZone")),
            last_report_timestamp=data.get("lastReportTimestamp"),
            next_update_expected_by=data.get("nextUpdateExpectedBy"),
            battery_percent=device_summary.get("batteryPercent"),
            has_power_supply=device_summary.get("hasPowerSupply"),
            led_color=LedColor.from_dict(device_summary.get("ledColor")),
            available_led_colors=[c for c in available_colors if c is not None],
            module_id=device_summary.get("moduleId"),
            model_name=device_summary.get("modelName"),
            is_walking=bool(ongoing_act.get("isWalking", False)),
            ongoing_steps=int(ongoing_act.get("steps", 0) or 0),
            ongoing_distance_meters=float(ongoing_act.get("distanceMeters", 0) or 0),
            raw_data=data,
        )


@dataclass
class ActivitySummary:
    total_steps: int
    step_goal: int
    strain_score: float | int | None = None
    strain_level: str | None = None
    streak_days: int = 0
    raw_data: dict[str, Any] = field(default_factory=dict)

    @property
    def goal_percent(self) -> float:
        if self.step_goal > 0:
            return round((self.total_steps / self.step_goal) * 100.0, 1)
        return 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ActivitySummary:
        feed = data.get("stepFeed") or {}
        summary = feed.get("stepSummary") or {}
        return cls(
            total_steps=int(summary.get("totalSteps", 0) or 0),
            step_goal=int(summary.get("stepGoal", 10000) or 10000),
            strain_score=summary.get("strainScore"),
            strain_level=summary.get("strainLevel"),
            streak_days=int(summary.get("streakDays", 0) or 0),
            raw_data=data,
        )


@dataclass
class RestSummary:
    has_sleep_data: bool
    sleep_seconds: int = 0
    nap_seconds: int = 0
    rest_seconds: int = 0
    raw_data: dict[str, Any] = field(default_factory=dict)

    @property
    def sleep_hours(self) -> float:
        return round(self.sleep_seconds / 3600.0, 2)

    @property
    def nap_hours(self) -> float:
        return round(self.nap_seconds / 3600.0, 2)

    @property
    def rest_hours(self) -> float:
        return round(self.rest_seconds / 3600.0, 2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RestSummary:
        feed = data.get("restFeed") or {}
        summary = feed.get("restSummary") or {}
        overnight = summary.get("overnightRestSummary") or {}
        return cls(
            has_sleep_data=bool(data.get("hasSleepData", False)),
            sleep_seconds=int(overnight.get("sleepSeconds", 0) or 0),
            nap_seconds=int(summary.get("napSecondsTotal", 0) or 0),
            rest_seconds=int(summary.get("restSecondsTotal", 0) or 0),
            raw_data=data,
        )


@dataclass
class Walk:
    id: str
    start: str
    end: str | None = None
    distance_meters: float = 0.0
    total_steps: int = 0
    present_user_name: str | None = None
    city_state: str | None = None
    map_url: str | None = None
    path: list[Position] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)

    @property
    def distance_miles(self) -> float:
        return round(self.distance_meters * 0.000621371, 2)

    @property
    def distance_km(self) -> float:
        return round(self.distance_meters / 1000.0, 2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Walk:
        map_path = data.get("mapPath") or {}
        raw_pts = map_path.get("path") or []
        pts = [Position.from_dict(p) for p in raw_pts]
        return cls(
            id=data.get("id", ""),
            start=data.get("start", ""),
            end=data.get("end"),
            distance_meters=float(data.get("distance", 0) or 0),
            total_steps=int(data.get("totalSteps", 0) or 0),
            present_user_name=data.get("presentUserString"),
            city_state=data.get("cityState"),
            map_url=data.get("mapUrl"),
            path=[p for p in pts if p is not None],
            raw_data=data,
        )


@dataclass
class Pet:
    id: str
    name: str
    gender: str | None = None
    species: str | None = None
    breed_name: str | None = None
    weight: float | None = None
    year_of_birth: int | None = None
    month_of_birth: int | None = None
    day_of_birth: int | None = None
    fi_handle: str | None = None
    photo_url: str | None = None
    home_city_state: str | None = None
    device: Device | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)

    @property
    def weight_lbs(self) -> float | None:
        if self.weight is not None:
            return round(self.weight * 2.20462, 1)
        return None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Pet:
        breed = data.get("breed") or {}
        photos = data.get("photos") or {}
        first_photo = photos.get("first") or {}
        image = first_photo.get("image") or {}
        photo_url = image.get("fullSize") or image.get("id")
        home_loc = data.get("homeLocation") or {}

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            gender=data.get("gender"),
            species=data.get("species"),
            breed_name=breed.get("name"),
            weight=data.get("weight"),
            year_of_birth=data.get("yearOfBirth"),
            month_of_birth=data.get("monthOfBirth"),
            day_of_birth=data.get("dayOfBirth"),
            fi_handle=data.get("fiHandle"),
            photo_url=photo_url,
            home_city_state=home_loc.get("cityState"),
            device=Device.from_dict(data.get("device")),
            raw_data=data,
        )


@dataclass
class Household:
    id: str
    name: str
    role: str | None = None
    pets: list[Pet] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any], role: str | None = None) -> Household:
        raw_pets = data.get("pets") or []
        pets = [Pet.from_dict(p) for p in raw_pets]
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            role=role,
            pets=pets,
        )


@dataclass
class User:
    id: str
    email: str
    first_name: str | None = None
    last_name: str | None = None
    households: list[Household] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)

    @property
    def all_pets(self) -> list[Pet]:
        pets: list[Pet] = []
        for h in self.households:
            pets.extend(h.pets)
        return pets

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> User:
        user_households = data.get("userHouseholds") or []
        households = []
        for uh in user_households:
            hh_data = uh.get("household")
            if hh_data:
                households.append(Household.from_dict(hh_data, role=uh.get("householdRole")))

        return cls(
            id=data.get("id", ""),
            email=data.get("email", ""),
            first_name=data.get("firstName"),
            last_name=data.get("lastName"),
            households=households,
            raw_data=data,
        )
