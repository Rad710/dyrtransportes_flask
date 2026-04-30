from datetime import datetime
from datetime import timedelta
from datetime import timezone

from flask import Blueprint
from flask import request
from flask import jsonify
from flask import current_app

from sqlalchemy import select

import jwt

from app_config import logger
from app_config import db_session

from models.user import User

from utils.security import hash_password
from utils.security import verify_password
from utils.security import validate_user_email
from utils.security import validate_user_password

from utils.locale import get_message

auth_bp = Blueprint("auth", __name__)


# Translation dictionaries
MESSAGES = {
    "en": {
        "missing_required_fields": "Missing required fields",
        "name_empty": "Name must not be empty",
        "email_registered": "Email already registered",
        "registration_successful": "Registration successful",
        "registration_failed": "Registration failed",
        "missing_credentials": "Missing credentials",
        "user_not_found": "User not found",
        "invalid_password": "Invalid password",
        "login_successful": "Login successful",
        "login_failed": "Login failed",
        "invalid_email": "Invalid email format",
        "password_too_weak": "Password is too weak",
    },
    "es": {
        "missing_required_fields": "Faltan campos obligatorios",
        "name_empty": "El nombre no debe estar vacío",
        "email_registered": "Correo electrónico ya registrado",
        "registration_successful": "Registro exitoso",
        "registration_failed": "Error en el registro",
        "missing_credentials": "Faltan credenciales",
        "user_not_found": "Usuario no encontrado",
        "invalid_password": "Contraseña inválida",
        "login_successful": "Inicio de sesión exitoso",
        "login_failed": "Error en el inicio de sesión",
        "invalid_email": "Formato de correo electrónico inválido",
        "password_too_weak": "La contraseña es demasiado débil",
    },
}


@auth_bp.route("/api/auth/sign-up", methods=["POST"])
def register():
    try:
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if all required fields are present
        if not name or not email or not password:
            return (
                jsonify({"message": get_message(MESSAGES, "missing_required_fields")}),
                400,
            )

        if len(name) <= 0:
            return jsonify({"message": get_message(MESSAGES, "name_empty")}), 400

        # Validate email format
        email_validation = validate_user_email(email)
        if email_validation:
            return jsonify({"message": get_message(MESSAGES, "invalid_email")}), 400

        # Validate password strength
        password_validation = validate_user_password(password)
        if password_validation:
            return jsonify({"message": get_message(MESSAGES, "password_too_weak")}), 400

        # Check if user already exists
        stmt = select(User).where(User.email == email)
        existing_user = db_session.scalars(stmt).first()

        if existing_user:
            return jsonify({"message": get_message(MESSAGES, "email_registered")}), 409

        # Create new user
        new_user = User(
            email=email,
            name=name,
            password_hash=hash_password(password),
            modification_user=email,  # Using email as the modification user for creation
            modification_timestamp=datetime.now(timezone.utc),
        )

        # Add and commit to database
        db_session.add(new_user)
        db_session.commit()

        # Generate JWT token for automatic login after registration
        token = jwt.encode(
            {
                "user_id": new_user.user_id,
                "exp": datetime.now(timezone.utc) + timedelta(days=1),
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

        return (
            jsonify(
                {
                    "message": get_message(MESSAGES, "registration_successful"),
                    "token": token,
                    "user": {
                        "email": new_user.email,
                        "name": new_user.name,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        db_session.rollback()
        logger.error("Registration, error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "registration_failed")}), 500


@auth_bp.route("/api/auth/log-in", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    remember_me = request.form.get("remember_me") == "on"

    if not email or not password:
        return jsonify({"message": get_message(MESSAGES, "missing_credentials")}), 400

    try:
        # Query the user by email
        stmt = select(User).where(User.email == email)
        user = db_session.scalars(stmt).first()

        if not user:
            return jsonify({"message": get_message(MESSAGES, "user_not_found")}), 401

        # Verify password
        if not verify_password(password, user.password_hash):
            return jsonify({"message": get_message(MESSAGES, "invalid_password")}), 401

        # Generate token
        exp = datetime.now(timezone.utc) + timedelta(days=1)
        if remember_me:
            exp = datetime.now(timezone.utc) + timedelta(days=7)

        token = jwt.encode(
            {
                "user_id": user.user_id,
                "exp": exp,
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

        return jsonify(
            {
                "token": token,
                "user": {
                    "email": user.email,
                    "name": user.name,
                    "remember_me": remember_me,
                    "admin": user.user_id == "dyrtransportes",
                },
                "message": get_message(MESSAGES, "login_successful"),
            }
        )

    except Exception as e:
        db_session.rollback()
        logger.error("Login, error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "login_failed")}), 500
