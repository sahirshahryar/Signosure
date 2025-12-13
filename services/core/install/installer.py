#!/usr/bin/env python3
"""
Signosure Installer CLI

A command-line tool for initial setup tasks, such as creating admin accounts.
Connects to the core service and authenticates using a challenge token.

Usage:
    python installer.py --host <ip>:<port> --challenge <token>
"""

import argparse
import getpass
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


def post_form(url: str, data: dict) -> tuple[int, dict | str]:
    """
    Send a POST request with form data.

    Returns:
        Tuple of (status_code, response_body)
        response_body is a dict if JSON, otherwise a string
    """
    encoded_data = urlencode(data).encode("utf-8")
    request = Request(
        url,
        data=encoded_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
            try:
                return response.status, json.loads(body)
            except json.JSONDecodeError:
                return response.status, body
    except HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, body


def verify_challenge(base_url: str, challenge: str) -> bool:
    """Verify the challenge token with the core service."""
    try:
        status, _ = post_form(
            urljoin(base_url, "/core/install/challenge"),
            {"challenge": challenge},
        )
        return status == 200
    except URLError as e:
        print(f"Error connecting to server: {e}")
        return False


def create_admin(base_url: str, challenge: str) -> bool:
    """Prompt for admin details and create the account."""
    print("\n--- Create Admin Account ---\n")

    email = input("Email address: ").strip()
    if not email:
        print("Email is required.")
        return False

    name = input("Name: ").strip()
    if not name:
        print("Name is required.")
        return False

    password = getpass.getpass("Password: ")
    if not password:
        print("Password is required.")
        return False

    confirm_password = getpass.getpass("Confirm password: ")
    if password != confirm_password:
        print("Passwords do not match.")
        return False

    try:
        status, response = post_form(
            urljoin(base_url, "/core/install/create-admin"),
            {
                "email": email,
                "name": name,
                "password": password,
                "challenge": challenge,
            },
        )

        if status == 200:
            print("\nAdmin account created successfully!")
            return True
        else:
            if isinstance(response, dict):
                detail = response.get("detail", "Unknown error")
                if isinstance(detail, dict) and "errors" in detail:
                    print(
                        f"\nFailed to create account: {', '.join(detail['errors'])}"
                    )
                else:
                    print(f"\nFailed to create account: {detail}")
            else:
                print(f"\nFailed to create account: {response}")
            return False

    except URLError as e:
        print(f"\nError connecting to server: {e}")
        return False


def main_menu(base_url: str, challenge: str) -> None:
    """Display the main menu and handle user selection."""
    while True:
        print("\n" + "=" * 40)
        print("Signosure Installer")
        print("=" * 40)
        print("\n1. Create admin account")
        print("2. Exit")
        print()

        choice = input("Select an option: ").strip()

        if choice == "1":
            create_admin(base_url, challenge)
        elif choice == "2":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid option. Please try again.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Signosure Installer CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--host",
        required=False,
        default="localhost:8000",
        help="Core service host in format <ip>:<port> (e.g., localhost:8000)",
    )
    parser.add_argument(
        "--challenge",
        required=True,
        help="Installation challenge token from the core service",
    )

    args = parser.parse_args()

    # Build base URL
    host = args.host
    if not host.startswith("http://") and not host.startswith("https://"):
        host = f"http://{host}"
    base_url = host.rstrip("/")

    print(f"Connecting to {base_url}...")

    # Verify challenge token
    if not verify_challenge(base_url, args.challenge):
        print(
            "Failed to verify challenge token. Please check your token and try again."
        )
        sys.exit(1)

    print("Challenge verified successfully!")

    # Enter main menu
    main_menu(base_url, args.challenge)


if __name__ == "__main__":
    main()
