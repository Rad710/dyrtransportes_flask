import io

from typing import Sequence
from typing import Tuple
from typing import Optional
from typing import List

from datetime import datetime

from dataclasses import asdict

from openpyxl import Workbook
from openpyxl.styles import Alignment
from openpyxl.styles import numbers
from openpyxl.styles import Border
from openpyxl.styles import Side
from openpyxl.styles import Font
from openpyxl.styles import PatternFill
from openpyxl.utils import get_column_letter

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
from app_config import app
from app_config import db_session
from app_config import RequestWithUser

from decorators.token_required import token_required

from models.shipment import Shipment
from models.api_models import shipment_list_to_grouped_shipments_list
from models.driver_payroll import DriverPayroll
from models.shipment_payroll import ShipmentPayroll

request: RequestWithUser


@app.route("/api/shipment/<int:shipment_code>", methods=["GET"])
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
            return jsonify({"message": "No se encontró la Carga"}), 404

        logger.info("fetch table Shipment, found: %s", shipment.shipment_code)
        logger.debug("fetch table Shipment, found: %s", shipment)

        return jsonify(shipment), 200

    except SQLAlchemyError as e:
        logger.error("fetch table Shipment, error: %s", e)
        return jsonify({"message": "Error de transacción"}), 500


@app.route("/api/shipments", methods=["GET"])
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
                return jsonify({"message": "Planilla de carga no encontrada"}), 404

        except ValueError:
            logger.error("Invalid 'shipment_payroll_code' parameter: not an integer")
            return (
                jsonify(
                    {
                        "message": "Parámetro 'shipment_payroll_code' debe ser un número entero"
                    }
                ),
                400,
            )

    try:
        stmt = select(Shipment).where(
            Shipment.deleted == False,
            Shipment.modification_user == request.current_user.user_id,
        )

        if shipment_payroll_code:
            stmt = stmt.where(Shipment.shipment_payroll_code == shipment_payroll_code)

        shipments: Sequence[Shipment] = db_session.scalars(stmt).all()
        logger.info("fetch shipments table Shipment, len: %s", len(shipments))
        logger.debug("fetch shipments table Shipment, shipments: %s", shipments)
        return jsonify(shipments), 200

    except SQLAlchemyError as e:
        logger.error("fetch shipments table Shipment, error: %s", e)
        return jsonify({"message": "Error al obtener planillas"}), 500


