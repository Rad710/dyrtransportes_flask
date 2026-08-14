import io

from typing import Any
from typing import Sequence
from typing import Tuple
from typing import Optional
from typing import List

from datetime import datetime
from decimal import Decimal

from dataclasses import asdict

from openpyxl import Workbook
from openpyxl.styles import Alignment
from openpyxl.styles import numbers
from openpyxl.styles import Border
from openpyxl.styles import Side
from openpyxl.styles import Font
from openpyxl.styles import PatternFill
from openpyxl.utils import get_column_letter

from reportlab.platypus import Paragraph
from reportlab.platypus import Spacer
from reportlab.platypus import Table
from reportlab.platypus import TableStyle
from reportlab.platypus.doctemplate import LayoutError

from flask import Blueprint
from flask import request
from flask import jsonify
from flask import Response
from flask import make_response


from sqlalchemy import select
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import IntegrityError

from app_config import logger
from app_config import db_session
from app_config import RequestWithUser

from decorators.token_required import token_required

from models.shipment import Shipment
from models.api_models import shipment_list_to_grouped_shipments_list
from models.driver_payroll import DriverPayroll
from models.shipment_payroll import ShipmentPayroll

from utils.locale import get_locale
from utils.locale import get_message

from utils.pdf import build_pdf
from utils.pdf import cell as pdf_cell
from utils.pdf import format_number
from utils.pdf import round_amount
from utils.pdf import scale_widths
from utils.pdf import ACCENT_TITLE_STYLE
from utils.pdf import GRID_COLOR
from utils.pdf import HEADER_BACKGROUND
from utils.pdf import SUBTITLE_STYLE
from utils.pdf import SUBTOTAL_BACKGROUND

shipment_bp = Blueprint("shipment", __name__)

request: RequestWithUser

# Translation dictionaries
MESSAGES = {
    "en": {
        # Error messages
        "shipment_not_found": "Shipment not found",
        "transaction_error": "Transaction error",
        "get_shipments_error": "Error getting shipments",
        "shipment_payroll_not_found": "Shipment payroll not found",
        "invalid_shipment_payroll_param": "Parameter 'shipment_payroll_code' must be an integer",
        "driver_payroll_not_found": "Driver payroll not found",
        "invalid_driver_payroll_param": "Parameter 'driver_payroll_code' must be an integer",
        "driver_no_payrolls": "The driver has no payrolls",
        "invalid_shipment_data": "Invalid shipment data",
        "connection_error": "Connection error",
        "add_shipment_error": "Error adding shipment",
        "duplicate_shipment": "Error adding shipment: duplicate shipment",
        "data_integrity_error": "Error adding shipment: data integrity error",
        "update_shipment_error": "Error updating shipment",
        "invalid_payload": "Invalid payload",
        "shipments_not_found_to_update": "No shipments found to update",
        "update_shipments_error": "Error updating shipments",
        "delete_shipment_error": "Error deleting shipment",
        "shipment_not_found_for_delete": "Error deleting shipment: shipment not found",
        "excel_creation_error": "Error creating Excel file",
        "excel_no_data": "Error creating Excel file, no data",
        "pdf_creation_error": "Error creating PDF file",
        # Success messages
        "shipment_added": "Shipment added successfully",
        "shipment_updated": "Shipment updated successfully",
        "shipments_updated": "Shipments updated successfully",
        "shipment_deleted": "Shipment deleted successfully",
        # Excel headers and values
        "num": "No.",
        "date": "Date",
        "driver": "Driver",
        "plate": "Plate",
        "product": "Product",
        "origin": "Origin",
        "destination": "Destination",
        "dispatch": "Dispatch",
        "ticket": "Ticket",
        "origin_weight": "Origin Weight",
        "destination_weight": "Destination Weight",
        "difference": "Diff.",
        "tolerance": "Tolerance",
        "difference_tolerance": "Diff. Tol.",
        "price": "Price",
        "total": "Total",
        "subtotal": "Subtotal",
        "total_row": "TOTAL",
        "company_name": "D & R TRANSPORT",
        "collection": "collection",
    },
    "es": {
        # Error messages
        "shipment_not_found": "No se encontró la Carga",
        "transaction_error": "Error de transacción",
        "get_shipments_error": "Error al obtener planillas",
        "shipment_payroll_not_found": "Planilla de carga no encontrada",
        "invalid_shipment_payroll_param": "Parámetro 'shipment_payroll_code' debe ser un número entero",
        "driver_payroll_not_found": "Liquidación no encontrada",
        "invalid_driver_payroll_param": "Parámetro 'driver_payroll_code' debe ser un número entero",
        "driver_no_payrolls": "El chofer no tiene liquidaciones",
        "invalid_shipment_data": "Datos de la Carga inválidos",
        "connection_error": "problema de conexión",
        "add_shipment_error": "Error al agregar Carga",
        "duplicate_shipment": "Error al agregar Carga: carga duplicada",
        "data_integrity_error": "Error al agregar Carga: error de integridad de datos",
        "update_shipment_error": "Error al actualizar Carga",
        "invalid_payload": "Payload inválido",
        "shipments_not_found_to_update": "No se encontraron cargas para actualizar",
        "update_shipments_error": "Error al actualizar cargas",
        "delete_shipment_error": "Error al eliminar Carga",
        "shipment_not_found_for_delete": "Error al eliminar Carga: Carga no encontrada",
        "excel_creation_error": "Error al crear archivo Excel",
        "excel_no_data": "Error al crear archivo Excel, sin datos",
        "pdf_creation_error": "Error al crear archivo PDF",
        # Success messages
        "shipment_added": "Carga agregada exitosamente",
        "shipment_updated": "Carga actualizada exitosamente",
        "shipments_updated": "Cargas actualizadas exitosamente",
        "shipment_deleted": "Carga eliminada exitosamente",
        # Excel headers and values
        "num": "N°",
        "date": "Fecha",
        "driver": "Chofer",
        "plate": "Chapa",
        "product": "Producto",
        "origin": "Origen",
        "destination": "Destino",
        "dispatch": "Remision",
        "ticket": "Tiquet",
        "origin_weight": "Kilos Origen",
        "destination_weight": "Kilos Destino",
        "difference": "Dif.",
        "tolerance": "Tolera",
        "difference_tolerance": "Dif. Tol.",
        "price": "Precio",
        "total": "Total",
        "subtotal": "Subtotal",
        "total_row": "TOTAL",
        "company_name": "D & R TRANSPORTES",
        "collection": "cobranza",
    },
}


