import io
from datetime import datetime
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import List
from typing import Any

from dataclasses import asdict

from flask import request
from flask import jsonify
from flask import Response
from flask import make_response

from sqlalchemy import select
from sqlalchemy import desc
from sqlalchemy import cast
from sqlalchemy import Date
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import OperationalError

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles import Border
from openpyxl.styles import Side
from openpyxl.styles import Alignment
from openpyxl.styles import Font
from openpyxl.styles import numbers
from openpyxl.utils import get_column_letter

from app_config import logger
from app_config import app
from app_config import db_session
from app_config import RequestWithUser

from decorators.token_required import token_required

from models.driver_payroll import DriverPayroll
from models.driver import Driver
from models.shipment import Shipment
from models.shipment_expense import ShipmentExpense

request: RequestWithUser


@app.route("/api/driver-payroll/<int:payroll_code>", methods=["GET"])
@token_required
def get_driver_payroll(payroll_code: int) -> Tuple[Response, int]:
    try:
        stmt = select(DriverPayroll).where(
            DriverPayroll.payroll_code == payroll_code,
            DriverPayroll.deleted == False,
            DriverPayroll.modification_user == request.current_user.user_id,
        )

        driver_payroll: Optional[DriverPayroll] = db_session.scalar(stmt)
        if driver_payroll is None:
            logger.error("fetch table DriverPayroll, not found")
            return jsonify({"message": "No se encontró la liquidación"}), 404

        logger.info("fetch table DriverPayroll, found: %s", driver_payroll.payroll_code)
        logger.debug("fetch table DriverPayroll, found: %s", driver_payroll)

        return jsonify(driver_payroll), 200

    except SQLAlchemyError as e:
        logger.error("fetch table DriverPayroll, error: %s", e)
        return jsonify({"message": "Error de transacción"}), 500


@app.route("/api/driver/<int:driver_code>/payrolls", methods=["GET"])
@token_required
def get_driver_payrolls_by_driver(driver_code: int) -> Tuple[Response, int]:
    try:
        # Verify driver exists
        driver_stmt = select(Driver).where(
            Driver.driver_code == driver_code,
            Driver.modification_user == request.current_user.user_id,
        )
        existing_driver: Optional[Driver] = db_session.scalar(driver_stmt)
        if existing_driver is None:
            logger.error("get driver payrolls, driver not found")
            return jsonify({"message": "Chofer no encontrado"}), 404

        # Get payrolls for this driver
        stmt = (
            select(DriverPayroll)
            .where(
                DriverPayroll.driver_code == driver_code,
                DriverPayroll.modification_user == request.current_user.user_id,
                DriverPayroll.deleted == False,
            )
            .order_by(
                desc(DriverPayroll.payroll_timestamp), desc(DriverPayroll.payroll_code)
            )
        )

        payrolls: Sequence[DriverPayroll] = db_session.scalars(stmt).all()
        logger.info(
            "fetch driver payrolls, driver: %s, len: %s", driver_code, len(payrolls)
        )
        logger.debug("fetch driver payrolls, payrolls: %s", payrolls)

        return jsonify(payrolls), 200

    except SQLAlchemyError as e:
        logger.error("fetch driver payrolls, error: %s", e)
        return jsonify({"message": "Error al obtener liquidaciones del chofer"}), 500


# TODO: combine into endpoint of shipments.py
@app.route("/api/driver-payroll/<int:payroll_code>/shipments", methods=["GET"])
@token_required
def get_driver_payroll_shipments(payroll_code: int) -> Tuple[Response, int]:
    try:
        driver_payroll_stmt = select(DriverPayroll).where(
            DriverPayroll.payroll_code == payroll_code,
            DriverPayroll.modification_user == request.current_user.user_id,
            DriverPayroll.deleted == False,
        )

        driver_payroll: Optional[DriverPayroll] = db_session.scalar(driver_payroll_stmt)
        if driver_payroll is None:
            logger.error("fetch table DriverPayroll, not found")
            return jsonify({"message": "No se encontró la liquidación"}), 404

        logger.info("fetch table DriverPayroll, found: %s", driver_payroll.payroll_code)
        logger.debug("fetch table DriverPayroll, found: %s", driver_payroll)

        shipments_stmt = select(Shipment).where(
            Shipment.deleted == False,
            Shipment.modification_user == request.current_user.user_id,
            Shipment.driver_payroll_code == payroll_code,
        )

        shipments: Sequence[Shipment] = db_session.scalars(shipments_stmt).all()
        logger.info("fetch shipments table Shipment, len: %s", len(shipments))
        logger.debug("fetch shipments table Shipment, shipments: %s", shipments)
        return jsonify(shipments), 200

    except SQLAlchemyError as e:
        logger.error("fetch shipments table Shipment, error: %s", e)
        return jsonify({"message": "Error al obtener planillas"}), 500


