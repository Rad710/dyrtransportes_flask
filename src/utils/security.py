import os
import re
import hashlib

from .locale import get_message

# Translation dictionaries
MESSAGES = {
    "en": {
        "invalid_email_format": "Invalid email format",
        "password_requirements": "Password must be at least 8 characters and include at least one number, one lowercase letter, and one uppercase letter",
    },
    "es": {
        "invalid_email_format": "Formato de correo electrónico inválido",
        "password_requirements": "La contraseña debe tener al menos 8 caracteres e incluir al menos un número, una letra minúscula y una letra mayúscula",
    },
}


def hash_password(password: str) -> str:
    """Hash password with SHA-256 and random salt"""
    salt = os.urandom(32)

    # Hash password with salt
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)

    # Combine salt and hash with $ separator
    return f"{salt.hex()}${hashed.hex()}"


def verify_password(password: str, stored_password: str) -> bool:
    """Verify password against stored salt$hash"""
    try:
        # Split stored value into salt and hash
        salt_str, hash_str = stored_password.split("$")
        salt = bytes.fromhex(salt_str)

        # Hash the provided password with stored salt
        hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)

        return hashed.hex() == hash_str
    except Exception:
        return False


def validate_user_email(email: str) -> str | None:
    # Validate email format
    email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(email_pattern, email):
        return get_message(MESSAGES, "invalid_email_format")

    return None


def validate_user_password(password: str) -> str | None:
    # Password must be at least 8 characters and include at least
    # one number, one lowercase letter, and one uppercase letter
    password_regex = r"^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}$"

    if not re.match(password_regex, password):
        return get_message(MESSAGES, "password_requirements")

    return None
