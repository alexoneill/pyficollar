"""Tests for TryFi models."""

from __future__ import annotations

import unittest
from pyficollar.models import (
    ActivitySummary,
    Device,
    Pet,
    PetLiveState,
    Place,
    RestSummary,
    User,
    Walk,
)
from tests.fixtures import (
    AllUserPets,
    CurrentUserPetsAndDevices,
    GetDevice,
    GetPetPlaces,
    HomescreenActivityInfo,
    HomescreenPetRestInfo,
    LastWalkWithMap,
    PetLiveState as PetLiveStateFixture,
    UpdateDeviceOperationParams,
)


class TestModels(unittest.TestCase):
    def test_user_model(self):
        user_data = CurrentUserPetsAndDevices["data"]["currentUser"]
        user = User.from_dict(user_data)
        self.assertEqual(user.id, "36fSMTPhVaC3Zr74eeYIWX")
        self.assertEqual(user.first_name, "Alex")
        self.assertEqual(len(user.households), 2)
        self.assertEqual(user.households[0].name, "Hannah's Pack")
        self.assertEqual(len(user.all_pets), 1)
        self.assertEqual(user.all_pets[0].name, "Ritz")

    def test_pet_model(self):
        pet_data = AllUserPets["data"]["currentUser"]["userHouseholds"][0]["household"]["pets"][0]
        pet = Pet.from_dict(pet_data)
        self.assertEqual(pet.name, "Ritz")
        self.assertEqual(pet.breed_name, "Australian Labradoodle")
        self.assertEqual(pet.gender, "MALE")
        self.assertAlmostEqual(pet.weight_lbs, 24.0, delta=0.5)
        self.assertIsNotNone(pet.photo_url)
        self.assertIsNotNone(pet.device)
        self.assertEqual(pet.device.module_id, "FC35H674757")

    def test_device_model(self):
        dev_data = GetDevice["data"]["device"]
        dev = Device.from_dict(dev_data)
        self.assertEqual(dev.module_id, "FC35H674757")
        self.assertEqual(dev.battery_percent, 99)
        self.assertFalse(dev.led_enabled)
        self.assertGreater(len(dev.available_led_colors), 0)

    def test_device_update_model(self):
        dev_data = UpdateDeviceOperationParams["data"]["updateDeviceOperationParams"]
        dev = Device.from_dict(dev_data)
        self.assertEqual(dev.module_id, "FC35H674757")
        self.assertTrue(dev.led_enabled)

    def test_pet_live_state_model(self):
        live_data = PetLiveStateFixture["data"]["petLiveState"]
        live = PetLiveState.from_dict(live_data, pet_id="3uM1gkV7XRhltddsxTEx3s")
        self.assertTrue(live.is_online)
        self.assertEqual(live.location_name, "Home")
        self.assertTrue(live.is_at_home)
        self.assertIsNotNone(live.latitude)
        self.assertIsNotNone(live.longitude)
        self.assertEqual(live.battery_percent, 99)
        self.assertEqual(live.lost_mode, "LDM_DISABLED")

    def test_activity_summary(self):
        act_data = HomescreenActivityInfo["data"]["pet"]
        act = ActivitySummary.from_dict(act_data)
        self.assertEqual(act.total_steps, 5629)
        self.assertEqual(act.step_goal, 10000)
        self.assertEqual(act.goal_percent, 56.3)

    def test_rest_summary(self):
        rest_data = HomescreenPetRestInfo["data"]["pet"]
        rest = RestSummary.from_dict(rest_data)
        self.assertTrue(rest.has_sleep_data)
        self.assertGreater(rest.sleep_hours, 0)
        self.assertGreater(rest.nap_hours, 0)

    def test_walk_model(self):
        activities = LastWalkWithMap["data"]["pet"]["activityFeed"]["activities"]
        walk = Walk.from_dict(activities[0])
        self.assertEqual(walk.id, "5tI1qtE1bI8a9QUXOgXMdp")
        self.assertEqual(walk.total_steps, 3156)
        self.assertEqual(walk.present_user_name, "Hannah")
        self.assertAlmostEqual(walk.distance_km, 1.08, delta=0.1)
        self.assertGreater(len(walk.path), 0)

    def test_places_model(self):
        places_data = GetPetPlaces["data"]["pet"]["household"]["places"]
        places = [Place.from_dict(p) for p in places_data]
        self.assertEqual(len(places), 1)
        self.assertEqual(places[0].name, "Home")
        self.assertIn("Carroll", places[0].address or "")


if __name__ == "__main__":
    unittest.main()
