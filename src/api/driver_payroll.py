import io

from decimal import Decimal

from datetime import datetime
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import List
from typing import Iterator

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


from num2words import num2words

from app_config import logger
from app_config import app
from app_config import db_session
from app_config import RequestWithUser

from decorators.token_required import token_required

from models.driver_payroll import DriverPayroll
from models.driver import Driver
from models.shipment import Shipment
from models.shipment_expense import ShipmentExpense

from utils.locale import get_locale
from utils.locale import get_message

request: RequestWithUser

# Translation dictionaries
MESSAGES = {
    "en": {
        # Error messages
        "payroll_not_found": "Payroll not found",
        "driver_not_found": "Driver not found",
        "transaction_error": "Transaction error",
        "driver_payrolls_error": "Error getting driver payrolls",
        "paid_field_required": "Field 'paid' is required",
        "invalid_data": "Invalid data",
        "connection_error": "Connection error",
        "paid_status_update_error": "Error updating payment status",
        "invalid_payroll_data": "Invalid payroll data",
        "add_payroll_error": "Error adding payroll",
        "update_payroll_error": "Error updating payroll",
        "delete_payroll_error": "Error deleting payroll",
        "export_error": "Error generating export file",
        "invalid_date_format": "Invalid date format",
        "no_export_data": "No data to export in the selected date range",
        # Success messages
        "payroll_added": "Payroll added successfully",
        "payroll_updated": "Payroll updated successfully",
        "payroll_deleted": "Payroll deleted successfully",
        "paid_status_updated_to_paid": "Payroll status updated to paid",
        "paid_status_updated_to_unpaid": "Payroll status updated to unpaid",
        # Excel headers and labels
        "code": "Code",
        "date": "Date",
        "collected": "Collected",
        "collection_date": "Collection Date",
        "payroll_list": "payroll_list",
        "yes": "Yes",
        "no": "No",
        # Settlement Excel specific translations
        "settlement": "SETTLEMENT",
        "driver": "Driver",
        "plate": "Plate",
        "shipments": "SHIPMENTS",
        "expenses": "EXPENSES (ALLOWANCE/FUEL)",
        "num": "No.",
        "product": "Prod.",
        "receipt_num": "Receipt No.",
        "origin": "Origin",
        "destination": "Destination",
        "origin_kg": "Origin Kg.",
        "destination_kg": "Destination Kg.",
        "diff": "Diff.",
        "price_per_kg": "$ per Kg",
        "amount": "Amount $",
        "reason": "Reason",
        "subtotal": "Subtotal",
        "total_shipments": "TOTAL SHIPMENTS:",
        "total_expenses": "TOTAL EXPENSES:",
        "total_to_collect": "TOTAL TO COLLECT:",
        "total_to_invoice": "TOTAL TO INVOICE:",
        "invoice_to": "Invoice to CARMELO MEDINA. Tax ID: 850,299-4",
        "description": "Description",
        "exempt": "Exempt",
        "vat_5": "VAT 5%",
        "vat_10": "VAT 10%",
        "shipping_service": "Shipping Service",
        "total": "Total",
        "settlement_for": "Settlement for",
    },
    "es": {
        # Error messages
        "payroll_not_found": "No se encontró la liquidación",
        "driver_not_found": "Chofer no encontrado",
        "transaction_error": "Error de transacción",
        "driver_payrolls_error": "Error al obtener liquidaciones del chofer",
        "paid_field_required": "Campo 'paid' requerido",
        "invalid_data": "Datos inválidos",
        "connection_error": "Problema de conexión",
        "paid_status_update_error": "Error al actualizar estado de pago",
        "invalid_payroll_data": "Datos de la Liquidación inválidos",
        "add_payroll_error": "Error al agregar liquidación",
        "update_payroll_error": "Error al actualizar liquidación",
        "delete_payroll_error": "Error al eliminar liquidación",
        "export_error": "Error al generar el archivo de exportación",
        "invalid_date_format": "Formato de fecha inválido",
        "no_export_data": "No hay datos para exportar en el rango de fechas seleccionado",
        # Success messages
        "payroll_added": "Liquidación agregada exitosamente",
        "payroll_updated": "Liquidación actualizada exitosamente",
        "payroll_deleted": "Liquidación eliminada exitosamente",
        "paid_status_updated_to_paid": "Estado de Liquidación a pagado",
        "paid_status_updated_to_unpaid": "Estado de Liquidación a no pagado",
        # Excel headers and labels
        "code": "Código",
        "date": "Fecha",
        "collected": "Cobrado",
        "collection_date": "Fecha de Cobro",
        "payroll_list": "lista_de_planillas",
        "yes": "Sí",
        "no": "No",
        # Settlement Excel specific translations
        "settlement": "LIQUIDACION DE FLETES",
        "driver": "Conductor",
        "plate": "Chapa",
        "shipments": "FLETES",
        "expenses": "GASTOS (VIATICO/GASOIL)",
        "num": "N°",
        "product": "Prod.",
        "receipt_num": "Recepcion N°",
        "origin": "Origen",
        "destination": "Destino",
        "origin_kg": "Kg. Origen",
        "destination_kg": "Kg. Llegada",
        "diff": "Dif.",
        "price_per_kg": "Gs. p/ Kg",
        "amount": "Importe Gs.",
        "reason": "Razón",
        "subtotal": "Subtotal",
        "total_shipments": "TOTAL FLETES:",
        "total_expenses": "TOTAL GASTOS:",
        "total_to_collect": "TOTAL A COBRAR:",
        "total_to_invoice": "TOTAL A FACTURAR:",
        "invoice_to": "Facturar a nombre de CARMELO MEDINA. Ruc: 850.299-4",
        "description": "Descripcion",
        "exempt": "Exenta",
        "vat_5": "IVA 5%",
        "vat_10": "IVA 10%",
        "shipping_service": "Servicio de Flete",
        "total": "Total",
        "settlement_for": "Liquidacion",
    },
}


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
            return jsonify({"message": get_message(MESSAGES, "payroll_not_found")}), 404

        logger.info("fetch table DriverPayroll, found: %s", driver_payroll.payroll_code)
        logger.debug("fetch table DriverPayroll, found: %s", driver_payroll)

        return jsonify(driver_payroll), 200

    except SQLAlchemyError as e:
        logger.error("fetch table DriverPayroll, error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "transaction_error")}), 500


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
            return jsonify({"message": get_message(MESSAGES, "driver_not_found")}), 404

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
        return jsonify({"message": get_message(MESSAGES, "driver_payrolls_error")}), 500


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
            return jsonify({"message": get_message(MESSAGES, "payroll_not_found")}), 404

        # Get the payload
        payload = request.get_json()

        if "paid" not in payload:
            logger.error("update paid status, missing paid field")
            return (
                jsonify({"message": get_message(MESSAGES, "paid_field_required")}),
                400,
            )

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

        status_message = get_message(
            MESSAGES,
            (
                "paid_status_updated_to_paid"
                if entry_to_update.paid
                else "paid_status_updated_to_unpaid"
            ),
        )

        return (
            jsonify(
                {
                    **asdict(entry_to_update),
                    "message": status_message,
                }
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("invalid paid status update: %s", e)
        error_msg = f"{get_message(MESSAGES, 'invalid_data')} ({e})"
        return jsonify({"message": error_msg}), 400

    except OperationalError as e:
        db_session.rollback()
        logger.error("update paid status: connection error %s", e)
        return (
            jsonify(
                {
                    "message": get_message(MESSAGES, "paid_status_update_error")
                    + ": "
                    + get_message(MESSAGES, "connection_error")
                }
            ),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("update paid status, error: %s", e)
        return (
            jsonify({"message": get_message(MESSAGES, "paid_status_update_error")}),
            500,
        )


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
            return jsonify({"message": get_message(MESSAGES, "driver_not_found")}), 404

        # add to database
        logger.debug("insert table DriverPayroll, payload: %s", payload)
        db_session.add(payload)

        db_session.commit()
        logger.info("inserted table DriverPayroll, payroll: %s", payload.payroll_code)
        return (
            jsonify(
                {**asdict(payload), "message": get_message(MESSAGES, "payroll_added")}
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("insert table DriverPayroll, invalid payroll error: %s", e)
        error_msg = f"{get_message(MESSAGES, 'invalid_payroll_data')} ({e})"
        return (
            jsonify({"message": error_msg}),
            500,
        )

    except OperationalError as e:
        db_session.rollback()
        logger.error("insert table DriverPayroll, connection error: %s", e)

        return (
            jsonify(
                {
                    "message": get_message(MESSAGES, "add_payroll_error")
                    + ": "
                    + get_message(MESSAGES, "connection_error")
                }
            ),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("insert table DriverPayroll, error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "add_payroll_error")}), 500


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
            return jsonify({"message": get_message(MESSAGES, "payroll_not_found")}), 404

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
            return jsonify({"message": get_message(MESSAGES, "driver_not_found")}), 404

        entry_to_update.driver_code = payload.driver_code
        entry_to_update.modification_user = payload.modification_user

        logger.info("update table DriverPayroll, payload: %s", entry_to_update)

        db_session.commit()
        logger.info("updated table DriverPayroll, payroll: %s", payroll_code)
        return (
            jsonify(
                {
                    **asdict(entry_to_update),
                    "message": get_message(MESSAGES, "payroll_updated"),
                }
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("invalid payroll: %s", e)
        error_msg = f"{get_message(MESSAGES, 'invalid_payroll_data')} ({e})"
        return (
            jsonify({"message": error_msg}),
            500,
        )

    except OperationalError as e:
        db_session.rollback()
        logger.error("update table DriverPayroll: connection error %s", e)

        return (
            jsonify(
                {
                    "message": get_message(MESSAGES, "update_payroll_error")
                    + ": "
                    + get_message(MESSAGES, "connection_error")
                }
            ),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("update table DriverPayroll, error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "update_payroll_error")}), 500


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
            return jsonify({"message": get_message(MESSAGES, "payroll_not_found")}), 404

        existing_entry.deleted = True
        existing_entry.modification_user = request.current_user.user_id
        db_session.commit()
        logger.info("delete table DriverPayroll: payroll %s", payroll_code)
        return jsonify({"message": get_message(MESSAGES, "payroll_deleted")}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table DriverPayroll, connection error: %s", e)
        return (
            jsonify(
                {
                    "message": get_message(MESSAGES, "delete_payroll_error")
                    + ": "
                    + get_message(MESSAGES, "connection_error")
                }
            ),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table DriverPayroll, error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "delete_payroll_error")}), 500


@app.route("/api/driver-payrolls", methods=["DELETE"])
@token_required
def delete_driver_payrolls() -> Tuple[Response, int]:
    if (request.data is None) or (not request.is_json):
        logger.error("delete payrolls table DriverPayroll, payroll list is empty")
        return (
            jsonify(
                {
                    "message": get_message(MESSAGES, "delete_payroll_error")
                    + ": "
                    + get_message(MESSAGES, "payroll_not_found")
                }
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
                            "message": get_message(MESSAGES, "delete_payroll_error")
                            + ": "
                            + get_message(MESSAGES, "payroll_not_found")
                        }
                    ),
                    404,
                )

            payroll.deleted = True
            payroll.modification_user = request.current_user.user_id
            logger.info("delete table DriverPayroll, payroll: %s", payroll_code)

        db_session.commit()
        return jsonify({"message": get_message(MESSAGES, "payroll_deleted")}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table DriverPayroll: connection error %s", e)
        return (
            jsonify(
                {
                    "message": get_message(MESSAGES, "delete_payroll_error")
                    + ": "
                    + get_message(MESSAGES, "connection_error")
                }
            ),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table DriverPayroll, error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "delete_payroll_error")}), 500


@app.route("/api/driver-payrolls/export-excel", methods=["GET"])
@token_required
def export_driver_payroll_list() -> Tuple[Response, int]:
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
                jsonify({"message": get_message(MESSAGES, "no_export_data")}),
                404,
            )

        # Create file
        output = io.BytesIO()
        workbook = Workbook(write_only=False, iso_dates=False)
        sheet = workbook.active

        # Get translated headers
        headers = [
            get_message(MESSAGES, "code"),
            get_message(MESSAGES, "date"),
            get_message(MESSAGES, "collected"),
            get_message(MESSAGES, "collection_date"),
        ]
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

            # Use translated yes/no responses
            paid_text = (
                get_message(MESSAGES, "yes")
                if payroll.paid
                else get_message(MESSAGES, "no")
            )

            row = [
                payroll.payroll_code,
                payroll_date,
                paid_text,
                paid_date,
            ]

            sheet.append(row)

            # Apply border style to each cell in the data row
            for cell in sheet[sheet.max_row]:
                cell.border = border_style

        # Save Excel file to output stream
        workbook.save(output)
        output.seek(0)

        # Create response with Excel file - use translated filename
        filename = f'{get_message(MESSAGES, "payroll_list")}.xlsx'

        response = make_response(output.getvalue())
        response.headers["Content-Type"] = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"

        logger.info("exported ShipmentPayrolls excel file")

        return response, 200

    except ValueError as e:
        logger.error("export ShipmentPayrolls, invalid date format: %s", e)
        return jsonify({"message": get_message(MESSAGES, "invalid_date_format")}), 400

    except SQLAlchemyError as e:
        logger.error("export ShipmentPayrolls, database error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "export_error")}), 500

    except Exception as e:
        logger.error("export ShipmentPayrolls, unexpected error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "export_error")}), 500


@app.route(
    "/api/driver-payroll/export-excel/<int:driver_payroll_code>", methods=["GET"]
)
@token_required
def exportar_driver_payroll(driver_payroll_code: int):
    try:
        driver_payroll_stmt = select(DriverPayroll).where(
            DriverPayroll.payroll_code == driver_payroll_code,
            DriverPayroll.deleted == False,
            DriverPayroll.modification_user == request.current_user.user_id,
        )
        driver_payroll: Optional[DriverPayroll] = db_session.scalar(driver_payroll_stmt)
        if driver_payroll is None:
            logger.error("fetch table DriverPayroll, not found")
            return jsonify({"message": get_message(MESSAGES, "payroll_not_found")}), 404

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
            return jsonify({"message": get_message(MESSAGES, "driver_not_found")}), 404

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
        return jsonify({"message": get_message(MESSAGES, "transaction_error")}), 500

    max_len = max(
        len(shipments),
        len(shipment_expenses_no_receipt),
        len(shipment_expenses_receipt),
    )

    # Fill the lists to have the same length with None if necessary
    shipments += [None] * (max_len - len(shipments))
    shipment_expenses_no_receipt += [None] * (
        max_len - len(shipment_expenses_no_receipt)
    )
    shipment_expenses_receipt += [None] * (max_len - len(shipment_expenses_receipt))

    # Combine the three lists into a list of tuples using zip
    results = zip(shipments, shipment_expenses_no_receipt, shipment_expenses_receipt)

    # Create an Excel file in memory
    output = io.BytesIO()
    workbook = Workbook()
    sheet = workbook.active

    # define columns
    columns: dict[str, dict[str, str | int]] = {
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
        "untaxed_expense_reason": {"letter": "M", "number": 13},
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
        get_message(MESSAGES, "subtotal"),
        None,
        subtotal_sin_boleta,
        get_message(MESSAGES, "subtotal"),
        None,
        None,
        subtotal_con_boleta,
    ]
    sheet.append(subtotales)

    for col in range(1, columns_length + 1):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.border = border
        cell.font = Font(bold=True)

    for col in range(columns["untaxed_expense_date"]["number"], columns_length + 1):
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
        get_message(MESSAGES, "total_shipments"),
        None,
        subtotal_viajes,
        get_message(MESSAGES, "total_expenses"),
        None,
        None,
        None,
        None,
        None,
        total_gastos,
    ]
    sheet.append(total)
    sheet.merge_cells(
        start_row=sheet.max_row,
        start_column=columns["difference"]["number"],
        end_row=sheet.max_row,
        end_column=columns["price_weight"]["number"],
    )
    sheet.merge_cells(
        start_row=sheet.max_row,
        start_column=columns["untaxed_expense_date"]["number"],
        end_row=sheet.max_row,
        end_column=columns["untaxed_expense_reason"]["number"],
    )

    for col in range(columns["shipment_amount"]["number"], len(columns) + 1):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.number_format = "#,##0"
        cell.border = border

    for col in range(1, len(columns) + 1):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.border = border
        cell.font = Font(bold=True)

    sheet.append([])

    render_driver_payroll_totals(
        sheet,
        columns,
        border,
        last_row,
        shipments,
        shipment_expenses_receipt,
    )

    # Save and send Excel file
    workbook.save(output)
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    name = (driver.driver_name or "") + " " + (driver.driver_surname or "")
    date = driver_payroll.payroll_timestamp.date().strftime("%d/%m/%Y")

    # Use translated settlement term in filename
    settlement_term = get_message(MESSAGES, "settlement_for")
    response.headers["Content-Disposition"] = (
        f"attachment; filename={name.strip()}_{settlement_term}_{date}.xlsx"
    )
    logger.info(
        "Liquidacion %s %s exportada", driver.driver_code, driver_payroll.payroll_code
    )
    return response


def render_driver_payroll_headers(
    sheet: Worksheet,
    columns: dict[str, dict[str, str | int]],
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
    sheet.column_dimensions[columns["untaxed_expense_reason"]["letter"]].width = 7.0
    sheet.column_dimensions[columns["untaxed_expense_amount"]["letter"]].width = 10.27
    sheet.column_dimensions[columns["taxed_expense_date"]["letter"]].width = 10.82
    sheet.column_dimensions[columns["taxed_expense_receipt"]["letter"]].width = 8.5
    sheet.column_dimensions[columns["taxed_expense_reason"]["letter"]].width = 7.0
    sheet.column_dimensions[columns["taxed_expense_amount"]["letter"]].width = 10.82

    # Title
    sheet.append([])
    sheet.append([get_message(MESSAGES, "settlement")])

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

    # Driver Information with translations
    driver_text = get_message(MESSAGES, "driver")
    plate_text = get_message(MESSAGES, "plate")
    date_text = get_message(MESSAGES, "date")

    sheet.append(
        [
            f'{driver_text}: {(driver.driver_name or "") + " " + (driver.driver_surname or "")}                {plate_text}: {driver.truck_plate}                {date_text}: {datetime.now().strftime("%d/%m/%Y")}'
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

    # Columns division with translations
    sheet.append(
        [
            get_message(MESSAGES, "shipments"),
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
            get_message(MESSAGES, "expenses"),
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

    # Table Header with translations
    headers = [
        get_message(MESSAGES, "num"),
        get_message(MESSAGES, "date"),
        get_message(MESSAGES, "product"),
        get_message(MESSAGES, "receipt_num"),
        get_message(MESSAGES, "origin"),
        get_message(MESSAGES, "destination"),
        get_message(MESSAGES, "origin_kg"),
        get_message(MESSAGES, "destination_kg"),
        get_message(MESSAGES, "diff"),
        get_message(MESSAGES, "price_per_kg"),
        get_message(MESSAGES, "amount"),
        get_message(MESSAGES, "date"),
        get_message(MESSAGES, "reason"),
        get_message(MESSAGES, "amount"),
        get_message(MESSAGES, "date"),
        get_message(MESSAGES, "receipt_num"),
        get_message(MESSAGES, "reason"),
        get_message(MESSAGES, "amount"),
    ]

    sheet.append(headers)
    for col in range(1, len(columns) + 1):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.border = border
        cell.font = Font(bold=True)

    sheet.row_dimensions[5].height = 25


def render_driver_payroll_shipment_expense(
    sheet: Worksheet,
    columns: dict[str, dict[str, str | int]],
    results: Iterator[tuple[Shipment, ShipmentExpense, ShipmentExpense]],
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


def render_driver_payroll_totals(
    sheet: Worksheet,
    columns: dict[str, dict[str, str | int]],
    border: Border,
    last_row: int,
    shipments: Sequence[Shipment],
    shipment_expenses_receipt: Sequence[ShipmentExpense],
):
    price_weight_column = columns["price_weight"]["letter"]
    shipment_amount_column = columns["shipment_amount"]["letter"]
    taxed_expense_amount_column = columns["taxed_expense_amount"]["letter"]

    totals_start_column = 7
    totals_end_column = 12
    title_end_column = 9

    # PAYROLL TOTAL with translation
    total_cobrar = [
        None,
        None,
        None,
        None,
        None,
        None,
        get_message(MESSAGES, "total_to_collect"),
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
        columns["origin_weight"]["number"], columns["shipment_amount"]["number"] + 1
    ):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.border = border
        cell.font = Font(bold=True)

        if col in [
            columns["shipment_amount"]["number"] - 1,
            columns["shipment_amount"]["number"],
        ]:
            cell.number_format = "#,##0"

    total_facturar = [
        None,
        None,
        None,
        None,
        None,
        None,
        get_message(MESSAGES, "total_to_invoice"),
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
        columns["origin_weight"]["number"], columns["shipment_amount"]["number"] + 1
    ):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.border = border
        cell.font = Font(bold=True)

        if col in [
            columns["shipment_amount"]["number"] - 1,
            columns["shipment_amount"]["number"],
        ]:
            cell.number_format = "#,##0"

    sheet.append(
        [
            None,
            None,
            None,
            None,
            None,
            None,
            get_message(MESSAGES, "invoice_to"),
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
            get_message(MESSAGES, "description"),
            None,
            None,
            get_message(MESSAGES, "exempt"),
            get_message(MESSAGES, "vat_5"),
            get_message(MESSAGES, "vat_10"),
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
            get_message(MESSAGES, "shipping_service"),
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
            get_message(MESSAGES, "subtotal"),
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
            get_message(MESSAGES, "total"),
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
            get_message(MESSAGES, "vat_10"),
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

    sheet.append([])

    # For shipments calculation, skip if destination_weight or payroll_price is None
    total_shipment_amount = sum(
        (shipment.destination_weight * shipment.payroll_price)
        for shipment in shipments
        if shipment is not None
    )
    # For shipment expenses calculation, skip if amount is None
    total_shipment_expenses_receipt_amount = sum(
        shipment_expense.amount
        for shipment_expense in shipment_expenses_receipt
        if shipment_expense is not None
    )
    total_invoice = total_shipment_amount - total_shipment_expenses_receipt_amount

    # Get locale for number to words conversion
    locale = get_locale()
    lang = "en" if locale == "en" else "es"

    # Convert to words in the appropriate language
    total_in_words = num2words(total_invoice, lang=lang).capitalize()
    iva_in_words = num2words(total_invoice / Decimal("11"), lang=lang).capitalize()

    # Use translated 'total' text
    total_label = get_message(MESSAGES, "total")
    sheet.append(
        [
            None,
            None,
            None,
            None,
            None,
            None,
            f"{total_label}: {total_in_words}",
            None,
            None,
            None,
            None,
            None,
            None,
        ]
    )

    # Add two more empty rows to create height for wrapping
    sheet.append([None] * 13)
    sheet.append([None] * 13)

    # Get the row numbers
    total_text_start_row = sheet.max_row - 2
    total_text_end_row = sheet.max_row

    # Merge cells vertically and horizontally for Total locale string
    sheet.merge_cells(
        start_row=total_text_start_row,
        start_column=totals_start_column,
        end_row=total_text_end_row,
        end_column=totals_end_column,
    )

    # Format the merged cell with borders, font, and text wrapping
    merged_cell = sheet.cell(row=total_text_start_row, column=totals_start_column)
    merged_cell.border = border
    merged_cell.font = Font(bold=True, italic=True)
    merged_cell.alignment = Alignment(wrap_text=True, vertical="center")

    # Get translated VAT label
    vat_label = get_message(MESSAGES, "vat_10")

    # Add empty rows for the 3-row IVA locale string (first row will contain the text)
    sheet.append(
        [
            None,
            None,
            None,
            None,
            None,
            None,
            f"{vat_label}: {iva_in_words}",
            None,
            None,
            None,
            None,
            None,
            None,
        ]
    )
    # Add two more empty rows to create height for wrapping
    sheet.append([None] * 13)
    sheet.append([None] * 13)

    # Get the row numbers
    iva_text_start_row = sheet.max_row - 2
    iva_text_end_row = sheet.max_row

    # Merge cells vertically and horizontally for IVA locale string
    sheet.merge_cells(
        start_row=iva_text_start_row,
        start_column=totals_start_column,
        end_row=iva_text_end_row,
        end_column=totals_end_column,
    )

    # Format the merged cell with borders, font, and text wrapping
    merged_cell = sheet.cell(row=iva_text_start_row, column=totals_start_column)
    merged_cell.border = border
    merged_cell.font = Font(bold=True, italic=True)
    merged_cell.alignment = Alignment(wrap_text=True, vertical="center")
