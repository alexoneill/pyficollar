# AGENTS.md

Guidance and instructions for AI coding agents working on the `pyficollar` codebase.

---

## 1. Project Overview

`pyficollar` is a Python client library and CLI for the **TryFi (Fi Smart Dog Collar)** API (`https://api.tryfi.com`). It was reverse-engineered from official iOS app network traffic (`Fi/3.142.0`).

### Core Design Principles
- **Zero Mandatory External Dependencies**: Built strictly using the Python standard library (`urllib.request`, `http.cookiejar`, `json`, `dataclasses`). Keep core runtime dependency-free.
- **Session Persistence**: Sessions can be saved to and loaded from JSON files (`save_session` / `load_session`) so credentials are only needed once.
- **Offline Testability**: All tests run without internet access using real payloads captured in `tests/fixtures.py`.
- **Typing & Standards**: Modern type annotations (PEP 561 `py.typed`).

---

## 2. Directory Layout

```
.
├── pyficollar/             # Main package source code
│   ├── __init__.py         # Public exports (FiClient, models, exceptions, constants)
│   ├── client.py           # FiClient: high-level domain methods and raw GraphQL executor
│   ├── const.py            # Endpoints, default headers, API key, LED color definitions
│   ├── exceptions.py       # FiError, FiAuthError, FiGraphQLError, FiNetworkError, FiDeviceError
│   ├── models.py           # Dataclasses with .from_dict() methods and helper properties
│   ├── queries.py          # 40 full GraphQL operations and fragment documents
│   ├── transport.py        # FiTransport: HTTP transport, cookies, session persistence
│   ├── cli.py              # CLI tool (login, pets, live, led)
│   └── py.typed            # PEP 561 typed package marker
├── tests/                  # Offline unit test suite
│   ├── fixtures.py         # Real JSON payloads extracted from request_log.chlsj
│   ├── test_client.py      # FiClient tests with MockTransport
│   ├── test_models.py      # Model deserialization and property tests
│   └── test_session.py     # Disk session persistence tests
├── demo_mock.py            # Standalone offline demonstration script
├── pyproject.toml          # PEP 621 / setuptools build configuration
├── README.md               # User documentation and API reference
├── LICENSE                 # MIT License
└── .gitignore              # Ignores *.session.json, *.chlsj, caches, virtualenvs
```

---

## 3. Key Modules & Responsibilities

### `pyficollar.client.FiClient`
- High-level interface for developers.
- `login(email, password, save_session=True)`: Posts to `/auth/login`, retrieves session ID and user ID, updates cookies.
- `save_session(path)` / `load_session(path)`: Persists session to JSON.
- `get_pets()`, `get_pet(id)`: Returns `list[Pet]` or `Pet`.
- `get_pet_live_state(id)`: Returns real-time GPS coordinates, battery %, safe place name, and online state.
- `set_led(module_id, led_enabled)`: Sends `UpdateDeviceOperationParams` mutation to toggle LED.
- `enable_lost_dog_mode(pet_id)`: Triggers `EnableOrExtendQuickReportMode` mutation (returns TTL seconds).
- `get_last_walk(pet_id)`: Retrieves last walk with GPS path points and metrics.
- `execute_graphql(op_name, variables)`: Runs an operation registered in `queries.py`.
- `execute_raw_graphql(query, variables)`: Runs arbitrary GraphQL queries.

### `pyficollar.models`
- Models are dataclasses with safe `.from_dict()` class methods.
- Always use `dict.get(...)` defensively when parsing dictionary fields to avoid breaking if Fi changes or omits optional fields.
- Computed properties provide ergonomic values (e.g., `pet.weight_lbs`, `live_state.is_at_home`, `live_state.latitude`, `walk.distance_km`).

### `pyficollar.queries`
- Contains exact GraphQL operation texts and fragments matching the mobile app.
- Maps operation names in `OPERATIONS` dict and operation types (`query` vs `mutation`) in `OPERATION_TYPES`.

### `pyficollar.transport.FiTransport`
- Handles cookie jars, automatic injection of Apollo headers (`apollographql-client-name`, `X-APOLLO-OPERATION-NAME`, `X-Api-Key`), and JSON payload serialization.
- Converts HTTP 401/403 into `FiAuthError` and GraphQL error arrays into `FiGraphQLError`.

---

## 4. Development Workflow

### Running Tests
Always run the test suite after making changes:
```bash
python3 -m unittest discover tests
```

### Running the Demo
Verify that offline execution remains functional:
```bash
python3 demo_mock.py
```

### Testing the CLI
```bash
python3 -m pyficollar.cli --help
```

---

## 5. Adding New Features

### Adding a New GraphQL Operation
1. Check if the operation is already present in `pyficollar/queries.py` (40 operations are pre-registered). If not, add the full query and fragments to `pyficollar/queries.py` and register it in `OPERATIONS` and `OPERATION_TYPES`.
2. If new data structures are returned, define or extend dataclasses in `pyficollar/models.py` with a `.from_dict()` method.
3. Add a convenience method in `pyficollar/client.py` on `FiClient`.
4. Add a sample response fixture to `tests/fixtures.py`.
5. Add unit tests in `tests/test_client.py` and `tests/test_models.py`.

### Dependencies & Compatibility
- Keep dependencies strictly optional. Do not import third-party packages in `pyficollar` root or standard runtime without a fallback or try/except block.

---

## 6. Security Considerations
- **NEVER** commit session tokens, password hashes, or `*.session.json` files to Git.
- **NEVER** commit Charles Proxy traces or HAR files (`*.chlsj`, `*.chls`, `*.har`) as they may contain plaintext authentication requests.
- Test fixtures in `tests/fixtures.py` should only contain mock or non-sensitive response structures.
