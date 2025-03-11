from typing import Optional
from typing import Tuple

from flask import jsonify
from flask import request
from flask import Response

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import IntegrityError

from app_config import logger
from app_config import app
from app_config import db_session
from app_config import RequestWithUser

from decorators.token_required import token_required

from utils.security import hash_password
from utils.security import validate_user_email
from utils.security import validate_user_password

from models.user import User

request: RequestWithUser


@app.route("/api/user/profile", methods=["PUT"])
@token_required
def put_user_profile() -> Tuple[Response, int]:
    try:
        # Get the current user from the database
        stmt = select(User).where(
            User.user_id == request.current_user.user_id,
        )
        entry_to_update: Optional[User] = db_session.scalar(stmt)

        if entry_to_update is None:
            logger.error("update table User, user not found")
            return jsonify({"message": "Usuario no encontrado"}), 404

        name = request.form.get("name")
        email = request.form.get("email")
        new_password = request.form.get("new_password")

        # Check if all required fields are present
        if not name or not email:
            return jsonify({"message": "Missing required fields"}), 400

        if len(name) <= 0:
            return jsonify({"message": "Name must not be empty"}), 400

        # Validate email format
        email_error = validate_user_email(email)
        if email_error:
            return jsonify({"message": email_error}), 400

        # Validate new_password strength (example: minimum 8 characters)
        new_password_error = (
            validate_user_password(new_password) if new_password else None
        )
        if new_password_error:
            return jsonify({"message": new_password_error}), 400

        entry_to_update.name = name
        entry_to_update.email = email

        if new_password:
            entry_to_update.password_hash = hash_password(new_password)

        entry_to_update.modification_user = request.current_user.user_id

        db_session.commit()
        logger.info("updated table User, user_id: %s", entry_to_update.user_id)

        return (
            jsonify(
                {
                    "user": {
                        "user_id": entry_to_update.user_id,
                        "email": entry_to_update.email,
                        "name": entry_to_update.name,
                    },
                    "message": "Perfil actualizado exitosamente",
                }
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("invalid user data: %s", e)
        return jsonify({"message": f"Error, datos del usuario inválidos ({e})"}), 400

    except OperationalError as e:
        db_session.rollback()
        logger.error("update table User: connection error %s", e)
        return (
            jsonify({"message": "Error al actualizar perfil: problema de conexión"}),
            503,
        )

    except IntegrityError as e:
        db_session.rollback()
        error_message = str(e)
        logger.error("insert table Shipment, error: %s", e)

        # Check for duplicate entry error
        if "Duplicate entry" in error_message and "unique_email_user" in error_message:
            return jsonify({"message": "El correo electrónico ya está en uso"}), 400

        return (
            jsonify(
                {"message": "Error al actualizar Perfil: error de integridad de datos"}
            ),
            400,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("update table User, error: %s", e)
        return jsonify({"message": "Error al actualizar perfil"}), 500