@shipment_bp.route("/api/shipment/<int:shipment_code>", methods=["GET"])
@token_required
def get_shipment(shipment_code: int) -> Tuple[Response, int]:
    try:
        stmt = select(Shipment).where(
            Shipment.shipment_code == shipment_code,
            Shipment.deleted == False,
            Shipment.modification_user == request.current_user.user_id,
        )

        shipment: Optional[Shipment] = db_session.scalar(stmt)
        if shipment is None:
            logger.error("fetch table Shipment, not found")
            return (
                jsonify({"message": get_message(MESSAGES, "shipment_not_found")}),
                404,
            )

        logger.info("fetch table Shipment, found: %s", shipment.shipment_code)
        logger.debug("fetch table Shipment, found: %s", shipment)

        return jsonify(shipment), 200

    except SQLAlchemyError as e:
        logger.error("fetch table Shipment, error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "transaction_error")}), 500


@shipment_bp.route("/api/shipments", methods=["GET"])
@token_required
def get_shipment_list() -> Tuple[Response, int]:
    shipment_payroll_code_param: str | None = request.args.get("shipment_payroll_code")
    shipment_payroll_code = None

    # If shipment_payroll_code_param is provided, validate it
    if shipment_payroll_code_param:
        try:
            shipment_payroll_code = int(shipment_payroll_code_param)

            # Validate that the shipment_payroll exists in the database
            stmt_shipment_payroll = select(ShipmentPayroll).where(
                ShipmentPayroll.payroll_code == shipment_payroll_code,
                ShipmentPayroll.deleted == False,
                ShipmentPayroll.modification_user == request.current_user.user_id,
            )

            shipment_payroll = db_session.scalar(stmt_shipment_payroll)
            if not shipment_payroll:
                logger.error(
                    "ShipmentPayroll with code %s not found", shipment_payroll_code
                )
                return (
                    jsonify(
                        {"message": get_message(MESSAGES, "shipment_payroll_not_found")}
                    ),
                    404,
                )

        except ValueError:
            logger.error("Invalid 'shipment_payroll_code' parameter: not an integer")
            return (
                jsonify(
                    {"message": get_message(MESSAGES, "invalid_shipment_payroll_param")}
                ),
                400,
            )

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
                    "driverPayroll with code %s not found", driver_payroll_code
                )
                return (
                    jsonify(
                        {"message": get_message(MESSAGES, "driver_payroll_not_found")}
                    ),
                    404,
                )

        except ValueError:
            logger.error("Invalid 'driver_payroll_code' parameter: not an integer")
            return (
                jsonify(
                    {"message": get_message(MESSAGES, "invalid_driver_payroll_param")}
                ),
                400,
            )

    try:
        stmt = (
            select(Shipment)
            .where(
                Shipment.deleted == False,
                Shipment.modification_user == request.current_user.user_id,
            )
            .order_by(Shipment.shipment_date, Shipment.shipment_code)
        )

        if shipment_payroll_code:
            stmt = stmt.where(Shipment.shipment_payroll_code == shipment_payroll_code)

        if driver_payroll_code:
            stmt = stmt.where(Shipment.driver_payroll_code == driver_payroll_code)

        shipments: Sequence[Shipment] = db_session.scalars(stmt).all()
        logger.info("fetch shipments table Shipment, len: %s", len(shipments))
        logger.debug("fetch shipments table Shipment, shipments: %s", shipments)
        return jsonify(shipments), 200

    except SQLAlchemyError as e:
        logger.error("fetch shipments table Shipment, error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "get_shipments_error")}), 500


@shipment_bp.route("/api/shipment/grouped-shipments", methods=["GET"])
@token_required
def get_grouped_shipments_list() -> Tuple[Response, int]:
    shipment_payroll_code_param: str | None = request.args.get("shipment_payroll_code")
    shipment_payroll_code = None

    # If shipment_payroll_code_param is provided, validate it
    if shipment_payroll_code_param:
        try:
            shipment_payroll_code = int(shipment_payroll_code_param)

            # Validate that the shipment_payroll exists in the database
            stmt_shipment_payroll = select(ShipmentPayroll).where(
                ShipmentPayroll.payroll_code == shipment_payroll_code,
                ShipmentPayroll.deleted == False,
                ShipmentPayroll.modification_user == request.current_user.user_id,
            )

            shipment_payroll = db_session.scalar(stmt_shipment_payroll)
            if not shipment_payroll:
                logger.error(
                    "ShipmentPayroll with code %s not found", shipment_payroll_code
                )
                return (
                    jsonify(
                        {"message": get_message(MESSAGES, "shipment_payroll_not_found")}
                    ),
                    404,
                )

        except ValueError:
            logger.error("Invalid 'shipment_payroll_code' parameter: not an integer")
            return (
                jsonify(
                    {"message": get_message(MESSAGES, "invalid_shipment_payroll_param")}
                ),
                400,
            )

    try:
        stmt_shipment = (
            select(Shipment)
            .where(
                Shipment.deleted == False,
                Shipment.modification_user == request.current_user.user_id,
            )
            .order_by(
                Shipment.shipment_date,
                Shipment.shipment_code,
                Shipment.route_code,
                Shipment.product_code,
            )
        )

        if shipment_payroll_code:
            stmt_shipment = stmt_shipment.where(
                Shipment.shipment_payroll_code == shipment_payroll_code
            )

        shipments: Sequence[Shipment] = db_session.scalars(stmt_shipment).all()
        result = shipment_list_to_grouped_shipments_list(shipments)

        logger.info(
            "fetch shipments table Shipment and aggregated, len: %s", len(shipments)
        )
        logger.debug(
            "fetch shipments table Shipment and aggregated, response: %s", shipments
        )
        return jsonify(result), 200

    except SQLAlchemyError as e:
        logger.error("fetch shipments table Shipment and aggregated, error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "get_shipments_error")}), 500


@shipment_bp.route("/api/shipment", methods=["POST"])
@token_required
def post_shipment() -> Tuple[Response, int]:
    try:
        shipment_dict = request.get_json()
        driver_code: int | None = shipment_dict["driver_code"]

        driver_payroll_stmt = (
            select(DriverPayroll.payroll_code)
            .where(
                DriverPayroll.driver_code == driver_code,
                DriverPayroll.deleted == False,
                DriverPayroll.paid == False,
                DriverPayroll.modification_user == request.current_user.user_id,
            )
            .order_by(
                desc(DriverPayroll.payroll_timestamp), desc(DriverPayroll.payroll_code)
            )
        )
        driver_payroll_code = db_session.scalar(driver_payroll_stmt)
        if driver_payroll_code is None:
            logger.error("update table Shipment, driver_payroll_code not found")
            return (
                jsonify({"message": get_message(MESSAGES, "driver_no_payrolls")}),
                404,
            )

        shipment_dict["driver_payroll_code"] = driver_payroll_code

        # json to db object
        payload = Shipment(
            **{**shipment_dict, "modification_user": request.current_user.user_id}
        )

        # add to database
        logger.debug("insert table Shipment, payload: %s", payload)
        db_session.add(payload)

        db_session.commit()
        logger.info("inserted table Shipment, shipment: %s", payload.shipment_code)
        return (
            jsonify(
                {**asdict(payload), "message": get_message(MESSAGES, "shipment_added")}
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("insert table Shipment, invalid shipment error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "invalid_shipment_data")}), 500

    except OperationalError as e:
        db_session.rollback()
        logger.error("insert table Shipment, connection error: %s", e)
        return (
            jsonify(
                {
                    "message": get_message(MESSAGES, "add_shipment_error")
                    + ": "
                    + get_message(MESSAGES, "connection_error")
                }
            ),
            503,
        )

    except IntegrityError as e:
        db_session.rollback()
        error_message = str(e)
        logger.error("insert table Shipment, error: %s", e)

        # Check for duplicate entry error
        if (
            "Duplicate entry" in error_message
            and "unique_driver_ticket_date" in error_message
        ):
            return (
                jsonify({"message": get_message(MESSAGES, "duplicate_shipment")}),
                400,
            )

        return (
            jsonify({"message": get_message(MESSAGES, "data_integrity_error")}),
            400,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("insert table Shipment, error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "add_shipment_error")}), 500


@shipment_bp.route("/api/shipment/<int:shipment_code>", methods=["PUT"])
@token_required
def put_shipment(shipment_code: int) -> Tuple[Response, int]:
    try:
        # get entry to update
        stmt = select(Shipment).where(
            Shipment.shipment_code == shipment_code,
            Shipment.modification_user == request.current_user.user_id,
        )
        entry_to_update: Optional[Shipment] = db_session.scalar(stmt)

        if entry_to_update is None:
            logger.error("update table Shipment, shipment not found")
            return (
                jsonify({"message": get_message(MESSAGES, "shipment_not_found")}),
                404,
            )

        ## UPDATE: DRIVER PAYROLL
        shipment_dict = request.get_json()
        driver_code: int | None = shipment_dict["driver_code"]

        driver_payroll_stmt = (
            select(DriverPayroll.payroll_code)
            .where(
                DriverPayroll.driver_code == driver_code,
                DriverPayroll.deleted == False,
                DriverPayroll.paid == False,
                DriverPayroll.modification_user == request.current_user.user_id,
            )
            .order_by(
                desc(DriverPayroll.payroll_timestamp), desc(DriverPayroll.payroll_code)
            )
        )
        driver_payroll_code = db_session.scalar(driver_payroll_stmt)
        if driver_payroll_code is None:
            logger.error("update table Shipment, driver_payroll_code not found")
            return (
                jsonify({"message": get_message(MESSAGES, "driver_no_payrolls")}),
                404,
            )

        shipment_dict["driver_payroll_code"] = driver_payroll_code

        # json to db object
        payload = Shipment(
            **{**shipment_dict, "modification_user": request.current_user.user_id}
        )

        entry_to_update.shipment_date = payload.shipment_date

        entry_to_update.driver_name = payload.driver_name
        entry_to_update.truck_plate = payload.truck_plate
        entry_to_update.trailer_plate = payload.trailer_plate
        entry_to_update.driver_code = payload.driver_code

        entry_to_update.product_code = payload.product_code
        entry_to_update.product_name = payload.product_name

        entry_to_update.route_code = payload.route_code
        entry_to_update.origin = payload.origin
        entry_to_update.destination = payload.destination
        entry_to_update.price = payload.price
        entry_to_update.payroll_price = payload.payroll_price

        entry_to_update.dispatch_code = payload.dispatch_code
        entry_to_update.receipt_code = payload.receipt_code
        entry_to_update.origin_weight = payload.origin_weight
        entry_to_update.destination_weight = payload.destination_weight
        entry_to_update.shipment_payroll_code = payload.shipment_payroll_code
        entry_to_update.driver_payroll_code = payload.driver_payroll_code
        entry_to_update.deleted = payload.deleted
        entry_to_update.modification_user = payload.modification_user

        logger.info("update table Shipment, payload: %s", entry_to_update)

        db_session.commit()
        logger.info("updated table Shipment, shipment: %s", shipment_code)
        return (
            jsonify(
                {
                    **asdict(entry_to_update),
                    "message": get_message(MESSAGES, "shipment_updated"),
                }
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("update table Shipment, invalid shipment error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "invalid_shipment_data")}), 500

    except OperationalError as e:
        db_session.rollback()
        logger.error("update table Shipment, connection error: %s", e)

        return (
            jsonify(
                {
                    "message": get_message(MESSAGES, "update_shipment_error")
                    + ": "
                    + get_message(MESSAGES, "connection_error")
                }
            ),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("update table Shipment, error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "update_shipment_error")}), 500


@shipment_bp.route("/api/shipments/change-payroll", methods=["PATCH"])
@token_required
def shipments_change_shipment_payroll() -> Tuple[Response, int]:
    shipment_payroll_code_param: str | None = request.args.get("shipment_payroll_code")
    shipment_payroll_code = None

    # If shipment_payroll_code_param is provided, validate it
    if shipment_payroll_code_param:
        try:
            shipment_payroll_code = int(shipment_payroll_code_param)

            # Validate that the shipment_payroll exists in the database
            stmt_shipment_payroll = select(ShipmentPayroll).where(
                ShipmentPayroll.payroll_code == shipment_payroll_code,
                ShipmentPayroll.deleted == False,
                ShipmentPayroll.modification_user == request.current_user.user_id,
            )

            shipment_payroll = db_session.scalar(stmt_shipment_payroll)
            if not shipment_payroll:
                logger.error(
                    "ShipmentPayroll with code %s not found", shipment_payroll_code
                )
                return (
                    jsonify(
                        {"message": get_message(MESSAGES, "shipment_payroll_not_found")}
                    ),
                    404,
                )

        except ValueError:
            logger.error("Invalid 'shipment_payroll_code' parameter: not an integer")
            return (
                jsonify(
                    {"message": get_message(MESSAGES, "invalid_shipment_payroll_param")}
                ),
                400,
            )

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
                    "driverPayroll with code %s not found", driver_payroll_code
                )
                return (
                    jsonify(
                        {"message": get_message(MESSAGES, "driver_payroll_not_found")}
                    ),
                    404,
                )

        except ValueError:
            logger.error("Invalid 'driver_payroll_code' parameter: not an integer")
            return (
                jsonify(
                    {"message": get_message(MESSAGES, "invalid_driver_payroll_param")}
                ),
                400,
            )

    try:
        # Get payload from request
        shipment_codes = request.get_json()

        # Validate payload
        if not shipment_codes or not isinstance(shipment_codes, list):
            return jsonify({"message": get_message(MESSAGES, "invalid_payload")}), 400

        # Find all shipments that belong to the current user
        stmt = select(Shipment).where(
            Shipment.shipment_code.in_(shipment_codes),
            Shipment.modification_user == request.current_user.user_id,
        )
        shipments_to_update = db_session.scalars(stmt).all()

        if not shipments_to_update:
            logger.error("move shipments, no shipments found")
            return (
                jsonify(
                    {"message": get_message(MESSAGES, "shipments_not_found_to_update")}
                ),
                404,
            )

        # Track successfully updated shipments
        updated_shipment_codes = []

        # Update shipment_payroll_code for each shipment
        for shipment in shipments_to_update:
            if shipment_payroll_code:
                shipment.shipment_payroll_code = shipment_payroll_code

            if driver_payroll_code:
                shipment.driver_payroll_code = driver_payroll_code

            shipment.modification_user = request.current_user.user_id
            updated_shipment_codes.append(shipment.shipment_code)

        db_session.commit()

        logger.info(
            "Updated shipment_payroll_code to %s for shipments: %s",
            shipment_payroll_code,
            updated_shipment_codes,
        )

        return (
            jsonify(
                {
                    "message": get_message(MESSAGES, "shipments_updated"),
                }
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("move shipments, invalid data error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "invalid_shipment_data")}), 400

    except OperationalError as e:
        db_session.rollback()
        logger.error("move shipments, connection error: %s", e)
        return (
            jsonify(
                {
                    "message": get_message(MESSAGES, "update_shipments_error")
                    + ": "
                    + get_message(MESSAGES, "connection_error")
                }
            ),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("move shipments, database error: %s", e)
        return (
            jsonify({"message": get_message(MESSAGES, "update_shipments_error")}),
            500,
        )


@shipment_bp.route("/api/shipment/<int:shipment_code>", methods=["DELETE"])
@token_required
def delete_shipment(shipment_code: int) -> Tuple[Response, int]:
    try:
        stmt = select(Shipment).where(
            Shipment.shipment_code == shipment_code,
            Shipment.modification_user == request.current_user.user_id,
        )
        existing_entry: Optional[Shipment] = db_session.scalar(stmt)

        if existing_entry is None:
            logger.error("delete table Shipment, shipment not found")
            return (
                jsonify({"message": get_message(MESSAGES, "shipment_not_found")}),
                404,
            )

        existing_entry.deleted = True
        existing_entry.modification_user = request.current_user.user_id
        db_session.commit()
        logger.info("delete table Shipment, shipment: %s", shipment_code)
        return jsonify({"message": get_message(MESSAGES, "shipment_deleted")}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table Shipment, connection error: %s", e)
        return (
            jsonify(
                {
                    "message": get_message(MESSAGES, "delete_shipment_error")
                    + ": "
                    + get_message(MESSAGES, "connection_error")
                }
            ),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table Shipment, error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "delete_shipment_error")}), 500


@shipment_bp.route("/api/shipments", methods=["DELETE"])
@token_required
def delete_shipment_list() -> Tuple[Response, int]:
    if (request.data is None) or (not request.is_json):
        logger.error("delete shipments table Shipment, shipment list is empty")
        return (
            jsonify(
                {"message": get_message(MESSAGES, "shipment_not_found_for_delete")}
            ),
            404,
        )

    shipment_list: List[int] = request.get_json()
    logger.debug("delete shipments table Shipment, payload: %s", shipment_list)

    try:
        for shipment_code in shipment_list:
            stmt = select(Shipment).where(
                Shipment.shipment_code == shipment_code,
                Shipment.modification_user == request.current_user.user_id,
            )
            shipment: Optional[Shipment] = db_session.scalar(stmt)

            if shipment is None:
                return (
                    jsonify(
                        {
                            "message": get_message(
                                MESSAGES, "shipment_not_found_for_delete"
                            )
                        }
                    ),
                    404,
                )

            shipment.deleted = True
            shipment.modification_user = request.current_user.user_id
            logger.info("delete table Shipment, shipment: %s", shipment_code)

        db_session.commit()
        return jsonify({"message": get_message(MESSAGES, "shipment_deleted")}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table Shipment, connection error: %s", e)
        return (
            jsonify(
                {
                    "message": get_message(MESSAGES, "delete_shipment_error")
                    + ": "
                    + get_message(MESSAGES, "connection_error")
                }
            ),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table Shipment, error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "delete_shipment_error")}), 500


def fetch_shipments_export_data() -> (
    Tuple[Optional[List[Shipment]], Optional[int], str, int]
):
    """Fetch the shipments to export, shared by the Excel and PDF exports.

    Reads the optional 'shipment_payroll_code' query param. Returns the
    shipments, the payroll code, an empty message key and 200, or None with
    the message key and HTTP status of the failure.
    """
    shipment_payroll_code_param: str | None = request.args.get("shipment_payroll_code")
    shipment_payroll_code = None

    # If shipment_payroll_code_param is provided, validate it
    if shipment_payroll_code_param:
        try:
            shipment_payroll_code = int(shipment_payroll_code_param)

            # Validate that the shipment_payroll exists in the database
            stmt_shipment_payroll = select(ShipmentPayroll).where(
                ShipmentPayroll.payroll_code == shipment_payroll_code,
                ShipmentPayroll.deleted == False,
                ShipmentPayroll.modification_user == request.current_user.user_id,
            )

            shipment_payroll = db_session.scalar(stmt_shipment_payroll)
            if not shipment_payroll:
                logger.error(
                    "ShipmentPayroll with code %s not found", shipment_payroll_code
                )
                return None, None, "shipment_payroll_not_found", 404

        except ValueError:
            logger.error("Invalid 'shipment_payroll_code' parameter: not an integer")
            return None, None, "invalid_shipment_payroll_param", 400

    try:
        stmt_shipment = (
            select(Shipment)
            .where(
                Shipment.deleted == False,
                Shipment.modification_user == request.current_user.user_id,
                Shipment.shipment_payroll_code == shipment_payroll_code,
            )
            .order_by(
                Shipment.route_code,
                Shipment.product_code,
                Shipment.shipment_date,
                Shipment.shipment_code,
            )
        )

        if shipment_payroll_code:
            stmt_shipment = stmt_shipment.where(
                Shipment.shipment_payroll_code == shipment_payroll_code
            )
        shipments: List[Shipment] = list(db_session.scalars(stmt_shipment).all())

        if len(shipments) <= 0:
            logger.error("export Shipments, fetch Shipments returned empty list")
            return None, None, "excel_no_data", 500

    except SQLAlchemyError as e:
        logger.error("export Shipments, fetch Shipments error: %s", e)
        return None, None, "excel_creation_error", 500

    return shipments, shipment_payroll_code, "", 200


@shipment_bp.route("/api/shipments/export-excel", methods=["GET"])
@token_required
def export_shipments_excel() -> Tuple[Response, int]:
    shipments, shipment_payroll_code, error_key, status = fetch_shipments_export_data()
    if shipments is None:
        return jsonify({"message": get_message(MESSAGES, error_key)}), status

    # dict for subtotals
    subtotal_groups: dict[str, str | int] = {}
    default_group = {
        "product": "",
        "origin": 0,
        "destination": 0,
        "diff": "",
        "tol": "",
        "diff_tol": "",
        "subtotal": "",
        "last_entry": "",
        "last_row": 0,
    }

    group_counter = 6
    first_row = 0
    for shipment in shipments:
        group = f"R{shipment.route_code}|P{shipment.product_code}"

        if group not in subtotal_groups:
            group_counter += 1
            subtotal_groups[group] = default_group.copy()
            first_row = group_counter
            subtotal_groups[group]["product"] = shipment.product_name

        subtotal_groups[group]["origin"] += shipment.origin_weight
        subtotal_groups[group]["destination"] += shipment.destination_weight
        subtotal_groups[group]["diff"] = f"=SUM(L{first_row}:L{group_counter})"
        subtotal_groups[group]["tol"] = f"=SUM(M{first_row}:M{group_counter})"
        subtotal_groups[group]["diff_tol"] = f"=SUM(N{first_row}:N{group_counter})"
        subtotal_groups[group]["subtotal"] = f"=SUM(P{first_row}:P{group_counter})"
        subtotal_groups[group]["last_entry"] = (
            shipment.dispatch_code + "|" + shipment.receipt_code
        )
        subtotal_groups[group]["last_row"] = group_counter

        group_counter += 1

    # Create Excel file in memory
    output = io.BytesIO()
    workbook = Workbook()
    sheet = workbook.active

    sheet.column_dimensions["A"].width = 2.64
    sheet.column_dimensions["B"].width = 11.00
    sheet.column_dimensions["C"].width = 20.55
    sheet.column_dimensions["D"].width = 9.09
    sheet.column_dimensions["E"].width = 11.82
    sheet.column_dimensions["F"].width = 18.64
    sheet.column_dimensions["G"].width = 17.64
    sheet.column_dimensions["H"].width = 9.91
    sheet.column_dimensions["I"].width = 9.91
    sheet.column_dimensions["J"].width = 10.91
    sheet.column_dimensions["K"].width = 11.09
    sheet.column_dimensions["L"].width = 7.18
    sheet.column_dimensions["M"].width = 6.27
    sheet.column_dimensions["N"].width = 6.36
    sheet.column_dimensions["O"].width = 6.27
    sheet.column_dimensions["P"].width = 14.64

    # Add a blank row
    sheet.append([])
    # Add company name row
    sheet.append([get_message(MESSAGES, "company_name")])

    # Get the range of columns with values None
    column_start = 1  # Cambiar al índice de la primera columna con valor None
    column_end = 16  # Cambiar al índice de la última columna con valor None

    # Merge cells in the column range
    sheet.merge_cells(
        start_row=sheet.max_row,
        start_column=column_start,
        end_row=sheet.max_row,
        end_column=column_end,
    )

    # Center content in the merged cell
    merged_cell = sheet.cell(row=sheet.max_row, column=column_start)
    merged_cell.alignment = Alignment(horizontal="center", vertical="center")

    # Apply desired font style (Arial Black, size 22, purple color)
    # Using a standard purple color index
    font = Font(name="Arial Black", size=22, color="800080")
    merged_cell.font = font

    sheet.row_dimensions[2].height = 35

    sheet.append([])  # Add a blank row after the date
    sheet.append([None, datetime.now().strftime("%d/%m/%Y")])
    sheet.append([])  # Add a blank row after the date

    # Get translated headers
    headers = [
        get_message(MESSAGES, "num"),
        get_message(MESSAGES, "date"),
        get_message(MESSAGES, "driver"),
        get_message(MESSAGES, "plate"),
        get_message(MESSAGES, "product"),
        get_message(MESSAGES, "origin"),
        get_message(MESSAGES, "destination"),
        get_message(MESSAGES, "dispatch"),
        get_message(MESSAGES, "ticket"),
        get_message(MESSAGES, "origin_weight"),
        get_message(MESSAGES, "destination_weight"),
        get_message(MESSAGES, "difference"),
        get_message(MESSAGES, "tolerance"),
        get_message(MESSAGES, "difference_tolerance"),
        get_message(MESSAGES, "price"),
        get_message(MESSAGES, "total"),
    ]
    sheet.append(headers)

    # Apply borders and fill to header cells
    for col_idx, _ in enumerate(headers, start=1):
        col_letter = get_column_letter(col_idx)
        cell = sheet[f"{col_letter}6"]

        # Apply borders
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )
        cell.border = thin_border

        # Apply fill with Gold, Accent 4, Lighter 40% color
        fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
        cell.fill = fill

        # Apply vertical and horizontal alignment in the cell
        cell.alignment = Alignment(horizontal="left", vertical="bottom")

    sheet.row_dimensions[6].height = 30

    # Add data rows
    index = 1
    counter = 7
    for shipment in shipments:
        row = [
            index,
            shipment.shipment_date.strftime("%d/%m/%Y"),
            shipment.driver_name,
            shipment.truck_plate,
            shipment.product_name,
            shipment.origin,
            shipment.destination,
            shipment.dispatch_code,
            shipment.receipt_code,
            shipment.origin_weight,
            shipment.destination_weight,
            f"=+K{counter}-J{counter}",
            f"=ROUND(K{counter}*0.002, 0)",
            f"=+M{counter}+L{counter}",
            shipment.price,
            f"=ROUND(K{counter}*O{counter}, 0)",
        ]
        sheet.append(row)

        for col in range(9, 17):
            cell = sheet.cell(row=sheet.max_row, column=col)

            if col == 15:
                cell.number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED2
            else:
                cell.number_format = "#,##0"

        for col in range(1, 17):
            cell = sheet.cell(row=sheet.max_row, column=col)
            thin_border = Border(
                left=Side(style="thin"),
                right=Side(style="thin"),
                top=Side(style="thin"),
                bottom=Side(style="thin"),
            )
            cell.border = thin_border

        group = f"R{shipment.route_code}|P{shipment.product_code}"
        if (
            subtotal_groups[group]["last_entry"]
            == shipment.dispatch_code + "|" + shipment.receipt_code
        ):
            counter += 1

            sheet.append(
                [
                    get_message(MESSAGES, "subtotal"),
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    subtotal_groups[group]["origin"],
                    subtotal_groups[group]["destination"],
                    subtotal_groups[group]["diff"],
                    subtotal_groups[group]["tol"],
                    subtotal_groups[group]["diff_tol"],
                    None,
                    subtotal_groups[group]["subtotal"],
                ]
            )

            # Get the range of columns with None values
            column_start = 1
            column_end = 9

            # Merge cells in the column range
            sheet.merge_cells(
                start_row=sheet.max_row,
                start_column=column_start,
                end_row=sheet.max_row,
                end_column=column_end,
            )

            # Center content in the merged cell
            merged_cell = sheet.cell(row=sheet.max_row, column=column_start)
            merged_cell.alignment = Alignment(horizontal="center", vertical="center")

            # Format columns 8 to 15 as numbers
            for col in range(10, 17):
                cell = sheet.cell(row=sheet.max_row, column=col)

                if col == 15:
                    cell.number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED2
                else:
                    cell.number_format = "#,##0"

            for col in range(1, 17):
                cell = sheet.cell(row=sheet.max_row, column=col)
                thin_border = Border(
                    left=Side(style="thin"),
                    right=Side(style="thin"),
                    top=Side(style="thin"),
                    bottom=Side(style="thin"),
                )
                cell.border = thin_border

                # Apply fill with Gray, Accent 4, Lighter 60% color
                fill = PatternFill(
                    start_color="969696", end_color="969696", fill_type="solid"
                )
                cell.fill = fill

        counter += 1
        index += 1

    total = {
        "origin": "=",
        "destination": "=",
        "diff": "=",
        "tol": "=",
        "diff_tol": "=",
        "total": "=",
        "products": {},
    }
    last_row = None
    for _, subtotal_group in subtotal_groups.items():
        last_row = subtotal_group["last_row"] + 1

        total["origin"] += f"+J{last_row}"
        total["destination"] += f"+K{last_row}"
        total["diff"] += f"+L{last_row}"
        total["tol"] += f"+M{last_row}"
        total["diff_tol"] += f"+N{last_row}"
        subtotal_row = f"+P{last_row}"
        total["total"] += subtotal_row

        product = subtotal_group["product"]
        if product not in total["products"]:
            total["products"][product] = "="

        total["products"][product] += subtotal_row

    sheet.append(
        [
            get_message(MESSAGES, "total_row"),
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            total["origin"],
            total["destination"],
            total["diff"],
            total["tol"],
            total["diff_tol"],
            None,
            total["total"],
        ]
    )

    # Get the range of columns with None values
    column_start = 1
    column_end = 9

    # Merge cells in the column range
    sheet.merge_cells(
        start_row=sheet.max_row,
        start_column=column_start,
        end_row=sheet.max_row,
        end_column=column_end,
    )

    # Center content in the merged cell
    merged_cell = sheet.cell(row=sheet.max_row, column=column_start)
    merged_cell.alignment = Alignment(horizontal="center", vertical="center")

    # Format columns 8 to 15 as numbers
    for col in range(10, 17):
        cell = sheet.cell(row=sheet.max_row, column=col)

        if col == 15:
            cell.number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED2
        else:
            cell.number_format = "#,##0"

    for col in range(1, 17):
        cell = sheet.cell(row=sheet.max_row, column=col)
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )
        cell.border = thin_border

        fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
        cell.fill = fill

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
            None,
            None,
            None,
            None,
            None,
            None,
            f"=+P{last_row + 1}/11",
        ]
    )
    cell = sheet.cell(row=sheet.max_row, column=16)
    cell.number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED2

    sheet.append([])
    for product, subtotal in total["products"].items():
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
                None,
                None,
                None,
                None,
                None,
                product,
                subtotal,
            ]
        )
        cell = sheet.cell(row=sheet.max_row, column=16)
        cell.number_format = "#,##0"

    # Save Excel file to output stream
    workbook.save(output)
    output.seek(0)

    # Get translated filename component
    collection_term = get_message(MESSAGES, "collection")

    # Create client response with Excel file
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response.headers["Content-Disposition"] = (
        f'attachment; filename={collection_term}_{shipment_payroll_code or "todos"}.xlsx'
    )
    logger.info("Shipment Excel file exported: %s", shipment_payroll_code)

    return response, 200


@shipment_bp.route("/api/shipments/export-pdf", methods=["GET"])
@token_required
def export_shipments_pdf() -> Tuple[Response, int]:
    shipments, shipment_payroll_code, error_key, status = fetch_shipments_export_data()
    if shipments is None:
        return jsonify({"message": get_message(MESSAGES, error_key)}), status

    try:
        pdf_file = render_shipments_pdf(shipments)
    except LayoutError as e:
        logger.error("export Shipments pdf, render error: %s", e)
        return jsonify({"message": get_message(MESSAGES, "pdf_creation_error")}), 500

    # Get translated filename component
    collection_term = get_message(MESSAGES, "collection")

    # Create client response with PDF file
    response = make_response(pdf_file)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = (
        f'attachment; filename={collection_term}_{shipment_payroll_code or "todos"}.pdf'
    )
    logger.info("Shipment PDF file exported: %s", shipment_payroll_code)

    return response, 200


def render_shipments_pdf(shipments: List[Shipment]) -> bytes:
    """Render the collection sheet (planilla de cobranza) as a PDF file.

    Mirrors the Excel export, but every Excel formula is calculated here
    because a PDF can only hold the resulting values.
    """
    locale = get_locale()

    # Same column layout as the Excel export, widths in Excel character units
    column_widths = [
        2.64,
        11.00,
        20.55,
        9.09,
        11.82,
        18.64,
        17.64,
        9.91,
        9.91,
        10.91,
        11.09,
        7.18,
        6.27,
        6.36,
        6.27,
        14.64,
    ]
    last_column = len(column_widths) - 1
    subtotal_label_end_column = 8

    header_row: List[Any] = [
        pdf_cell(get_message(MESSAGES, key), bold=True, align="center")
        for key in [
            "num",
            "date",
            "driver",
            "plate",
            "product",
            "origin",
            "destination",
            "dispatch",
            "ticket",
            "origin_weight",
            "destination_weight",
            "difference",
            "tolerance",
            "difference_tolerance",
            "price",
            "total",
        ]
    ]

    table_data: List[List[Any]] = [header_row]
    subtotal_row_indexes: List[int] = []

    subtotal_text = get_message(MESSAGES, "subtotal")
    empty_totals = {
        "origin_weight": Decimal(0),
        "destination_weight": Decimal(0),
        "difference": Decimal(0),
        "tolerance": Decimal(0),
        "difference_tolerance": Decimal(0),
        "total": Decimal(0),
    }

    def totals_row(label: str, totals: dict[str, Decimal]) -> List[Any]:
        return (
            [pdf_cell(label, bold=True, align="center")]
            + [""] * subtotal_label_end_column
            + [
                pdf_cell(format_number(totals[key], locale), bold=True, align="right")
                for key in [
                    "origin_weight",
                    "destination_weight",
                    "difference",
                    "tolerance",
                    "difference_tolerance",
                ]
            ]
            + [
                "",
                pdf_cell(
                    format_number(totals["total"], locale), bold=True, align="right"
                ),
            ]
        )

    group_totals = empty_totals.copy()
    grand_totals = empty_totals.copy()
    product_totals: dict[str, Decimal] = {}
    current_group: Optional[str] = None
    index = 1

    for position, shipment in enumerate(shipments):
        group = f"R{shipment.route_code}|P{shipment.product_code}"

        if current_group is not None and group != current_group:
            table_data.append(totals_row(subtotal_text, group_totals))
            subtotal_row_indexes.append(len(table_data) - 1)
            group_totals = empty_totals.copy()

        current_group = group

        difference = shipment.destination_weight - shipment.origin_weight
        tolerance = round_amount(shipment.destination_weight * Decimal("0.002"))
        difference_tolerance = tolerance + difference
        total = round_amount(shipment.destination_weight * shipment.price)

        table_data.append(
            [
                pdf_cell(index, align="center"),
                pdf_cell(shipment.shipment_date.strftime("%d/%m/%Y")),
                pdf_cell(shipment.driver_name),
                pdf_cell(shipment.truck_plate),
                pdf_cell(shipment.product_name),
                pdf_cell(shipment.origin),
                pdf_cell(shipment.destination),
                pdf_cell(shipment.dispatch_code),
                pdf_cell(shipment.receipt_code),
                pdf_cell(format_number(shipment.origin_weight, locale), align="right"),
                pdf_cell(
                    format_number(shipment.destination_weight, locale), align="right"
                ),
                pdf_cell(format_number(difference, locale), align="right"),
                pdf_cell(format_number(tolerance, locale), align="right"),
                pdf_cell(format_number(difference_tolerance, locale), align="right"),
                pdf_cell(
                    format_number(shipment.price, locale, decimals=2), align="right"
                ),
                pdf_cell(format_number(total, locale), align="right"),
            ]
        )

        row_values = {
            "origin_weight": shipment.origin_weight,
            "destination_weight": shipment.destination_weight,
            "difference": difference,
            "tolerance": tolerance,
            "difference_tolerance": difference_tolerance,
            "total": total,
        }
        for key, value in row_values.items():
            group_totals[key] += value
            grand_totals[key] += value

        product_totals[shipment.product_name] = (
            product_totals.get(shipment.product_name, Decimal(0)) + total
        )

        # The last shipment closes the last group
        if position == len(shipments) - 1:
            table_data.append(totals_row(subtotal_text, group_totals))
            subtotal_row_indexes.append(len(table_data) - 1)

        index += 1

    table_data.append(totals_row(get_message(MESSAGES, "total_row"), grand_totals))
    total_row_index = len(table_data) - 1

    # VAT row, the Excel export divides the grand total by 11
    vat_row: List[Any] = [""] * last_column + [
        pdf_cell(
            format_number(grand_totals["total"] / 11, locale, decimals=2), align="right"
        )
    ]
    table_data.append(vat_row)
    vat_row_index = len(table_data) - 1

    for product, product_total in product_totals.items():
        table_data.append(
            [""] * (last_column - 1)
            + [
                pdf_cell(product),
                pdf_cell(format_number(product_total, locale), align="right"),
            ]
        )

    table = Table(table_data, colWidths=scale_widths(column_widths), repeatRows=1)

    style: List[Any] = [
        ("GRID", (0, 0), (-1, total_row_index), 0.4, GRID_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 1),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BACKGROUND),
        ("BACKGROUND", (0, total_row_index), (-1, total_row_index), HEADER_BACKGROUND),
        ("SPAN", (0, total_row_index), (subtotal_label_end_column, total_row_index)),
        (
            "GRID",
            (last_column, vat_row_index),
            (last_column, vat_row_index),
            0.4,
            GRID_COLOR,
        ),
        (
            "GRID",
            (last_column - 1, vat_row_index + 1),
            (last_column, -1),
            0.4,
            GRID_COLOR,
        ),
    ]
    for row_index in subtotal_row_indexes:
        style.append(
            ("BACKGROUND", (0, row_index), (-1, row_index), SUBTOTAL_BACKGROUND)
        )
        style.append(("SPAN", (0, row_index), (subtotal_label_end_column, row_index)))

    table.setStyle(TableStyle(style))

    company_name = get_message(MESSAGES, "company_name")

    return build_pdf(
        [
            Paragraph(company_name, ACCENT_TITLE_STYLE),
            Spacer(1, 6),
            Paragraph(datetime.now().strftime("%d/%m/%Y"), SUBTITLE_STYLE),
            Spacer(1, 6),
            table,
        ],
        company_name,
    )
