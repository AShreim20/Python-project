
import hashlib
import secrets

import db

_HASH_ITERATIONS = 200_000


def _hash_password(password, salt_hex):
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _HASH_ITERATIONS)
    return digest.hex()


def create_account(username, password):
    """
    Create a new user account. Raises ValueError for bad input, or
    whatever Supabase raises if the username is already taken
    (the `users.username` column has a UNIQUE constraint).
    """
    username = username.strip()
    if not username or not password:
        raise ValueError("Username and password are both required.")
    if len(password) < 4:
        raise ValueError("Password must be at least 4 characters.")

    salt_hex = secrets.token_hex(16)
    password_hash = _hash_password(password, salt_hex)

    db.supabase.table("users").insert(
        {"username": username, "password_hash": password_hash, "password_salt": salt_hex}
    ).execute()


def verify_login(username, password):
    """Return True if the username/password combination is correct."""
    username = username.strip()
    if not username or not password:
        return False

    result = (
        db.supabase.table("users")
        .select("password_hash, password_salt")
        .eq("username", username)
        .execute()
    )
    if not result.data:
        return False

    row = result.data[0]
    computed_hash = _hash_password(password, row["password_salt"])
    return secrets.compare_digest(computed_hash, row["password_hash"])
