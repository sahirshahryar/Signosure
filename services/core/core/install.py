"""
Installation routines for Signosure. Note that these routines are not
available if an admin user already exists in the database.
"""

import base64
import os

from email_validator import validate_email
from fastapi import APIRouter, Form, HTTPException

from core.mongodb import User, UserActivity
from core.users import PASSWORD_HASHING_ITERATIONS, hash_password, validate_user

router = APIRouter()
INSTALLATION_CHALLENGE = base64.b64encode(os.urandom(12)).decode("utf-8")


@router.post("/challenge")
async def check_challenge(challenge: str = Form(...)):
    if challenge != INSTALLATION_CHALLENGE:
        raise HTTPException(403, "Incorrect installation challenge")
    return {"success": True}


@router.post("/create-admin")
async def create_admin(
    email: str = Form(...),
    name: str = Form(...),
    password: str = Form(...),
    challenge: str = Form(...),
):
    await check_challenge(challenge)
    await validate_user(email, password, skip_registration_check=True)
    parsed_email = validate_email(email)
    norm_email = parsed_email.email

    # Hash user's password
    salt = os.urandom(32)
    password_hash = hash_password(password, salt, PASSWORD_HASHING_ITERATIONS)

    salt_encoded = base64.b64encode(salt).decode("utf-8")
    hash_encoded = base64.b64encode(password_hash).decode("utf-8")
    pass_hash_str = (
        f"pbkdf2:sha256:{PASSWORD_HASHING_ITERATIONS}:"
        f"{salt_encoded}:{hash_encoded}"
    )

    new_user = User(
        email=norm_email,
        name=name,
        confirm_token="",
        confirm_exp=0,
        validated=True,
        oauth=False,
        pass_hash=pass_hash_str,
        admin=True,
        unscoped_permissions=0,
        scoped_permissions={},
        admin_scopes=set(),
        activity_id="",
    )

    await new_user.save()

    user_activity = UserActivity(
        user_id=str(new_user.id),
        collection_activity={},
        annotation_activity={},
    )

    await user_activity.save()

    # Update user with activity_id
    new_user.activity_id = str(user_activity.id)
    await new_user.save()

    return {"success": True}
