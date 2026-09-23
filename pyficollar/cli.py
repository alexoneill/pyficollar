"""CLI utility for TryFi API interaction."""

from __future__ import annotations
import argparse
import getpass
import os
from pathlib import Path
import sys

from .client import FiClient
from .exceptions import FiAuthError, FiError

DEFAULT_SESSION_FILE = Path.home() / ".tryfi_session.json"


def get_client(session_file: Path | None = None) -> FiClient:
    sf = session_file or DEFAULT_SESSION_FILE
    client = FiClient(session_file=sf)
    return client


def cmd_login(args: argparse.Namespace) -> None:
    session_file = Path(args.session_file) if args.session_file else DEFAULT_SESSION_FILE
    client = FiClient(session_file=session_file)

    email = args.email or input("TryFi Email: ").strip()
    password = args.password
    if not password:
        password = getpass.getpass("TryFi Password: ")

    try:
        print(f"Authenticating as {email}...")
        client.login(email=email, password=password, save_session=True)
        print(f"Successfully authenticated! Session saved to: {session_file}")
    except FiAuthError as e:
        print(f"Authentication failed: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_pets(args: argparse.Namespace) -> None:
    client = get_client(Path(args.session_file) if args.session_file else None)
    if not client.is_authenticated:
        print("Not logged in. Run `python -m fi.cli login` first or specify --session-file.", file=sys.stderr)
        sys.exit(1)

    try:
        pets = client.get_pets()
        if not pets:
            print("No pets found on this account.")
            return

        print(f"Found {len(pets)} pet(s):")
        for p in pets:
            weight_str = f"{p.weight_lbs} lbs" if p.weight_lbs else "unknown"
            dev_str = f"Module: {p.device.module_id} (Battery: {p.device.battery_percent}%)" if p.device else "No device"
            print(f"- {p.name} (ID: {p.id})")
            print(f"    Breed: {p.breed_name or 'Unknown'}")
            print(f"    Weight: {weight_str}")
            print(f"    Device: {dev_str}")
            print(f"    Handle: @{p.fi_handle or 'none'}")
    except FiError as e:
        print(f"Error fetching pets: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_live(args: argparse.Namespace) -> None:
    client = get_client(Path(args.session_file) if args.session_file else None)
    if not client.is_authenticated:
        print("Not logged in. Run `python -m fi.cli login` first.", file=sys.stderr)
        sys.exit(1)

    try:
        live = client.get_pet_live_state(args.pet_id)
        print(f"=== Live State for Pet {args.pet_id} ===")
        print(f"Status: {'ONLINE' if live.is_online else 'OFFLINE'} ({live.online_state})")
        print(f"Battery: {live.battery_percent}% (Charging: {live.has_power_supply})")
        print(f"Current Location: {live.location_name or 'Unknown'}")
        if live.latitude and live.longitude:
            print(f"Coordinates: {live.latitude}, {live.longitude}")
        print(f"At Safe Place: {live.at_safe_zone.name if live.at_safe_zone else 'No'}")
        print(f"Lost Dog Mode: {live.lost_mode}")
        if live.is_walking:
            print(f"Currently walking! Steps: {live.ongoing_steps}, Distance: {round(live.ongoing_distance_meters)}m")
        print(f"Last Reported: {live.last_report_timestamp}")
    except FiError as e:
        print(f"Error fetching live state: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_led(args: argparse.Namespace) -> None:
    client = get_client(Path(args.session_file) if args.session_file else None)
    if not client.is_authenticated:
        print("Not logged in. Run `python -m fi.cli login` first.", file=sys.stderr)
        sys.exit(1)

    state = args.state.lower() in ("on", "1", "true")
    try:
        dev = client.set_led(args.module_id, led_enabled=state)
        print(f"LED on module {dev.module_id} is now {'ON' if dev.led_enabled else 'OFF'}.")
    except FiError as e:
        print(f"Error setting LED: {e}", file=sys.stderr)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TryFi Collar API CLI")
    parser.add_argument("--session-file", help="Path to session JSON file", default=str(DEFAULT_SESSION_FILE))
    subparsers = parser.add_subparsers(dest="command", required=True)

    login_p = subparsers.add_parser("login", help="Authenticate with TryFi account")
    login_p.add_argument("--email", help="Account email")
    login_p.add_argument("--password", help="Account password")
    login_p.set_defaults(func=cmd_login)

    pets_p = subparsers.add_parser("pets", help="List pets and their collar modules")
    pets_p.set_defaults(func=cmd_pets)

    live_p = subparsers.add_parser("live", help="Check pet real-time live location & battery")
    live_p.add_argument("pet_id", help="Target Pet ID")
    live_p.set_defaults(func=cmd_live)

    led_p = subparsers.add_parser("led", help="Turn collar LED light on or off")
    led_p.add_argument("module_id", help="Collar module ID (e.g. FC35H674757)")
    led_p.add_argument("state", choices=["on", "off"], help="LED state (on or off)")
    led_p.set_defaults(func=cmd_led)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