@app.route("/api/shipment/grouped-shipments", methods=["GET"])
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
                return jsonify({"message": "Planilla de carga no encontrada"}), 404

        except ValueError:
            logger.error("Invalid 'shipment_payroll_code' parameter: not an integer")
            return (
                jsonify(
                    {
                        "message": "Parámetro 'shipment_payroll_code' debe ser un número entero"
                    }
                ),
                400,
            )

    try:
        stmt_shipment = (
            select(Shipment)
            .where(
                Shipment.deleted == False,
                Shipment.modification_user == request.current_user.user_id,
                Shipment.shipment_payroll_code == shipment_payroll_code,
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
        return jsonify({"message": "Error al obtener planillas"}), 500


@app.route("/api/shipment", methods=["POST"])
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
            .order_by(desc(DriverPayroll.payroll_code))
        )
        driver_payroll_code = db_session.scalar(driver_payroll_stmt)
        shipment_dict["driver_payroll_code"] = driver_payroll_code

        # json to db object
        payload = Shipment(
            **shipment_dict,
            modification_user=request.current_user.user_id,
        )

        # add to database
        logger.debug("insert table Shipment, payload: %s", payload)
        db_session.add(payload)

        db_session.commit()
        logger.info("inserted table Shipment, shipment: %s", payload.shipment_code)
        return (
            jsonify({**asdict(payload), "message": "Carga agregada exitosamente"}),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("insert table Shipment, invalid shipment error: %s", e)
        return jsonify({"message": f"Error, datos de la Carga inválidos ({e})"}), 500

    except OperationalError as e:
        db_session.rollback()
        logger.error("insert table Shipment, connection error: %s", e)
        return jsonify({"message": "Error al agregar Carga: problema de conexión"}), 503

    except IntegrityError as e:
        db_session.rollback()
        error_message = str(e)
        logger.error("insert table Shipment, error: %s", e)

        # Check for duplicate entry error
        if (
            "Duplicate entry" in error_message
            and "unique_driver_ticket_date" in error_message
        ):
            return jsonify({"message": "Error al agregar Carga: carga duplicada"}), 400

        return (
            jsonify(
                {"message": "Error al agregar Carga: error de integridad de datos"}
            ),
            400,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("insert table Shipment, error: %s", e)
        return jsonify({"message": "Error al agregar Carga"}), 500


@app.route("/api/shipment/<int:shipment_code>", methods=["PUT"])
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
            return jsonify({"message": "Carga no encontrada"}), 404

        # json to db object
        payload = Shipment(
            **request.get_json(), modification_user=request.current_user.user_id
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
                {**asdict(entry_to_update), "message": "Carga actualizada exitosamente"}
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("update table Shipment, invalid shipment error: %s", e)
        return jsonify({"message": f"Error, datos de la Carga inválidos ({e})"}), 500

    except OperationalError as e:
        db_session.rollback()
        logger.error("update table Shipment, connection error: %s", e)

        return (
            jsonify({"message": "Error al actualizar Carga: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("update table Shipment, error: %s", e)
        return jsonify({"message": "Error al actualizar Carga"}), 500


@app.route("/api/shipments/change-shipment-payroll", methods=["PATCH"])
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
                return jsonify({"message": "Planilla de carga no encontrada"}), 404

        except ValueError:
            logger.error("Invalid 'shipment_payroll_code' parameter: not an integer")
            return (
                jsonify(
                    {
                        "message": "Parámetro 'shipment_payroll_code' debe ser un número entero"
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

        # Update shipment_payroll_code for each shipment
        for shipment in shipments_to_update:
            shipment.shipment_payroll_code = shipment_payroll_code
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


@app.route("/api/shipment/<int:shipment_code>", methods=["DELETE"])
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
            return jsonify({"message": "Carga no encontrada"}), 404

        existing_entry.deleted = True
        existing_entry.modification_user = request.current_user.user_id
        db_session.commit()
        logger.info("delete table Shipment, shipment: %s", shipment_code)
        return jsonify({"message": "Carga eliminada exitosamente"}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table Shipment, connection error: %s", e)
        return (
            jsonify({"message": "Error al eliminar Carga: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table Shipment, error: %s", e)
        return jsonify({"message": "Error al eliminar Carga"}), 500


@app.route("/api/shipments", methods=["DELETE"])
@token_required
def delete_shipment_list() -> Tuple[Response, int]:
    if (request.data is None) or (not request.is_json):
        logger.error("delete shipments table Shipment, shipment list is empty")
        return jsonify({"message": "Error al eliminar Carga: Carga no encontrada"}), 404

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
                        {"message": "Error al eliminar Carga: Carga no encontrada"}
                    ),
                    404,
                )

            shipment.deleted = True
            shipment.modification_user = request.current_user.user_id
            logger.info("delete table Shipment, shipment: %s", shipment_code)

        db_session.commit()
        return jsonify({"message": "Carga eliminada exitosamente"}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table Shipment, connection error: %s", e)
        return (
            jsonify({"message": "Error al eliminar Carga: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table Shipment, error: %s", e)
        return jsonify({"message": "Error al eliminar Carga"}), 500


@app.route("/api/shipments/export-excel", methods=["GET"])
@token_required
def export_shipments_excel() -> Tuple[Response, int]:
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
                return jsonify({"message": "Planilla de carga no encontrada"}), 404

        except ValueError:
            logger.error("Invalid 'shipment_payroll_code' parameter: not an integer")
            return (
                jsonify(
                    {
                        "message": "Parámetro 'shipment_payroll_code' debe ser un número entero"
                    }
                ),
                400,
            )

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
        shipments: Sequence[Shipment] = db_session.scalars(stmt_shipment).all()

        if shipments is None or len(shipments) <= 0:
            logger.error("export Shipments, fetch Shipments returned empty list")
            return jsonify({"message": "Error al crear archivo Excel, sin datos"}), 500

    except SQLAlchemyError as e:
        logger.error("export Shipments, fetch Shipments error: %s", e)
        return jsonify({"message": "Error al crear archivo Excel"}), 500

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

    # Agregar la fecha como la primera fila
    sheet.append([])  # Agregar una fila en blanco después de la fecha
    # Agregar una fila en blanco después de la fecha
    sheet.append(["D & R TRANSPORTES"])

    # Obtener el rango de columnas con valores None
    column_start = 1  # Cambiar al índice de la primera columna con valor None
    column_end = 16  # Cambiar al índice de la última columna con valor None

    # Combinar las celdas en el rango de columnas
    sheet.merge_cells(
        start_row=sheet.max_row,
        start_column=column_start,
        end_row=sheet.max_row,
        end_column=column_end,
    )

    # Centrar el contenido en la celda combinada
    merged_cell = sheet.cell(row=sheet.max_row, column=column_start)
    merged_cell.alignment = Alignment(horizontal="center", vertical="center")

    # Aplicar el estilo de fuente deseado (Arial Black, size 22, purple color)
    # Using a standard purple color index
    font = Font(name="Arial Black", size=22, color="800080")
    merged_cell.font = font

    sheet.row_dimensions[2].height = 35

    sheet.append([])  # Agregar una fila en blanco después de la fecha
    sheet.append([None, datetime.now().strftime("%d/%m/%Y")])
    sheet.append([])  # Agregar una fila en blanco después de la fecha

    headers = [
        "N°",
        "Fecha",
        "Chofer",
        "Chapa",
        "Producto",
        "Origen",
        "Destino",
        "Remision",
        "Tiquet",
        "Kilos Origen",
        "Kilos Destino",
        "Dif.",
        "Tolera",
        "Dif. Tol.",
        "Precio",
        "Total",
    ]
    sheet.append(headers)

    # Aplicar bordes y relleno a las celdas del encabezado
    for col_idx, _ in enumerate(headers, start=1):
        col_letter = get_column_letter(col_idx)
        cell = sheet[f"{col_letter}6"]

        # Aplicar bordes
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )
        cell.border = thin_border

        # Aplicar relleno con el color Gold, Accent 4, Lighter 40%
        fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
        cell.fill = fill

        # Aplicar alineación vertical y horizontal en la celda
        cell.alignment = Alignment(horizontal="left", vertical="bottom")

    sheet.row_dimensions[6].height = 30

    # Agregar filas de datos
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
                    "Subtotal",
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

            # Obtener el rango de columnas con valores None
            column_start = 1  # Cambiar al índice de la primera columna con valor None
            column_end = 9  # Cambiar al índice de la última columna con valor None

            # Combinar las celdas en el rango de columnas
            sheet.merge_cells(
                start_row=sheet.max_row,
                start_column=column_start,
                end_row=sheet.max_row,
                end_column=column_end,
            )

            # Centrar el contenido en la celda combinada
            merged_cell = sheet.cell(row=sheet.max_row, column=column_start)
            merged_cell.alignment = Alignment(horizontal="center", vertical="center")

            # Formatear columnas 8 a 15 como números
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

                # Aplicar relleno con el color Gray, Accent 4, Lighter 60%
                # Gray, Accent 4, Lighter 60%
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
            "TOTAL",
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

    # Obtener el rango de columnas con valores None
    column_start = 1  # Cambiar al índice de la primera columna con valor None
    column_end = 9  # Cambiar al índice de la última columna con valor None

    # Combinar las celdas en el rango de columnas
    sheet.merge_cells(
        start_row=sheet.max_row,
        start_column=column_start,
        end_row=sheet.max_row,
        end_column=column_end,
    )

    # Centrar el contenido en la celda combinada
    merged_cell = sheet.cell(row=sheet.max_row, column=column_start)
    merged_cell.alignment = Alignment(horizontal="center", vertical="center")

    # Formatear columnas 8 a 15 como números
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

    # Guardar el archivo Excel en el flujo de salida
    workbook.save(output)
    output.seek(0)

    # Crear la respuesta para el cliente con el archivo Excel
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response.headers["Content-Disposition"] = (
        f'attachment; filename="cobranza_{shipment_payroll_code or "todos"}.xlsx"'
    )
    logger.info("Shipment Excel file exported: %s", shipment_payroll_code)

    return response, 200
