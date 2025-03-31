from functools import wraps

from flask import request
from flask import jsonify

from sqlalchemy import select

from jwt import decode
from jwt import ExpiredSignatureError
from jwt import InvalidTokenError

from app_config import app
from app_config import db_session
from app_config import logger

from app_config import RequestWithUser
from utils.locale import get_message

from models.user import User

request: RequestWithUser

# Translation dictionaries
MESSAGES = {
    "en": {
        "token_missing": "Token is missing",
        "token_expired": "Token has expired",
        "invalid_token": "Invalid token",
        "user_not_found": "User not found",
        "generic_error": "Error",
    },
    "es": {
        "token_missing": "Falta el token",
        "token_expired": "El token ha expirado",
        "invalid_token": "Token inválido",
        "user_not_found": "Usuario no encontrado",
        "generic_error": "Error",
    },
}


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"message": get_message(MESSAGES, "token_missing")}), 401

        try:
            if token.startswith("Bearer "):
                token = token[7:]

            # Decode token
            data = decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])

            # Get user from database
            stmt = select(User).where(User.user_id == data["user_id"])
            current_user = db_session.scalars(stmt).first()

            if not current_user:
                return (
                    jsonify({"message": get_message(MESSAGES, "user_not_found")}),
                    401,
                )

            # Add user to request context
            request.current_user = current_user

        except ExpiredSignatureError as e:
            logger.error("Error, expired token: %s", e)
            return jsonify({"message": get_message(MESSAGES, "token_expired")}), 401
        except InvalidTokenError as e:
            logger.error("Error, invalid token: %s", e)
            return jsonify({"message": get_message(MESSAGES, "invalid_token")}), 401
        except Exception as e:
            logger.error("Error: %s", e)
            return jsonify({"message": get_message(MESSAGES, "generic_error")}), 500

        return f(*args, **kwargs)

    return decorated
