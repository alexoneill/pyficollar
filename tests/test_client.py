"""Tests for FiClient using mocked transport."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from typing import Any

from pyficollar.client import FiClient
from pyficollar.const import LOGIN_ENDPOINT
from pyficollar.exceptions import FiAuthError, FiGraphQLError
from pyficollar.transport import FiTransport
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


class MockTransport(FiTransport):
    """Mock transport that serves pre-recorded responses."""

    def __init__(self) -> None:
        super().__init__()
        self.last_requested_op = None
        self.last_variables = None

    def request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        if "checkemail" in endpoint:
            if "exists" in endpoint or "me@aoneill.me" in endpoint:
                return {"exists": True}
            return {"exists": False}

        if endpoint == LOGIN_ENDPOINT:
            if data and data.get("password") == "correct_password":
                return LOGIN_RESPONSE
            raise FiAuthError("Unauthorized")

        return {}

    def execute_graphql(
        self,
        query: str,
        operation_name: str | None = None,
        variables: dict[str, Any] | None = None,
        op_type: str | None = None,
    ) -> dict[str, Any]:
        self.last_requested_op = operation_name
        self.last_variables = variables

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

        if operation_name in mapping:
            return mapping[operation_name]

        return {"data": {}}


class TestFiClient(unittest.TestCase):
    def setUp(self) -> None:
        self.transport = MockTransport()
        self.client = FiClient(transport=self.transport)

    def test_check_email(self) -> None:
        self.assertTrue(self.client.check_email("me@aoneill.me"))
        self.assertFalse(self.client.check_email("notfound@example.com"))

    def test_login_success(self) -> None:
        res = self.client.login("me@aoneill.me", "correct_password", save_session=False)
        self.assertEqual(res["userId"], "36fSMTPhVaC3Zr74eeYIWX")
        self.assertTrue(self.client.is_authenticated)
        self.assertEqual(self.client.current_user_id, "36fSMTPhVaC3Zr74eeYIWX")

    def test_login_failure(self) -> None:
        with self.assertRaises(FiAuthError):
            self.client.login("me@aoneill.me", "wrong_password", save_session=False)

    def test_get_current_user(self) -> None:
        user = self.client.get_current_user()
        self.assertEqual(user.first_name, "Alex")
        self.assertEqual(user.email, "me@aoneill.me")

    def test_get_pets(self) -> None:
        pets = self.client.get_pets()
        self.assertEqual(len(pets), 1)
        self.assertEqual(pets[0].name, "Ritz")

    def test_get_pet_live_state(self) -> None:
        live = self.client.get_pet_live_state("3uM1gkV7XRhltddsxTEx3s")
        self.assertEqual(self.transport.last_requested_op, "PetLiveState")
        self.assertEqual(self.transport.last_variables, {"petId": "3uM1gkV7XRhltddsxTEx3s"})
        self.assertTrue(live.is_online)
        self.assertEqual(live.location_name, "Home")
        self.assertEqual(live.battery_percent, 99)

    def test_get_pet_activity(self) -> None:
        activity = self.client.get_pet_activity("3uM1gkV7XRhltddsxTEx3s")
        self.assertEqual(activity.total_steps, 5629)
        self.assertEqual(activity.step_goal, 10000)

    def test_get_pet_rest(self) -> None:
        rest = self.client.get_pet_rest("3uM1gkV7XRhltddsxTEx3s")
        self.assertTrue(rest.has_sleep_data)
        self.assertGreater(rest.sleep_hours, 0)

    def test_get_pet_places(self) -> None:
        places = self.client.get_pet_places("3uM1gkV7XRhltddsxTEx3s")
        self.assertEqual(len(places), 1)
        self.assertEqual(places[0].name, "Home")

    def test_get_last_walk(self) -> None:
        walk = self.client.get_last_walk("3uM1gkV7XRhltddsxTEx3s")
        self.assertIsNotNone(walk)
        if walk:
            self.assertEqual(walk.total_steps, 3156)
            self.assertEqual(walk.present_user_name, "Hannah")

    def test_get_device(self) -> None:
        device = self.client.get_device("FC35H674757")
        self.assertEqual(device.module_id, "FC35H674757")
        self.assertEqual(device.battery_percent, 99)

    def test_set_led(self) -> None:
        dev = self.client.set_led("FC35H674757", led_enabled=True)
        self.assertEqual(self.transport.last_requested_op, "UpdateDeviceOperationParams")
        self.assertEqual(self.transport.last_variables, {"input": {"moduleId": "FC35H674757", "ledEnabled": True}})
        self.assertTrue(dev.led_enabled)

    def test_enable_lost_dog_mode(self) -> None:
        ttl = self.client.enable_lost_dog_mode("3uM1gkV7XRhltddsxTEx3s")
        self.assertEqual(self.transport.last_requested_op, "EnableOrExtendQuickReportMode")
        self.assertEqual(self.transport.last_variables, {"petId": "3uM1gkV7XRhltddsxTEx3s"})
        self.assertEqual(ttl, 120)


if __name__ == "__main__":
    unittest.main()
