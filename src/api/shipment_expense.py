from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import List

from dataclasses import asdict

from flask import Blueprint
from flask import request
from flask import jsonify
from flask import Response

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import OperationalError

from app_config import logger
from app_config import db_session
from app_config import RequestWithUser

from decorators.token_required import token_required

from models.driver_payroll import DriverPayroll
from models.shipment_expense import ShipmentExpense
from utils.locale import get_message

shipment_expense_bp = Blueprint("shipment_expense", __name__)

request: RequestWithUser

# Translation dictionaries
MESSAGES = {
    "en": {
        # Error messages
        "expense_not_found": "Expense not found",
        "transaction_error": "Transaction error",
        "get_expenses_error": "Error getting expenses",
        "payroll_not_found": "Payroll not found",
        "invalid_payroll_code_param": "Parameter 'driver_payroll_code' must be an integer",
        "invalid_expense_data": "Invalid expense data",
        "connection_error": "Connection error",
        "add_expense_error": "Error adding expense",
        "update_expense_error": "Error updating expense",
        "delete_expense_error": "Error deleting expense",
        "invalid_payload": "Invalid payload",
        "expenses_not_found_to_update": "Expenses not found to update",
        "update_expenses_error": "Error updating expenses",
        "empty_expense_list": "Empty expense list",
        "expenses_not_found": "Expenses not found",
        # Success messages
        "expense_added": "Expense added successfully",
        "expense_updated": "Expense updated successfully",
        "expense_deleted": "Expense deleted successfully",
        "expenses_deleted": "Expenses deleted successfully",
        "expenses_updated": "Expenses updated successfully",
    },
    "es": {
        # Error messages
        "expense_not_found": "No se encontró el gasto",
        "transaction_error": "Error de transacción",
        "get_expenses_error": "Error al obtener gastos",
        "payroll_not_found": "Liquidación no encontrada",
        "invalid_payroll_code_param": "Parámetro 'driver_payroll_code' debe ser un número entero",
        "invalid_expense_data": "Datos del Gasto inválidos",
        "connection_error": "problema de conexión",
        "add_expense_error": "Error al agregar gasto",
        "update_expense_error": "Error al actualizar gasto",
        "delete_expense_error": "Error al eliminar gasto",
        "invalid_payload": "Payload inválido",
        "expenses_not_found_to_update": "No se encontraron los gastos para actualizar",
        "update_expenses_error": "Error al actualizar cargas",
        "empty_expense_list": "lista de gastos vacía",
        "expenses_not_found": "gasto no encontrado",
        # Success messages
        "expense_added": "Gasto agregado exitosamente",
        "expense_updated": "Gasto actualizado exitosamente",
        "expense_deleted": "Gasto eliminado exitosamente",
        "expenses_deleted": "Gastos eliminados exitosamente",
        "expenses_updated": "Gastos actualizadas exitosamente",
    },
}


