# TryFi Python API Client

A Python client library for the **TryFi (Fi Smart Dog Collar)** API, reconstructed directly from iOS app network traces (`request_log.chlsj`).

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
  - [Authentication & Session Persistence](#1-authentication--session-persistence)
  - [Pets & Real-Time Live State](#2-inspect-pets-and-live-state)
  - [Collar Controls (LED & Lost Dog Mode)](#3-collar-controls-led-and-lost-dog-mode)
  - [Activity, Rest, and Walks](#4-activity-rest-and-walks)
- [API Reference](#api-reference)
  - [`FiClient` Methods](#ficlient-methods)
  - [Data Models](#data-models)
  - [Collar LED Colors](#collar-led-colors)
  - [Captured GraphQL Operations (40 Operations)](#captured-graphql-operations-40-operations)
- [Command Line Interface (CLI)](#command-line-interface-cli)
- [Offline Testing & Demonstration](#offline-testing--demonstration)
- [Security & Privacy](#security--privacy)

---

## Features

- **Zero External Dependencies**: Built entirely on the Python standard library (`urllib.request`, `http.cookiejar`, `dataclasses`).
- **Session Persistence**: Save and restore authenticated sessions (`save_session` / `load_session`) to avoid entering credentials repeatedly.
- **Real-Time Live State**: Live GPS coordinates, battery percentage, charging status, online/offline status, and safe place detection.
- **Hardware & Collar Controls**:
  - Turn collar LED light ON / OFF.
  - Inspect current and available LED colors.
  - Trigger Lost Dog Mode (Quick Report Mode) for emergency GPS tracking.
- **Activity & Sleep Tracking**: Daily steps, step goals, strain levels, overnight sleep, and nap duration.
- **Walk History**: Historical walk routes with GPS paths, distance in km/miles, step counts, and walker information.
- **Full GraphQL Registry**: 40 extracted GraphQL operations and query documents captured directly from the official iOS client.
- **CLI Utility**: Command-line tool `tryfi` or `python -m fi.cli` for quick checks and device control.

---

## Installation

```bash
pip install .
```

Or copy the `fi/` package directory directly into your project.

---

## Quick Start

### 1. Authentication & Session Persistence

```python
from fi import FiClient

# Initialize client with a session file path for persistence
client = FiClient(session_file="~/.tryfi_session.json")

# If the session file does not exist or has expired, log in:
if not client.is_authenticated:
    client.login("your_email@example.com", "your_password", save_session=True)
```

Subsequent runs will automatically load the credentials from `~/.tryfi_session.json`.

### 2. Inspect Pets and Live State

```python
# Fetch all pets across your households
pets = client.get_pets()
for pet in pets:
    print(f"Dog: {pet.name} ({pet.breed_name}, {pet.weight_lbs} lbs)")
    
    # Real-time Live State
    live = client.get_pet_live_state(pet.id)
    print(f"  Status: {'Online' if live.is_online else 'Offline'}")
    print(f"  Battery: {live.battery_percent}% (Charging: {live.has_power_supply})")
    print(f"  Location: {live.location_name} (Coordinates: {live.latitude}, {live.longitude})")
    print(f"  At Home: {live.is_at_home}")
```

### 3. Collar Controls: LED and Lost Dog Mode

```python
module_id = pets[0].device.module_id

# Toggle LED light
client.set_led(module_id, led_enabled=True)
print("Collar LED turned ON")

# Turn off LED light
client.set_led(module_id, led_enabled=False)
print("Collar LED turned OFF")

# Activate Lost Dog Mode (120-second quick reporting interval)
ttl = client.enable_lost_dog_mode(pets[0].id)
print(f"Lost dog mode active for {ttl} seconds")
```

### 4. Activity, Rest, and Walks

```python
pet_id = pets[0].id

# Steps & Activity
activity = client.get_pet_activity(pet_id)
print(f"Steps: {activity.total_steps:,} / {activity.step_goal:,} ({activity.goal_percent}%)")

# Sleep & Nap
rest = client.get_pet_rest(pet_id)
print(f"Sleep: {rest.sleep_hours} hrs | Naps: {rest.nap_hours} hrs")

# Last Walk
walk = client.get_last_walk(pet_id)
if walk:
    print(f"Last Walk: {walk.distance_miles} miles, {walk.total_steps} steps, walker: {walk.present_user_name}")
    print(f"Route coordinates: {len(walk.path)} GPS waypoints")
```

---

## API Reference

### `FiClient` Methods

| Method | Parameters | Returns | Description |
|---|---|---|---|
| `check_email` | `email: str` | `bool` | Check whether an email is registered with TryFi (`GET /auth/checkemail`). |
| `login` | `email: str, password: str, sync_locale_to_account: bool = True, save_session: bool = True` | `dict[str, Any]` | Authenticate using credentials and set up session cookies (`POST /auth/login`). |
| `save_session` | `filepath: str \| Path \| None = None` | `None` | Serialize active session and cookies to a JSON file. |
| `load_session` | `filepath: str \| Path` | `bool` | Restore cookies and session ID from a saved JSON file. |
| `get_current_user` | None | `User` | Fetch user account details, households, and registered dogs. |
| `get_pets` | None | `list[Pet]` | Fetch all pets linked to the user's account. |
| `get_pet` | `pet_id: str` | `Pet` | Fetch profile details for a specific pet. |
| `get_pet_live_state` | `pet_id: str` | `PetLiveState` | Fetch real-time GPS location, battery %, online status, and safe place info. |
| `get_pet_activity` | `pet_id: str` | `ActivitySummary` | Fetch daily step count, goal, streak, and strain score. |
| `get_pet_rest` | `pet_id: str` | `RestSummary` | Fetch sleep and nap statistics. |
| `get_pet_places` | `pet_id: str` | `list[Place]` | Fetch configured safe places (e.g. Home) and containment zones. |
| `get_last_walk` | `pet_id: str, ...` | `Walk \| None` | Fetch most recent walk, route coordinates, steps, and distance. |
| `get_device` | `module_id: str` | `Device` | Fetch hardware info, battery %, LED state, and firmware status. |
| `set_led` | `module_id: str, led_enabled: bool` | `Device` | Turn collar LED light on or off. |
| `enable_lost_dog_mode` | `pet_id: str` | `int` | Activate Lost Dog Mode (returns TTL in seconds). |
| `execute_graphql` | `operation_name: str, variables: dict = None` | `dict[str, Any]` | Execute one of the 40 pre-registered operations. |
| `execute_raw_graphql` | `query: str, variables: dict = None` | `dict[str, Any]` | Execute an arbitrary custom GraphQL query document. |

---

### Data Models

- **`User`**: `id`, `email`, `first_name`, `last_name`, `households: list[Household]`, `all_pets: list[Pet]`.
- **`Household`**: `id`, `name`, `role`, `pets: list[Pet]`.
- **`Pet`**: `id`, `name`, `gender`, `breed_name`, `weight`, `weight_lbs`, `photo_url`, `device: Device`.
- **`Device`**: `module_id`, `model_name`, `carrier`, `battery_percent`, `has_power_supply`, `led_enabled`, `led_color`, `available_led_colors`, `is_stale`.
- **`PetLiveState`**: `is_online`, `battery_percent`, `has_power_supply`, `latitude`, `longitude`, `location_name`, `is_at_home`, `at_safe_zone`, `lost_mode`, `is_walking`, `ongoing_steps`.
- **`ActivitySummary`**: `total_steps`, `step_goal`, `goal_percent`, `streak_days`, `strain_score`, `strain_level`.
- **`RestSummary`**: `has_sleep_data`, `sleep_hours`, `nap_hours`, `rest_hours`.
- **`Walk`**: `id`, `start`, `end`, `total_steps`, `distance_meters`, `distance_miles`, `distance_km`, `present_user_name`, `path: list[Position]`.
- **`Place`**: `id`, `name`, `address`, `position: Position`, `radius`, `city_state`, `is_quick_zone`.
- **`Position`**: `latitude`, `longitude`.
- **`LedColor`**: `led_color_code`, `hex_code`, `name`.

---

### Collar LED Colors

The collar supports 7 LED colors (defined in `fi.const.LedColorEnum`):

| Color Name | Code | Hex Code |
|---|---|---|
| **Red** | `2` | `#ff4242` |
| **Green** | `3` | `#3cba0f` |
| **Blue** | `4` | `#0071ff` |
| **Purple** | `5` | `#ff2fcc` |
| **Yellow** | `6` | `#ffff01` |
| **Cyan** | `7` | `#00ffff` |
| **White** | `8` | `#ffffff` |

---

### Captured GraphQL Operations (40 Operations)

Extracted directly from `request_log.chlsj` and available via `client.execute_graphql(op_name, variables)`:

1. `AllUserPets` (Query)
2. `ChargingBaseCredentials` (Query)
3. `CurrentUserPetsAndDevices` (Query)
4. `DeviceNormalModeReportInterval` (Query)
5. `DiscoverFeed` (Query)
6. `DismissCommsClientSplash` (Mutation)
7. `DismissCommsSplash` (Mutation)
8. `EnableOrExtendQuickReportMode` (Mutation)
9. `GetComms` (Query)
10. `GetDevice` (Query)
11. `GetFeatureFlags` (Query)
12. `GetInsights` (Query)
13. `GetIntelligenceTeaser` (Query)
14. `GetLocalizedAssets` (Query)
15. `GetModuleLatestFirmwareUpdate` (Query)
16. `GetMostRecentDeviceActuation` (Query)
17. `GetPermissionBlockers` (Query)
18. `GetPetPlaces` (Query)
19. `GetPetProfileStats` (Query)
20. `HelpCenterUrl` (Query)
21. `HomescreenActivityInfo` (Query)
22. `HomescreenPetRestInfo` (Query)
23. `LastWalkWithMap` (Query)
24. `ModuleCredentials` (Query)
25. `NotificationFeedUnreadCount` (Query)
26. `PetDocumentFeed` (Query)
27. `PetLifetimeStatsTiers` (Query)
28. `PetLiveState` (Query)
29. `PetPackFeed` (Query)
30. `PetProfileDiscoverFeed` (Query)
31. `RecentCommunityPhotoThumbnails` (Query)
32. `RegisterHandset` (Mutation)
33. `RegisterLiveActivityToken` (Mutation)
34. `ReportBaseAtPosition` (Mutation)
35. `SetDeviceActuationSuccess` (Mutation)
36. `SetTermsOfServiceAccepted` (Mutation)
37. `SubmitMobilityReport` (Mutation)
38. `UpdateDeviceOperationParams` (Mutation)
39. `UserPetProfile` (Query)
40. `getSharingSession` (Query)

---

## Command Line Interface (CLI)

```bash
# 1. Login & persist session to ~/.tryfi_session.json
python -m fi.cli login --email me@example.com

# 2. List dogs and collar batteries
python -m fi.cli pets

# 3. Check real-time live GPS & location
python -m fi.cli live <PET_ID>

# 4. Turn LED light on or off
python -m fi.cli led <MODULE_ID> on
python -m fi.cli led <MODULE_ID> off
```

---

## Offline Testing & Demonstration

Run tests and the demonstration script offline with zero network credentials:

```bash
# Run unit test suite (24 tests)
python3 -m unittest discover tests

# Run interactive demonstration
python3 demo_mock.py
```

---

## Security & Privacy

- Network traces containing cleartext passwords or session dumps (`*.chlsj`, `*.chls`, `*.har`, `*.session.json`) are ignored in `.gitignore`.
- Session files should be protected with appropriate filesystem permissions (`chmod 600 ~/.tryfi_session.json`).
