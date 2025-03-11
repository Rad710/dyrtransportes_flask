from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import List

from dataclasses import asdict

from flask import request
from flask import jsonify
from flask import Response

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import OperationalError

from app_config import logger
from app_config import app
from app_config import db_session
from app_config import RequestWithUser

from decorators.token_required import token_required

from models.driver_payroll import DriverPayroll
from models.shipment_expense import ShipmentExpense

request: RequestWithUser


@app.route("/api/shipment-expense/<int:expense_code>", methods=["GET"])
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
            return jsonify({"message": "No se encontró el gasto"}), 404

        logger.info(
            "fetch table ShipmentExpense, found: %s", shipment_expense.expense_code
        )
        logger.debug("fetch table ShipmentExpense, found: %s", shipment_expense)

        return jsonify(shipment_expense), 200

    except SQLAlchemyError as e:
        logger.error("fetch table ShipmentExpense, error: %s", e)
        return jsonify({"message": "Error de transacción"}), 500


@app.route("/api/shipment-expenses", methods=["GET"])
@token_required
def get_shipment_expense_list(payroll_code: int) -> Tuple[Response, int]:
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
                return jsonify({"message": "Planilla de carga no encontrada"}), 404

        except ValueError:
            logger.error("Invalid 'driver_payroll_code' parameter: not an integer")
            return (
                jsonify(
                    {
                        "message": "Parámetro 'driver_payroll_code' debe ser un número entero"
                    }
                ),
                400,
            )

    try:
        shipment_expenses_stmt = select(ShipmentExpense).where(
            ShipmentExpense.deleted == False,
            ShipmentExpense.modification_user == request.current_user.user_id,
            ShipmentExpense.driver_payroll_code == payroll_code,
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
        return jsonify({"message": "Error al obtener gastos"}), 500


@app.route("/api/shipment-expense", methods=["POST"])
@token_required
def post_shipment_expense() -> Tuple[Response, int]:
    try:
        # json to db object
        payload = ShipmentExpense(
            **request.get_json(), modification_user=request.current_user.user_id
        )

        # Verify driver payroll exists
        stmt = select(DriverPayroll).where(
            DriverPayroll.payroll_code == payload.driver_payroll_code,
            DriverPayroll.modification_user == request.current_user.user_id,
        )
        existing_payroll: Optional[DriverPayroll] = db_session.scalar(stmt)
        if existing_payroll is None:
            logger.error("insert table ShipmentExpense, driver payroll not found")
            return jsonify({"message": "Liquidación no encontrada"}), 404

        # add to database
        logger.debug("insert table ShipmentExpense, payload: %s", payload)
        db_session.add(payload)

        db_session.commit()
        logger.info("inserted table ShipmentExpense, expense: %s", payload.expense_code)
        return (
            jsonify({**asdict(payload), "message": "Gasto agregado exitosamente"}),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("insert table ShipmentExpense, invalid expense error: %s", e)
        return (
            jsonify({"message": f"Error, datos del Gasto inválidos ({e})"}),
            500,
        )

    except OperationalError as e:
        db_session.rollback()
        logger.error("insert table ShipmentExpense, connection error: %s", e)

        return (
            jsonify({"message": "Error al agregar gasto: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("insert table ShipmentExpense, error: %s", e)
        return jsonify({"message": "Error al agregar gasto"}), 500


@app.route("/api/shipment-expense/<int:expense_code>", methods=["PUT"])
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
            return jsonify({"message": "Gasto no encontrado"}), 404

        # json to db object
        payload = ShipmentExpense(
            **request.get_json(), modification_user=request.current_user.user_id
        )

        # Verify driver payroll exists
        stmt = select(DriverPayroll).where(
            DriverPayroll.payroll_code == payload.driver_payroll_code,
            DriverPayroll.modification_user == request.current_user.user_id,
        )
        existing_payroll: Optional[DriverPayroll] = db_session.scalar(stmt)
        if existing_payroll is None:
            logger.error("update table ShipmentExpense, driver payroll not found")
            return jsonify({"message": "Liquidación no encontrada"}), 404

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
                    "message": "Gasto actualizado exitosamente",
                }
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("invalid expense: %s", e)
        return (
            jsonify({"message": f"Error, datos del Gasto inválidos ({e})"}),
            500,
        )

    except OperationalError as e:
        db_session.rollback()
        logger.error("update table ShipmentExpense: connection error %s", e)

        return (
            jsonify({"message": "Error al actualizar gasto: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("update table ShipmentExpense, error: %s", e)
        return jsonify({"message": "Error al actualizar gasto"}), 500


@app.route("/api/shipment-expense/<int:expense_code>", methods=["DELETE"])
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
            return jsonify({"message": "Gasto no encontrado"}), 404

        existing_entry.deleted = True
        existing_entry.modification_user = request.current_user.user_id
        db_session.commit()
        logger.info("delete table ShipmentExpense: expense %s", expense_code)
        return jsonify({"message": "Gasto eliminado exitosamente"}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table ShipmentExpense, connection error: %s", e)
        return (
            jsonify({"message": "Error al eliminar gasto: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table ShipmentExpense, error: %s", e)
        return jsonify({"message": "Error al eliminar gasto"}), 500


@app.route("/api/shipment-expenses", methods=["DELETE"])
@token_required
def delete_shipment_expenses() -> Tuple[Response, int]:
    if (request.data is None) or (not request.is_json):
        logger.error("delete expenses table ShipmentExpense, expense list is empty")
        return (
            jsonify({"message": "Error al eliminar gastos: lista de gastos vacía"}),
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
                        {"message": "Error al eliminar gastos: gasto no encontrado"}
                    ),
                    404,
                )

            expense.deleted = True
            expense.modification_user = request.current_user.user_id
            logger.info("delete table ShipmentExpense, expense: %s", expense_code)

        db_session.commit()
        return jsonify({"message": "Gastos eliminados exitosamente"}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table ShipmentExpense: connection error %s", e)
        return (
            jsonify({"message": "Error al eliminar gastos: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table ShipmentExpense, error: %s", e)
        return jsonify({"message": "Error al eliminar gastos"}), 500