@shipment_expense_bp.route("/api/shipment-expense/<int:expense_code>", methods=["GET"])
@token_required
def get_shipment_expense(expense_code: int) -> Tuple[Response, int]:
    try:
        stmt = select(ShipmentExpense).where(
            ShipmentExpense.expense_code == expense_code,
            ShipmentExpense.deleted == False,
            ShipmentExpense.modification_user == request.current_user.user_id,
        )

        shipment_expense: Optional[ShipmentExpense] = db_session.scalar(stmt)
        if shipment_expense is None:
            logger.error("fetch table ShipmentExpense, not found")
            return jsonify({"message": get_message(MESSAGES, "expense_not_found")}), 404

        logger.info(
            "fetch table ShipmentExpense, found: %s", shipment_expense.expense_code
        )
        logger.debug("fetch table ShipmentExpense, found: %s", shipment_expense)

        return jsonify(shipment_expense), 200

    except SQLAlchemyError as e:
        logger.error("fetch table ShipmentExpense, error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "transaction_error")}), 500


@shipment_expense_bp.route("/api/shipment-expenses", methods=["GET"])
@token_required
def get_shipment_expense_list() -> Tuple[Response, int]:
    driver_payroll_code_param: str | None = request.args.get("driver_payroll_code")
    driver_payroll_code = None

    # If driver_payroll_code_param is provided, validate it
    if driver_payroll_code_param:
        try:
            driver_payroll_code = int(driver_payroll_code_param)

            # Validate that the driver_payroll exists in the database
            stmt_driver_payroll = select(DriverPayroll).where(
                DriverPayroll.payroll_code == driver_payroll_code,
                DriverPayroll.deleted == False,
                DriverPayroll.modification_user == request.current_user.user_id,
            )

            driver_payroll = db_session.scalar(stmt_driver_payroll)
            if not driver_payroll:
                logger.error(
                    "DriverPayroll with code %s not found", driver_payroll_code
                )
                return (
                    jsonify({"message": get_message(MESSAGES, "payroll_not_found")}),
                    404,
                )

        except ValueError:
            logger.error("Invalid 'driver_payroll_code' parameter: not an integer")
            return (
                jsonify(
                    {"message": get_message(MESSAGES, "invalid_payroll_code_param")}
                ),
                400,
            )

    try:
        shipment_expenses_stmt = (
            select(ShipmentExpense)
            .where(
                ShipmentExpense.deleted == False,
                ShipmentExpense.modification_user == request.current_user.user_id,
            )
            .order_by(
                ShipmentExpense.expense_date,
            )
        )

        if driver_payroll_code:
            shipment_expenses_stmt = shipment_expenses_stmt.where(
                ShipmentExpense.driver_payroll_code == driver_payroll_code
            )

        shipment_expenses: Sequence[ShipmentExpense] = db_session.scalars(
            shipment_expenses_stmt
        ).all()
        logger.info(
            "fetch shipment_expenses table ShipmentExpense, len: %s",
            len(shipment_expenses),
        )
        logger.debug(
            "fetch shipment_expenses table ShipmentExpense, shipment_expenses: %s",
            shipment_expenses,
        )
        return jsonify(shipment_expenses), 200

    except SQLAlchemyError as e:
        logger.error("fetch shipment_expenses table ShipmentExpense, error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "get_expenses_error")}), 500


@shipment_expense_bp.route("/api/shipment-expense", methods=["POST"])
@token_required
def post_shipment_expense() -> Tuple[Response, int]:
    try:
        # json to db object
        payload = ShipmentExpense(
            **{**request.get_json(), "modification_user": request.current_user.user_id}
        )

        # Verify driver payroll exists
        stmt = select(DriverPayroll).where(
            DriverPayroll.payroll_code == payload.driver_payroll_code,
            DriverPayroll.modification_user == request.current_user.user_id,
        )
        existing_payroll: Optional[DriverPayroll] = db_session.scalar(stmt)
        if existing_payroll is None:
            logger.error("insert table ShipmentExpense, driver payroll not found")
            return jsonify({"message": get_message(MESSAGES, "payroll_not_found")}), 404

        # add to database
        logger.debug("insert table ShipmentExpense, payload: %s", payload)
        db_session.add(payload)

        db_session.commit()
        logger.info("inserted table ShipmentExpense, expense: %s", payload.expense_code)
        return (
            jsonify(
                {**asdict(payload), "message": get_message(MESSAGES, "expense_added")}
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("insert table ShipmentExpense, invalid expense error: %s", e)
        return (
            jsonify({"message": get_message(MESSAGES, "invalid_expense_data")}),
            500,
        )

    except OperationalError as e:
        db_session.rollback()
        logger.error("insert table ShipmentExpense, connection error: %s", e)

        return (
            jsonify(
                {
                    "message": get_message(MESSAGES, "add_expense_error")
                    + ": "
                    + get_message(MESSAGES, "connection_error")
                }
            ),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("insert table ShipmentExpense, error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "add_expense_error")}), 500


@shipment_expense_bp.route("/api/shipment-expense/<int:expense_code>", methods=["PUT"])
@token_required
def put_shipment_expense(expense_code: int) -> Tuple[Response, int]:
    try:
        # get entry to update
        stmt = select(ShipmentExpense).where(
            ShipmentExpense.expense_code == expense_code,
            ShipmentExpense.modification_user == request.current_user.user_id,
        )
        entry_to_update: Optional[ShipmentExpense] = db_session.scalar(stmt)

        if entry_to_update is None:
            logger.error("update table ShipmentExpense, expense not found")
            return jsonify({"message": get_message(MESSAGES, "expense_not_found")}), 404

        # json to db object
        payload = ShipmentExpense(
            **{**request.get_json(), "modification_user": request.current_user.user_id}
        )

        # Verify driver payroll exists
        stmt = select(DriverPayroll).where(
            DriverPayroll.payroll_code == payload.driver_payroll_code,
            DriverPayroll.modification_user == request.current_user.user_id,
        )
        existing_payroll: Optional[DriverPayroll] = db_session.scalar(stmt)
        if existing_payroll is None:
            logger.error("update table ShipmentExpense, driver payroll not found")
            return jsonify({"message": get_message(MESSAGES, "payroll_not_found")}), 404

        entry_to_update.expense_date = payload.expense_date
        entry_to_update.receipt = payload.receipt
        entry_to_update.amount = payload.amount
        entry_to_update.reason = payload.reason
        entry_to_update.deleted = payload.deleted
        entry_to_update.driver_payroll_code = payload.driver_payroll_code
        entry_to_update.modification_user = payload.modification_user

        logger.info("update table ShipmentExpense, payload: %s", entry_to_update)

        db_session.commit()
        logger.info("updated table ShipmentExpense, expense: %s", expense_code)
        return (
            jsonify(
                {
                    **asdict(entry_to_update),
                    "message": get_message(MESSAGES, "expense_updated"),
                }
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("invalid expense: %s", e)
        return (
            jsonify({"message": get_message(MESSAGES, "invalid_expense_data")}),
            500,
        )

    except OperationalError as e:
        db_session.rollback()
        logger.error("update table ShipmentExpense: connection error %s", e)

        return (
            jsonify(
                {
                    "message": get_message(MESSAGES, "update_expense_error")
                    + ": "
                    + get_message(MESSAGES, "connection_error")
                }
            ),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("update table ShipmentExpense, error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "update_expense_error")}), 500


@shipment_expense_bp.route("/api/shipment-expenses/change-driver-payroll", methods=["PATCH"])
@token_required
def shipment_expenses_change_driver_payroll() -> Tuple[Response, int]:
    driver_payroll_code_param: str | None = request.args.get("driver_payroll_code")
    driver_payroll_code = None

    # If driver_payroll_code_param is provided, validate it
    if driver_payroll_code_param:
        try:
            driver_payroll_code = int(driver_payroll_code_param)

            # Validate that the driver_payroll exists in the database
            stmt_driver_payroll = select(DriverPayroll).where(
                DriverPayroll.payroll_code == driver_payroll_code_param,
                DriverPayroll.deleted == False,
                DriverPayroll.modification_user == request.current_user.user_id,
            )

            driver_payroll = db_session.scalar(stmt_driver_payroll)
            if not driver_payroll:
                logger.error(
                    "DriverPayroll with code %s not found", driver_payroll_code
                )
                return (
                    jsonify({"message": get_message(MESSAGES, "payroll_not_found")}),
                    404,
                )

        except ValueError:
            logger.error("Invalid 'driver_payroll_code' parameter: not an integer")
            return (
                jsonify(
                    {"message": get_message(MESSAGES, "invalid_payroll_code_param")}
                ),
                400,
            )

    try:
        # Get payload from request
        shipment_expenses_codes = request.get_json()

        # Validate payload
        if not shipment_expenses_codes or not isinstance(shipment_expenses_codes, list):
            return jsonify({"message": get_message(MESSAGES, "invalid_payload")}), 400

        # Find all shipment expenses that belong to the current user
        stmt = select(ShipmentExpense).where(
            ShipmentExpense.expense_code.in_(shipment_expenses_codes),
            ShipmentExpense.modification_user == request.current_user.user_id,
        )
        shipment_expenses_to_update = db_session.scalars(stmt).all()

        if not shipment_expenses_to_update:
            logger.error("move shipment expenses, no expenses found")
            return (
                jsonify(
                    {"message": get_message(MESSAGES, "expenses_not_found_to_update")}
                ),
                404,
            )

        # Track successfully updated shipment expenses
        updated_shipment_expense_codes = []

        # Update driver_payroll_code for each shipment expenses
        for shipment_expense in shipment_expenses_to_update:
            shipment_expense.driver_payroll_code = driver_payroll_code
            shipment_expense.modification_user = request.current_user.user_id
            updated_shipment_expense_codes.append(shipment_expense.expense_code)

        db_session.commit()

        logger.info(
            "Updated driver_payroll_code to %s for shipment expenses: %s",
            driver_payroll_code,
            updated_shipment_expense_codes,
        )

        return (
            jsonify(
                {
                    "message": get_message(MESSAGES, "expenses_updated"),
                }
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("move shipment expenses, invalid data error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "invalid_expense_data")}), 400

    except OperationalError as e:
        db_session.rollback()
        logger.error("move shipment expenses, connection error: %s", e)
        return (
            jsonify(
                {
                    "message": get_message(MESSAGES, "update_expenses_error")
                    + ": "
                    + get_message(MESSAGES, "connection_error")
                }
            ),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("move shipment expenses, database error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "update_expenses_error")}), 500


@shipment_expense_bp.route("/api/shipment-expense/<int:expense_code>", methods=["DELETE"])
@token_required
def delete_shipment_expense(expense_code: int) -> Tuple[Response, int]:
    try:
        stmt = select(ShipmentExpense).where(
            ShipmentExpense.expense_code == expense_code,
            ShipmentExpense.modification_user == request.current_user.user_id,
        )
        existing_entry: Optional[ShipmentExpense] = db_session.scalar(stmt)

        if existing_entry is None:
            logger.error("delete table ShipmentExpense, expense not found")
            return jsonify({"message": get_message(MESSAGES, "expense_not_found")}), 404

        existing_entry.deleted = True
        existing_entry.modification_user = request.current_user.user_id
        db_session.commit()
        logger.info("delete table ShipmentExpense: expense %s", expense_code)
        return jsonify({"message": get_message(MESSAGES, "expense_deleted")}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table ShipmentExpense, connection error: %s", e)
        return (
            jsonify(
                {
                    "message": get_message(MESSAGES, "delete_expense_error")
                    + ": "
                    + get_message(MESSAGES, "connection_error")
                }
            ),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table ShipmentExpense, error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "delete_expense_error")}), 500


@shipment_expense_bp.route("/api/shipment-expenses", methods=["DELETE"])
@token_required
def delete_shipment_expenses() -> Tuple[Response, int]:
    if (request.data is None) or (not request.is_json):
        logger.error("delete expenses table ShipmentExpense, expense list is empty")
        return (
            jsonify(
                {
                    "message": get_message(MESSAGES, "delete_expense_error")
                    + ": "
                    + get_message(MESSAGES, "empty_expense_list")
                }
            ),
            404,
        )

    expense_list: List[int] = request.get_json()
    logger.debug("delete expenses table ShipmentExpense, payload: %s", expense_list)

    try:
        for expense_code in expense_list:
            stmt = select(ShipmentExpense).where(
                ShipmentExpense.expense_code == expense_code,
                ShipmentExpense.modification_user == request.current_user.user_id,
            )
            expense: Optional[ShipmentExpense] = db_session.scalar(stmt)

            if expense is None:
                return (
                    jsonify(
                        {
                            "message": get_message(MESSAGES, "delete_expense_error")
                            + ": "
                            + get_message(MESSAGES, "expenses_not_found")
                        }
                    ),
                    404,
                )

            expense.deleted = True
            expense.modification_user = request.current_user.user_id
            logger.info("delete table ShipmentExpense, expense: %s", expense_code)

        db_session.commit()
        return jsonify({"message": get_message(MESSAGES, "expenses_deleted")}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table ShipmentExpense: connection error %s", e)
        return (
            jsonify(
                {
                    "message": get_message(MESSAGES, "delete_expense_error")
                    + ": "
                    + get_message(MESSAGES, "connection_error")
                }
            ),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table ShipmentExpense, error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "delete_expense_error")}), 500