@app.route("/api/driver-payroll/<int:payroll_code>/paid-status", methods=["PATCH"])
@token_required
def update_driver_payroll_paid_status(
    payroll_code: int,
) -> Tuple[Response, int]:
    try:
        # Get the entry to update
        stmt = select(DriverPayroll).where(
            DriverPayroll.payroll_code == payroll_code,
            DriverPayroll.modification_user == request.current_user.user_id,
        )
        entry_to_update: Optional[DriverPayroll] = db_session.scalar(stmt)

        if entry_to_update is None:
            logger.error(
                "update payroll paid status, DriverPayroll not found: %s", payroll_code
            )
            return jsonify({"message": "Liquidación no encontrada"}), 404

        # Get the payload
        payload = request.get_json()

        if "paid" not in payload:
            logger.error("update paid status, missing paid field")
            return jsonify({"message": "Campo 'paid' requerido"}), 400

        entry_to_update.paid = payload["paid"]

        # Update paid_timestamp if status is set to paid
        if payload["paid"]:
            entry_to_update.paid_timestamp = datetime.now()
        else:
            entry_to_update.paid_timestamp = None

        entry_to_update.modification_user = request.current_user.user_id

        logger.info(
            "update paid status, DriverPayroll: %s, status: %s",
            payroll_code,
            "paid" if entry_to_update.paid else "unpaid",
        )

        db_session.commit()

        return (
            jsonify(
                {
                    **asdict(entry_to_update),
                    "message": f"Estado de Liquidación a {'pagado' if entry_to_update.paid else 'no pagado'}",
                }
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("invalid paid status update: %s", e)
        return jsonify({"message": f"Error, datos inválidos ({e})"}), 400

    except OperationalError as e:
        db_session.rollback()
        logger.error("update paid status: connection error %s", e)
        return (
            jsonify(
                {"message": "Error al actualizar estado de pago: problema de conexión"}
            ),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("update paid status, error: %s", e)
        return jsonify({"message": "Error al actualizar estado de pago"}), 500


@app.route("/api/driver-payroll", methods=["POST"])
@token_required
def post_driver_payroll() -> Tuple[Response, int]:
    try:
        # json to db object
        payload = DriverPayroll(
            **request.get_json(), modification_user=request.current_user.user_id
        )

        # Verify driver exists
        stmt = select(Driver).where(
            Driver.driver_code == payload.driver_code,
            Driver.modification_user == request.current_user.user_id,
        )
        existing_driver: Optional[Driver] = db_session.scalar(stmt)
        if existing_driver is None:
            logger.error("insert table DriverPayroll, driver not found")
            return jsonify({"message": "Chofer no encontrado"}), 404

        # add to database
        logger.debug("insert table DriverPayroll, payload: %s", payload)
        db_session.add(payload)

        db_session.commit()
        logger.info("inserted table DriverPayroll, payroll: %s", payload.payroll_code)
        return (
            jsonify(
                {**asdict(payload), "message": "Liquidación agregada exitosamente"}
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("insert table DriverPayroll, invalid payroll error: %s", e)
        return (
            jsonify({"message": f"Error, datos de la Liquidación inválidos ({e})"}),
            500,
        )

    except OperationalError as e:
        db_session.rollback()
        logger.error("insert table DriverPayroll, connection error: %s", e)

        return (
            jsonify({"message": "Error al agregar liquidación: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("insert table DriverPayroll, error: %s", e)
        return jsonify({"message": "Error al agregar liquidación"}), 500


@app.route("/api/driver-payroll/<int:payroll_code>", methods=["PUT"])
@token_required
def put_driver_payroll(payroll_code: int) -> Tuple[Response, int]:
    try:
        # get entry to update
        stmt = select(DriverPayroll).where(
            DriverPayroll.payroll_code == payroll_code,
            DriverPayroll.modification_user == request.current_user.user_id,
        )
        entry_to_update: Optional[DriverPayroll] = db_session.scalar(stmt)

        if entry_to_update is None:
            logger.error("update table DriverPayroll, payroll not found")
            return jsonify({"message": "Liquidación no encontrada"}), 404

        # json to db object
        payload = DriverPayroll(
            **request.get_json(), modification_user=request.current_user.user_id
        )

        # Verify driver exists
        stmt = select(Driver).where(
            Driver.driver_code == payload.driver_code,
            Driver.modification_user == request.current_user.user_id,
        )
        existing_driver: Optional[Driver] = db_session.scalar(stmt)
        if existing_driver is None:
            logger.error("update table DriverPayroll, driver not found")
            return jsonify({"message": "Chofer no encontrado"}), 404

        entry_to_update.driver_code = payload.driver_code
        entry_to_update.modification_user = payload.modification_user

        logger.info("update table DriverPayroll, payload: %s", entry_to_update)

        db_session.commit()
        logger.info("updated table DriverPayroll, payroll: %s", payroll_code)
        return (
            jsonify(
                {
                    **asdict(entry_to_update),
                    "message": "Liquidación actualizada exitosamente",
                }
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("invalid payroll: %s", e)
        return (
            jsonify({"message": f"Error, datos de la Liquidación inválidos ({e})"}),
            500,
        )

    except OperationalError as e:
        db_session.rollback()
        logger.error("update table DriverPayroll: connection error %s", e)

        return (
            jsonify(
                {"message": "Error al actualizar liquidación: problema de conexión"}
            ),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("update table DriverPayroll, error: %s", e)
        return jsonify({"message": "Error al actualizar liquidación"}), 500


# TODO: combine into shipment.py endpoint
@app.route("/api/shipments/change-driver-payroll", methods=["PATCH"])
@token_required
def shipments_change_driver_payroll() -> Tuple[Response, int]:
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
        # Get payload from request
        shipment_codes = request.get_json()

        # Validate payload
        if not shipment_codes or not isinstance(shipment_codes, list):
            return jsonify({"message": "Payload inválido"}), 400

        # Find all shipments that belong to the current user
        stmt = select(Shipment).where(
            Shipment.shipment_code.in_(shipment_codes),
            Shipment.modification_user == request.current_user.user_id,
        )
        shipments_to_update = db_session.scalars(stmt).all()

        if not shipments_to_update:
            logger.error("move shipments, no shipments found")
            return jsonify({"message": "No se encontraron cargas para actualizar"}), 404

        # Track successfully updated shipments
        updated_shipment_codes = []

        # Update driver_payroll_code for each shipment
        for shipment in shipments_to_update:
            shipment.driver_payroll_code = driver_payroll_code
            shipment.modification_user = request.current_user.user_id
            updated_shipment_codes.append(shipment.shipment_code)

        db_session.commit()

        logger.info(
            "Updated driver_payroll_code to %s for shipments: %s",
            driver_payroll_code,
            updated_shipment_codes,
        )

        return (
            jsonify(
                {
                    "message": "Cargas actualizadas exitosamente",
                }
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("move shipments, invalid data error: %s", e)
        return jsonify({"message": f"Error, datos inválidos ({e})"}), 400

    except OperationalError as e:
        db_session.rollback()
        logger.error("move shipments, connection error: %s", e)
        return (
            jsonify({"message": "Error al actualizar cargas: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("move shipments, database error: %s", e)
        return jsonify({"message": "Error al actualizar cargas"}), 500


@app.route("/api/driver-payroll/<int:payroll_code>", methods=["DELETE"])
@token_required
def delete_driver_payroll(payroll_code: int) -> Tuple[Response, int]:
    try:
        stmt = select(DriverPayroll).where(
            DriverPayroll.payroll_code == payroll_code,
            DriverPayroll.modification_user == request.current_user.user_id,
        )
        existing_entry: Optional[DriverPayroll] = db_session.scalar(stmt)

        if existing_entry is None:
            logger.error("delete table DriverPayroll, payroll not found")
            return jsonify({"message": "Liquidación no encontrada"}), 404

        existing_entry.deleted = True
        existing_entry.modification_user = request.current_user.user_id
        db_session.commit()
        logger.info("delete table DriverPayroll: payroll %s", payroll_code)
        return jsonify({"message": "Liquidación eliminada exitosamente"}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table DriverPayroll, connection error: %s", e)
        return (
            jsonify({"message": "Error al eliminar liquidación: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table DriverPayroll, error: %s", e)
        return jsonify({"message": "Error al eliminar liquidación"}), 500


@app.route("/api/driver-payrolls", methods=["DELETE"])
@token_required
def delete_driver_payrolls() -> Tuple[Response, int]:
    if (request.data is None) or (not request.is_json):
        logger.error("delete payrolls table DriverPayroll, payroll list is empty")
        return (
            jsonify(
                {"message": "Error al eliminar liquidación: liquidación no encontrada"}
            ),
            404,
        )

    payroll_list: List[int] = request.get_json()
    logger.debug("delete payrolls table DriverPayroll, payload: %s", payroll_list)

    try:
        for payroll_code in payroll_list:
            stmt = select(DriverPayroll).where(
                DriverPayroll.payroll_code == payroll_code,
                DriverPayroll.modification_user == request.current_user.user_id,
            )
            payroll: Optional[DriverPayroll] = db_session.scalar(stmt)

            if payroll is None:
                return (
                    jsonify(
                        {
                            "message": "Error al eliminar liquidación: liquidación no encontrada"
                        }
                    ),
                    404,
                )

            payroll.deleted = True
            payroll.modification_user = request.current_user.user_id
            logger.info("delete table DriverPayroll, payroll: %s", payroll_code)

        db_session.commit()
        return jsonify({"message": "Liquidación eliminada exitosamente"}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table DriverPayroll: connection error %s", e)
        return (
            jsonify({"message": "Error al eliminar liquidación: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table DriverPayroll, error: %s", e)
        return jsonify({"message": "Error al eliminar liquidación"}), 500


# TODO: IMPLEMENT
@app.route("/api/driver-payrolls/export-excel", methods=["GET"])
@token_required
def export_driver_payrolls() -> Tuple[Response, int]:
    # Get date range parameters
    driver_code_str = request.args.get("driver_code", "")
    start_date_str = request.args.get("start_date", "")
    end_date_str = request.args.get("end_date", "")

    try:
        # Convert date parameters as needed
        driver_code = int(driver_code_str) if driver_code_str else None
        start_date = datetime.fromisoformat(start_date_str) if start_date_str else None
        end_date = datetime.fromisoformat(end_date_str) if end_date_str else None

        # Build query for shipment payrolls in date range
        stmt = select(DriverPayroll).where(
            DriverPayroll.deleted == False,
            DriverPayroll.modification_user == request.current_user.user_id,
        )

        if driver_code:
            stmt = stmt.where(DriverPayroll.driver_code == driver_code)
        if start_date:
            stmt = stmt.where(
                cast(DriverPayroll.payroll_timestamp, Date) >= start_date.date()
            )
        if end_date:
            stmt = stmt.where(
                cast(DriverPayroll.payroll_timestamp, Date) <= end_date.date()
            )

        stmt = stmt.order_by(
            desc(DriverPayroll.payroll_timestamp), desc(DriverPayroll.payroll_code)
        )

        payroll_list: Sequence[DriverPayroll] = db_session.scalars(stmt).all()

        if not payroll_list:
            logger.warning("export DriverPayroll, no data found in date range")
            return (
                jsonify(
                    {
                        "message": "No hay datos para exportar en el rango de fechas seleccionado"
                    }
                ),
                404,
            )

        # Create file
        output = io.BytesIO()
        workbook = Workbook(write_only=False, iso_dates=False)
        sheet = workbook.active

        headers = ["Código", "Fecha", "Cobrado", "Fecha de Cobro"]
        sheet.append(headers)

        for col_idx in range(1, 5):
            sheet.column_dimensions[get_column_letter(col_idx)].width = 20

        # Border style
        border_style = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        # Apply border style to each cell in the header row
        for cell in sheet[sheet.max_row]:
            cell.border = border_style

        # Add data rows
        for payroll in payroll_list:
            # Format dates for display
            payroll_date = (
                payroll.payroll_timestamp.strftime("%d/%m/%Y")
                if payroll.payroll_timestamp
                else ""
            )
            paid_date = (
                payroll.paid_timestamp.strftime("%d/%m/%Y")
                if payroll.paid_timestamp
                else ""
            )

            row = [
                payroll.payroll_code,
                payroll_date,
                "Sí" if payroll.paid else "No",
                paid_date,
            ]

            sheet.append(row)

            # Apply border style to each cell in the data row
            for cell in sheet[sheet.max_row]:
                cell.border = border_style

        # Save Excel file to output stream
        workbook.save(output)
        output.seek(0)

        # Create response with Excel file
        response = make_response(output.getvalue())
        response.headers["Content-Type"] = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response.headers["Content-Disposition"] = (
            'attachment; filename="lista_de_planillas.xlsx"'
        )

        logger.info("exported ShipmentPayrolls excel file")

        return response, 200

    except ValueError as e:
        logger.error("export ShipmentPayrolls, invalid date format: %s", e)
        return jsonify({"message": "Formato de fecha inválido"}), 400

    except SQLAlchemyError as e:
        logger.error("export ShipmentPayrolls, database error: %s", e)
        return jsonify({"message": "Error al generar el archivo de exportación"}), 500

    except Exception as e:
        logger.error("export ShipmentPayrolls, unexpected error: %s", e)
        return jsonify({"message": "Error al generar el archivo de exportación"}), 500


@app.route(
    "/api/driver-payroll/export-excel/<int:driver_payroll_code>", methods=["GET"]
)
@token_required
def exportar_liquidacion(driver_payroll_code: int):
    try:
        driver_payroll_stmt = select(DriverPayroll).where(
            DriverPayroll.payroll_code == driver_payroll_code,
            DriverPayroll.deleted == False,
            DriverPayroll.modification_user == request.current_user.user_id,
        )
        driver_payroll: Optional[DriverPayroll] = db_session.scalar(driver_payroll_stmt)
        if driver_payroll is None:
            logger.error("fetch table DriverPayroll, not found")
            return jsonify({"message": "No se encontró la liquidación"}), 404

        logger.info("fetch table DriverPayroll, found: %s", driver_payroll.payroll_code)
        logger.debug("fetch table DriverPayroll, found: %s", driver_payroll)

        driver_stmt = select(Driver).where(
            Driver.driver_code == driver_payroll.driver_code,
            Driver.deleted == False,
            Driver.modification_user == request.current_user.user_id,
        )
        driver: Optional[Driver] = db_session.scalar(driver_stmt)
        if driver is None:
            logger.error("fetch table Driver, not found")
            return jsonify({"message": "No se encontró al chofer"}), 404

        logger.debug("fetch table Driver, found: %s", driver)

        shipments_stmt = select(Shipment).where(
            Shipment.driver_payroll_code == driver_payroll_code,
            Shipment.deleted == False,
            Shipment.modification_user == request.current_user.user_id,
        )
        shipments: Sequence[Shipment] = db_session.scalars(shipments_stmt).all()

        shipment_expenses_no_receipt_stmt = select(ShipmentExpense).where(
            ShipmentExpense.driver_payroll_code == driver_payroll_code,
            ShipmentExpense.deleted == False,
            ShipmentExpense.receipt == None,
            ShipmentExpense.modification_user == request.current_user.user_id,
        )
        shipment_expenses_no_receipt: Sequence[ShipmentExpense] = db_session.scalars(
            shipment_expenses_no_receipt_stmt
        ).all()

        shipment_expenses_receipt_stmt = select(ShipmentExpense).where(
            ShipmentExpense.driver_payroll_code == driver_payroll_code,
            ShipmentExpense.deleted == False,
            ShipmentExpense.receipt != None,
            ShipmentExpense.modification_user == request.current_user.user_id,
        )
        shipment_expenses_receipt: Sequence[ShipmentExpense] = db_session.scalars(
            shipment_expenses_receipt_stmt
        ).all()

    except SQLAlchemyError as e:
        logger.error("fetch table DriverPayroll, error: %s", e)
        return jsonify({"message": "Error de transacción"}), 500

    max_len = max(
        len(shipments),
        len(shipment_expenses_no_receipt),
        len(shipment_expenses_receipt),
    )

    # Rellenar las listas para que tengan la misma longitud con None si es necesario
    shipments += [None] * (max_len - len(shipments))
    shipment_expenses_no_receipt += [None] * (
        max_len - len(shipment_expenses_no_receipt)
    )
    shipment_expenses_receipt += [None] * (max_len - len(shipment_expenses_receipt))

    # Combinar las tres listas en una lista de tuplas usando zip
    results = zip(shipments, shipment_expenses_no_receipt, shipment_expenses_receipt)

    # Crear un archivo Excel en memoria
    output = io.BytesIO()
    workbook = Workbook()
    sheet = workbook.active

    # define columns
    columns: dict[str, dict[str, Any]] = {
        "code": {"letter": "A", "number": 1},
        "shipment_date": {"letter": "B", "number": 2},
        "product": {"letter": "C", "number": 3},
        "ticket_number": {"letter": "D", "number": 4},
        "origin": {"letter": "E", "number": 5},
        "destination": {"letter": "F", "number": 6},
        "origin_weight": {"letter": "G", "number": 7},
        "destination_weight": {"letter": "H", "number": 8},
        "difference": {"letter": "I", "number": 9},
        "price_weight": {"letter": "J", "number": 10},
        "shipment_amount": {"letter": "K", "number": 11},
        "untaxed_expense_date": {"letter": "L", "number": 12},
        "untaxed_espense_reason": {"letter": "M", "number": 13},
        "untaxed_expense_amount": {"letter": "N", "number": 14},
        "taxed_expense_date": {"letter": "O", "number": 15},
        "taxed_expense_receipt": {"letter": "P", "number": 16},
        "taxed_expense_reason": {"letter": "Q", "number": 17},
        "taxed_expense_amount": {"letter": "R", "number": 18},
    }

    columns_length = len(columns)

    # style
    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    render_driver_payroll_headers(sheet, columns, driver, border)
    render_driver_payroll_shipment_expense(sheet, columns, results, border)
    last_row = 5 + max_len

    untaxed_expense_amount_column = columns["untaxed_expense_amount"]["letter"]
    taxed_expense_amount_column = columns["taxed_expense_amount"]["letter"]

    # Subtotals
    subtotal_sin_boleta = f"=SUM(${untaxed_expense_amount_column}6:${untaxed_expense_amount_column}{last_row})"
    subtotal_con_boleta = f"=SUM(${taxed_expense_amount_column}6:${taxed_expense_amount_column}{last_row})"
    subtotales = [
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        "Subtotal",
        None,
        subtotal_sin_boleta,
        "Subtotal",
        None,
        None,
        subtotal_con_boleta,
    ]
    sheet.append(subtotales)

    for col in range(1, columns_length + 1):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.border = border
        cell.font = Font(bold=True)

    for col in [columns["untaxed_expense_date"]["number"], columns_length]:
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.number_format = "#,##0"
        cell.border = border

    shipment_amount_column = columns["shipment_amount"]["letter"]
    untaxed_expense_amount_column = columns["untaxed_expense_amount"]["letter"]
    taxed_expense_amount_column = columns["taxed_expense_amount"]["letter"]

    # TOTAL SHIPMENT-EXPENSE
    total_gastos = f"=+${untaxed_expense_amount_column}{last_row + 1}+${taxed_expense_amount_column}{last_row + 1}"
    subtotal_viajes = (
        f"=SUM(${shipment_amount_column}6:${shipment_amount_column}{last_row})"
    )
    total = [
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        "TOTAL FLETES:",
        None,
        subtotal_viajes,
        "TOTAL GASTOS:",
        None,
        None,
        None,
        None,
        None,
        total_gastos,
    ]
    sheet.append(total)

    for col in [columns["shipment_amount"]["number"], len(columns)]:
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.number_format = "#,##0"
        cell.border = border

    for col in range(1, len(columns) + 1):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.border = border
        cell.font = Font(bold=True)

    sheet.append([None])

    render_driver_payroll_totals(sheet, columns, border, last_row)

    # Save and send Excel file
    workbook.save(output)
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    name = (driver.driver_name or "") + " " + (driver.driver_surname or "")
    date = driver_payroll.payroll_timestamp.date().strftime("%d/%m/%Y")

    response.headers["Content-Disposition"] = (
        f"attachment; filename={name.strip()}_Liquidacion_{date}.xlsx"
    )
    logger.info(
        "Liquidacion %s %s exportada", driver.driver_code, driver_payroll.payroll_code
    )
    return response


def render_driver_payroll_headers(
    sheet: Worksheet,
    columns: dict[str, dict[str, Any]],
    driver: Driver,
    border: Border,
):
    # set column widths
    sheet.column_dimensions[columns["code"]["letter"]].width = 2.64
    sheet.column_dimensions[columns["shipment_date"]["letter"]].width = 10.6
    sheet.column_dimensions[columns["product"]["letter"]].width = 5.00
    sheet.column_dimensions[columns["ticket_number"]["letter"]].width = 9.00
    sheet.column_dimensions[columns["origin"]["letter"]].width = 16
    sheet.column_dimensions[columns["destination"]["letter"]].width = 16
    sheet.column_dimensions[columns["origin_weight"]["letter"]].width = 9
    sheet.column_dimensions[columns["destination_weight"]["letter"]].width = 9
    sheet.column_dimensions[columns["difference"]["letter"]].width = 5
    sheet.column_dimensions[columns["price_weight"]["letter"]].width = 7.60
    sheet.column_dimensions[columns["shipment_amount"]["letter"]].width = 10.27
    sheet.column_dimensions[columns["untaxed_expense_date"]["letter"]].width = 10.82
    sheet.column_dimensions[columns["untaxed_espense_reason"]["letter"]].width = 7.0
    sheet.column_dimensions[columns["untaxed_expense_amount"]["letter"]].width = 10.27
    sheet.column_dimensions[columns["taxed_expense_date"]["letter"]].width = 10.82
    sheet.column_dimensions[columns["taxed_expense_receipt"]["letter"]].width = 8.5
    sheet.column_dimensions[columns["taxed_expense_reason"]["letter"]].width = 7.0
    sheet.column_dimensions[columns["taxed_expense_amount"]["letter"]].width = 10.82

    # Title
    sheet.append([])
    sheet.append(["LIQUIDACION DE FLETES"])

    sheet.merge_cells(
        start_row=sheet.max_row,
        start_column=1,
        end_row=sheet.max_row,
        end_column=len(columns),
    )
    merged_cell = sheet.cell(row=sheet.max_row, column=1)
    merged_cell.alignment = Alignment(horizontal="center", vertical="center")

    for col in range(1, len(columns) + 1):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.border = border
        cell.font = Font(bold=True)

    sheet.row_dimensions[2].height = 21

    # Driver Information
    sheet.append(
        [
            f'Conductor: {(driver.driver_name or "") + " " + (driver.driver_surname or "")}                Chapa: {driver.truck_plate}                Fecha: {datetime.now().strftime("%d/%m/%Y")}'
        ]
    )
    sheet.merge_cells(
        start_row=sheet.max_row,
        start_column=1,
        end_row=sheet.max_row,
        end_column=len(columns),
    )
    merged_cell = sheet.cell(row=sheet.max_row, column=1)
    merged_cell.alignment = Alignment(horizontal="center", vertical="center")

    for col in range(1, len(columns) + 1):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.border = border
        cell.font = Font(bold=True)

    sheet.row_dimensions[3].height = 21

    # Columns division
    sheet.append(
        [
            "FLETES",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            "GASTOS (VIATICO/GASOIL)",
            None,
            None,
            None,
            None,
        ]
    )

    # Merge FLETES title
    sheet.merge_cells(
        start_row=sheet.max_row,
        start_column=1,
        end_row=sheet.max_row,
        end_column=columns["shipment_amount"]["number"],
    )
    merged_cell = sheet.cell(row=sheet.max_row, column=1)
    merged_cell.alignment = Alignment(horizontal="center", vertical="center")

    for col in range(1, len(columns) + 1):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.border = border
        cell.font = Font(bold=True)

    # Merge GASTOS title
    sheet.merge_cells(
        start_row=sheet.max_row,
        start_column=columns["untaxed_expense_date"]["number"],
        end_row=sheet.max_row,
        end_column=len(columns),
    )
    merged_cell = sheet.cell(
        row=sheet.max_row, column=columns["untaxed_expense_date"]["number"]
    )
    merged_cell.alignment = Alignment(horizontal="center", vertical="center")

    for col in range(1, len(columns) + 1):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.border = border
        cell.font = Font(bold=True)

    # Table Header
    headers = [
        "N°",
        "Fecha",
        "Prod.",
        "Recepcion N°",
        "Origen",
        "Destino",
        "Kg. Origen",
        "Kg. Llegada",
        "Dif.",
        "Gs. p/ Kg",
        "Importe Gs.",
        "Fecha",
        "Razón",
        "Importe Gs.",
        "Fecha",
        "Boleta N°",
        "Razón",
        "Importe Gs.",
    ]

    sheet.append(headers)
    for col in range(1, len(columns) + 1):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.border = border
        cell.font = Font(bold=True)

    sheet.row_dimensions[5].height = 25


def render_driver_payroll_shipment_expense(
    sheet: Worksheet,
    columns: dict[str, dict[str, Any]],
    results: tuple[Shipment, ShipmentExpense, ShipmentExpense],
    border: Border,
):
    origin_weight_column = columns["origin_weight"]["letter"]
    destination_weight_column = columns["destination_weight"]["letter"]
    price_weight_column = columns["price_weight"]["letter"]

    contador = 1
    for shipment, no_receipt, receipt in results:
        row = [contador]

        if shipment:
            current_row = contador + 5
            diff = f"=+${destination_weight_column}{current_row}-${origin_weight_column}{current_row}"
            money = f"=ROUND(${destination_weight_column}{current_row}*${price_weight_column}{current_row}, 0)"

            shipment_row = [
                shipment.shipment_date.strftime("%d/%m/%Y"),
                shipment.product_name,
                shipment.receipt_code,
                shipment.origin,
                shipment.destination,
                shipment.origin_weight,
                shipment.destination_weight,
                diff,
                shipment.payroll_price,
                money,
            ]

            row.extend(shipment_row)

        else:
            row.extend([None] * 10)

        if no_receipt:
            no_receipt_row = [
                no_receipt.expense_date.strftime("%d/%m/%Y"),
                no_receipt.reason,
                no_receipt.amount,
            ]
            row.extend(no_receipt_row)
        else:
            row.extend([None] * 3)

        if receipt:
            receipt_fila = [
                receipt.expense_date.strftime("%d/%m/%Y"),
                receipt.receipt,
                receipt.reason,
                receipt.amount,
            ]
            row.extend(receipt_fila)
        else:
            row.extend([None] * 4)

        sheet.append(row)

        for col in range(1, len(columns) + 1):
            cell = sheet.cell(row=sheet.max_row, column=col)
            cell.border = border

            if col == columns["price_weight"]["number"]:
                cell.number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED2
            else:
                cell.number_format = "#,##0"

        contador += 1


def render_driver_payroll_totals(sheet, columns, border, last_row):
    price_weight_column = columns["price_weight"]["letter"]
    shipment_amount_column = columns["shipment_amount"]["letter"]
    taxed_expense_amount_column = columns["taxed_expense_amount"]["letter"]

    totals_start_column = 7
    totals_end_column = 12
    title_end_column = 9

    # PAYROLL TOTAL
    total_cobrar = [
        None,
        None,
        None,
        None,
        None,
        None,
        "TOTAL A COBRAR:",
        None,
        None,
        f"=+${shipment_amount_column}{last_row + 2}-${taxed_expense_amount_column}{last_row + 2}",
        None,
    ]
    sheet.append(total_cobrar)
    sheet.merge_cells(
        start_row=sheet.max_row,
        start_column=title_end_column + 1,
        end_row=sheet.max_row,
        end_column=title_end_column + 2,
    )
    sheet.merge_cells(
        start_row=sheet.max_row,
        start_column=totals_start_column,
        end_row=sheet.max_row,
        end_column=title_end_column,
    )

    for col in range(
        columns["origin_weight"]["number"], columns["shipment_amount"]["number"]
    ):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.border = border
        cell.font = Font(bold=True)

        if col == columns["shipment_amount"]["number"]:
            cell.number_format = "#,##0"

    total_facturar = [
        None,
        None,
        None,
        None,
        None,
        None,
        "TOTAL A FACTURAR:",
        None,
        None,
        f"=+${shipment_amount_column}{last_row + 2}-${taxed_expense_amount_column}{last_row + 1}",
        None,
    ]
    sheet.append(total_facturar)
    sheet.merge_cells(
        start_row=sheet.max_row,
        start_column=title_end_column + 1,
        end_row=sheet.max_row,
        end_column=title_end_column + 2,
    )
    sheet.merge_cells(
        start_row=sheet.max_row,
        start_column=totals_start_column,
        end_row=sheet.max_row,
        end_column=title_end_column,
    )

    for col in range(
        columns["origin_weight"]["number"], columns["shipment_amount"]["number"]
    ):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.border = border
        cell.font = Font(bold=True)

        if col == columns["shipment_amount"]["number"]:
            cell.number_format = "#,##0"

    sheet.append(
        [
            None,
            None,
            None,
            None,
            None,
            None,
            "Facturar a nombre de CARMELO MEDINA. Ruc: 850.299-4",
            None,
            None,
            None,
            None,
        ]
    )

    sheet.merge_cells(
        start_row=sheet.max_row,
        start_column=totals_start_column,
        end_row=sheet.max_row,
        end_column=totals_end_column,
    )

    for col in range(totals_start_column, totals_end_column + 1):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.border = border

    sheet.append([])
    sheet.append(
        [
            None,
            None,
            None,
            None,
            None,
            None,
            "Descripcion",
            None,
            None,
            "Exenta",
            "IVA 5%",
            "IVA 10%",
            None,
        ]
    )

    sheet.merge_cells(
        start_row=sheet.max_row,
        start_column=totals_start_column,
        end_row=sheet.max_row,
        end_column=title_end_column,
    )

    for col in range(totals_start_column, totals_end_column + 1):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.border = border

    sheet.append(
        [
            None,
            None,
            None,
            None,
            None,
            None,
            "Servicio de Flete",
            None,
            None,
            0,
            0,
            f"=+${price_weight_column}{last_row + 5}",
            None,
        ]
    )

    sheet.merge_cells(
        start_row=sheet.max_row,
        start_column=totals_start_column,
        end_row=sheet.max_row,
        end_column=title_end_column,
    )

    for col in range(totals_start_column, totals_end_column + 1):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.border = border

        if col >= title_end_column:
            cell.number_format = "#,##0"

    sheet.append([None, None, None, None, None, None, None, None, None, None, None])

    sheet.merge_cells(
        start_row=sheet.max_row,
        start_column=totals_start_column,
        end_row=sheet.max_row,
        end_column=title_end_column,
    )

    for col in range(totals_start_column, totals_end_column + 1):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.border = border

        if col >= title_end_column:
            cell.number_format = "#,##0"

    sheet.append(
        [
            None,
            None,
            None,
            None,
            None,
            None,
            "Subtotal",
            None,
            None,
            f"=+J{last_row + 9}",
            0,
            f"=+L{last_row + 9}",
            None,
        ]
    )

    sheet.merge_cells(
        start_row=sheet.max_row,
        start_column=totals_start_column,
        end_row=sheet.max_row,
        end_column=title_end_column,
    )

    for col in range(totals_start_column, totals_end_column + 1):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.border = border

        if col >= title_end_column:
            cell.number_format = "#,##0"

    sheet.append(
        [
            None,
            None,
            None,
            None,
            None,
            None,
            "Total",
            None,
            None,
            None,
            None,
            f"=+J{last_row + 11}+L{last_row + 11}",
            None,
        ]
    )

    sheet.merge_cells(
        start_row=sheet.max_row,
        start_column=totals_start_column,
        end_row=sheet.max_row,
        end_column=title_end_column,
    )
    for col in range(totals_start_column, totals_end_column + 1):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.border = border
        cell.font = Font(bold=True)

        if col >= title_end_column:
            cell.number_format = "#,##0"

    sheet.append(
        [
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            "IVA 10%",
            None,
            f"=+L{last_row + 12}/11",
            None,
        ]
    )

    sheet.merge_cells(
        start_row=sheet.max_row,
        start_column=totals_start_column,
        end_row=sheet.max_row,
        end_column=title_end_column,
    )

    for col in range(totals_start_column, totals_end_column + 1):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.border = border
        cell.font = Font(bold=True)

        if col >= title_end_column:
            cell.number_format = "#,##0"
