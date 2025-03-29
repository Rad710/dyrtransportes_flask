from datetime import datetime
from datetime import timedelta
from datetime import timezone

from flask import request
from flask import jsonify

from sqlalchemy import select

import jwt

from app_config import app
from app_config import logger
from app_config import db_session

from models.user import User

from utils.security import hash_password
from utils.security import verify_password
from utils.security import validate_user_email
from utils.security import validate_user_password


@app.route("/api/auth/sign-up", methods=["POST"])
def register():
    try:
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if all required fields are present
        if not name or not email or not password:
            return jsonify({"message": "Missing required fields"}), 400

        if len(name) <= 0:
            return jsonify({"message": "Name must not be empty"}), 400

        # Validate email format
        email_validation = validate_user_email(email)
        if email_validation:
            return jsonify({"message": email_validation}), 400

        # Validate password strength (example: minimum 8 characters)
        password_validation = validate_user_password(password)
        if password_validation:
            return jsonify({"message": password_validation}), 400

        # Check if user already exists
        stmt = select(User).where(User.email == email)
        existing_user = db_session.scalars(stmt).first()

        if existing_user:
            return jsonify({"message": "Email already registered"}), 409

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
                "exp": datetime.now(timezone.utc) + timedelta(days=7),
            },
            app.config["SECRET_KEY"],
            algorithm="HS256",
        )

        return (
            jsonify(
                {
                    "message": "Registration successful",
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
        return jsonify({"message": "Registration failed"}), 500


@app.route("/api/auth/log-in", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    remember_me = request.form.get("remember_me") == "on"

    if not email or not password:
        return jsonify({"message": "Missing credentials"}), 400

    try:
        # Query the user by email
        stmt = select(User).where(User.email == email)
        user = db_session.scalars(stmt).first()

        if not user:
            return jsonify({"message": "User not found"}), 401

        # Verify password
        if not verify_password(password, user.password_hash):
            return jsonify({"message": "Invalid password"}), 401

        # Generate token
        exp = datetime.now(timezone.utc) + timedelta(days=1)
        if remember_me:
            exp = datetime.now(timezone.utc) + timedelta(days=7)

        token = jwt.encode(
            {
                "user_id": user.user_id,
                "exp": exp,
            },
            app.config["SECRET_KEY"],
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
                "message": "Login successful",
            }
        )

    except Exception as e:
        db_session.rollback()
        logger.error("Login, error: %s", e)
        return jsonify({"message": "Login failed"}), 500
