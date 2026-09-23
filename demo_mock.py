#!/usr/bin/env python3
"""Offline Demonstration of the TryFi Python Client.

Uses mock responses extracted from the Charles Proxy session log (request_log.chlsj)
to demonstrate all key operations of the library without requiring live credentials.
"""

from __future__ import annotations
from typing import Any
from fi import FiClient, FiTransport
from tests.fixtures import (
    AllUserPets,
    CurrentUserPetsAndDevices,
    EnableOrExtendQuickReportMode,
    GetDevice,
    GetPetPlaces,
    HomescreenActivityInfo,
    HomescreenPetRestInfo,
    LastWalkWithMap,
    LOGIN_RESPONSE,
    PetLiveState,
    UpdateDeviceOperationParams,
    UserPetProfile,
)


class DemoMockTransport(FiTransport):
    def request(self, method: str, endpoint: str, data: Any = None, headers: Any = None) -> Any:
        if "login" in endpoint:
            return LOGIN_RESPONSE
        if "checkemail" in endpoint:
            return {"exists": True}
        return {}

    def execute_graphql(self, query: str, operation_name: str | None = None, variables: Any = None, op_type: Any = None) -> Any:
        mapping = {
            "CurrentUserPetsAndDevices": CurrentUserPetsAndDevices,
            "AllUserPets": AllUserPets,
            "UserPetProfile": UserPetProfile,
            "PetLiveState": PetLiveState,
            "HomescreenActivityInfo": HomescreenActivityInfo,
            "HomescreenPetRestInfo": HomescreenPetRestInfo,
            "LastWalkWithMap": LastWalkWithMap,
            "GetPetPlaces": GetPetPlaces,
            "GetDevice": GetDevice,
            "UpdateDeviceOperationParams": UpdateDeviceOperationParams,
            "EnableOrExtendQuickReportMode": EnableOrExtendQuickReportMode,
        }
        return mapping.get(operation_name, {"data": {}})


def main() -> None:
    print("==================================================")
    print("      TryFi Collar Python API - Demo Walkthrough   ")
    print("==================================================\n")

    # 1. Initialize Client
    client = FiClient(transport=DemoMockTransport())

    # 2. Authenticate
    print("1. Authenticating...")
    login_info = client.login("alex@example.com", "secret_password", save_session=False)
    print(f"   -> Authenticated as User ID: {client.current_user_id}")
    print(f"   -> Session ID: {login_info['sessionId'][:12]}...")

    # 3. Retrieve Pets
    print("\n2. Fetching user's pets...")
    pets = client.get_pets()
    for pet in pets:
        print(f"   🐶 Pet: {pet.name} (ID: {pet.id})")
        print(f"      Breed: {pet.breed_name}")
        print(f"      Weight: {pet.weight_lbs} lbs")
        print(f"      Handle: @{pet.fi_handle}")
        print(f"      Photo: {pet.photo_url}")
        if pet.device:
            print(f"      Collar Module: {pet.device.module_id} (Battery: {pet.device.battery_percent}%)")

    pet_id = pets[0].id
    module_id = pets[0].device.module_id if pets[0].device else "FC35H674757"

    # 4. Fetch Real-time Live State
    print(f"\n3. Fetching Real-time Live State for {pets[0].name}...")
    live = client.get_pet_live_state(pet_id)
    print(f"   -> Online: {live.is_online} (State: {live.online_state})")
    print(f"   -> Battery: {live.battery_percent}% (Charging: {live.has_power_supply})")
    print(f"   -> Location: {live.location_name}")
    print(f"   -> Coordinates: {live.latitude}, {live.longitude}")
    print(f"   -> At Home: {live.is_at_home}")
    print(f"   -> Lost Dog Mode: {live.lost_mode}")

    # 5. Fetch Activity & Sleep
    print(f"\n4. Fetching Daily Activity & Rest for {pets[0].name}...")
    act = client.get_pet_activity(pet_id)
    rest = client.get_pet_rest(pet_id)
    print(f"   -> Daily Steps: {act.total_steps:,} / {act.step_goal:,} ({act.goal_percent}% of goal)")
    print(f"   -> Sleep Duration: {rest.sleep_hours} hrs, Nap: {rest.nap_hours} hrs")

    # 6. Fetch Recent Walk
    print(f"\n5. Fetching Most Recent Walk...")
    walk = client.get_last_walk(pet_id)
    if walk:
        print(f"   -> Walk ID: {walk.id}")
        print(f"   -> Steps: {walk.total_steps:,}")
        print(f"   -> Distance: {walk.distance_km} km ({walk.distance_miles} miles)")
        print(f"   -> Walker: {walk.present_user_name}")
        print(f"   -> GPS Track points: {len(walk.path)} points")

    # 7. Collar Device Controls (LED)
    print(f"\n6. Controlling Collar Hardware (Module: {module_id})...")
    device = client.set_led(module_id, led_enabled=True)
    print(f"   -> LED Light Toggled: {'ON' if device.led_enabled else 'OFF'}")
    if device.led_color:
        print(f"   -> Current LED Color: {device.led_color.name} (#{device.led_color.hex_code})")

    # 8. Activate Lost Dog Mode
    print(f"\n7. Testing Lost Dog Mode (Quick Report Mode)...")
    ttl = client.enable_lost_dog_mode(pet_id)
    print(f"   -> Lost Dog Mode activated for {ttl} seconds!")

    print("\n==================================================")
    print("      Demo completed successfully!                ")
    print("==================================================")


if __name__ == "__main__":
    main()
