import io
from typing import Optional, Sequence, Tuple, List
from dataclasses import asdict

from flask import request, jsonify, Response, make_response
from sqlalchemy import select, desc
from sqlalchemy.sql import extract
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import numbers, Border, Side
from openpyxl.utils import get_column_letter

from app_config import logger, app, db_session, RequestWithUser
from decorators.token_required import token_required
from models.shipment_payroll import ShipmentPayroll

request: RequestWithUser


@app.route("/api/shipment-payroll/<int:payroll_code>", methods=["GET"])
@token_required
def get_shipment_payroll(payroll_code: int) -> Tuple[Response, int]:
    try:
        stmt = select(ShipmentPayroll).where(
            ShipmentPayroll.payroll_code == payroll_code,
            ShipmentPayroll.deleted == False,
            ShipmentPayroll.modification_user == request.current_user.user_id,
        )

        shipment_payroll: Optional[ShipmentPayroll] = db_session.scalar(stmt)
        if shipment_payroll is None:
            logger.error("fetch table ShipmentPayroll, not found")
            return jsonify({"message": "No se encontró la planilla"}), 404

        logger.info(
            "fetch table ShipmentPayroll, found: %s", shipment_payroll.payroll_code
        )
        logger.debug("fetch table ShipmentPayroll, found: %s", shipment_payroll)

        return jsonify(shipment_payroll), 200

    except SQLAlchemyError as e:
        logger.error("fetch table ShipmentPayroll, error: %s", e)
        return jsonify({"message": "Error de transacción"}), 500


@app.route("/api/shipment-payrolls", methods=["GET"])
@token_required
def get_shipment_payroll_list() -> Tuple[Response, int]:
    year_param: str | None = request.args.get("year")
    try:
        year: Optional[int] = int(year_param) if year_param else None
    except ValueError as e:
        logger.error("Invalid 'year' parameter %s", e)
        return jsonify({"message": "Parámetros inválidos"}), 400

    try:
        stmt = select(ShipmentPayroll).where(
            ShipmentPayroll.deleted == False,
            ShipmentPayroll.modification_user == request.current_user.user_id,
        )

        if year:
            stmt = stmt.where(
                extract("year", ShipmentPayroll.payroll_timestamp) == year
            )

        stmt = stmt.order_by(desc(ShipmentPayroll.payroll_timestamp))

        shipment_payrolls: Sequence[ShipmentPayroll] = db_session.scalars(stmt).all()
        logger.info(
            "fetch shipment payrolls table ShipmentPayroll, len: %s",
            len(shipment_payrolls),
        )
        logger.debug(
            "fetch shipment payrolls table ShipmentPayroll, payrolls: %s",
            shipment_payrolls,
        )
        return jsonify(shipment_payrolls), 200

    except SQLAlchemyError as e:
        logger.error("fetch shipment payrolls table ShipmentPayroll, error: %s", e)
        return jsonify({"message": "Error al obtener planillas"}), 500


@app.route("/api/shipment-payroll", methods=["POST"])
@token_required
def post_shipment_payroll() -> Tuple[Response, int]:
    try:
        # json to db object
        payload = ShipmentPayroll(
            **request.get_json(), modification_user=request.current_user.user_id
        )

        # add to database
        logger.debug("insert table ShipmentPayroll, payload: %s", payload)
        db_session.add(payload)

        db_session.commit()
        logger.info("inserted table ShipmentPayroll, payroll: %s", payload.payroll_code)
        return (
            jsonify({**asdict(payload), "message": "Planilla agregada exitosamente"}),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("insert table ShipmentPayroll, invalid payroll error: %s", e)
        return jsonify({"message": f"Error, datos de la Planilla inválidos ({e})"}), 500

    except OperationalError as e:
        db_session.rollback()
        logger.error("insert table ShipmentPayroll, connection error: %s", e)
        return (
            jsonify({"message": "Error al agregar planilla: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("insert table ShipmentPayroll, error: %s", e)
        return jsonify({"message": "Error al agregar planilla"}), 500


@app.route("/api/shipment-payroll/<int:payroll_code>", methods=["PUT"])
@token_required
def put_shipment_payroll(payroll_code: int) -> Tuple[Response, int]:
    try:
        # get entry to update
        stmt = select(ShipmentPayroll).where(
            ShipmentPayroll.payroll_code == payroll_code,
            ShipmentPayroll.modification_user == request.current_user.user_id,
        )
        entry_to_update: Optional[ShipmentPayroll] = db_session.scalar(stmt)

        if entry_to_update is None:
            logger.error("update table ShipmentPayroll, payroll not found")
            return jsonify({"message": "Planilla no encontrada"}), 404

        # json to db object
        payload = ShipmentPayroll(
            **request.get_json(), modification_user=request.current_user.user_id
        )

        entry_to_update.payroll_timestamp = payload.payroll_timestamp
        entry_to_update.collected = payload.collected
        entry_to_update.collection_timestamp = payload.collection_timestamp
        entry_to_update.deleted = payload.deleted
        entry_to_update.modification_user = payload.modification_user

        logger.info("update table ShipmentPayroll, payload: %s", entry_to_update)

        db_session.commit()
        logger.info("updated table ShipmentPayroll, payroll: %s", payroll_code)
        return (
            jsonify(
                {
                    **asdict(entry_to_update),
                    "message": "Planilla actualizada exitosamente",
                }
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("invalid payroll: %s", e)
        return jsonify({"message": f"Error, datos de la Planilla inválidos ({e})"}), 500

    except OperationalError as e:
        db_session.rollback()
        logger.error("update table ShipmentPayroll: connection error %s", e)
        return (
            jsonify({"message": "Error al actualizar planilla: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("update table ShipmentPayroll, error: %s", e)
        return jsonify({"message": "Error al actualizar planilla"}), 500


@app.route(
    "/api/shipment-payroll/<int:payroll_code>/collection-status", methods=["PATCH"]
)
@token_required
def update_shipment_payroll_collection_status(
    payroll_code: int,
) -> Tuple[Response, int]:
    try:
        # Get the entry to update
        stmt = select(ShipmentPayroll).where(
            ShipmentPayroll.payroll_code == payroll_code,
            ShipmentPayroll.modification_user == request.current_user.user_id,
        )
        entry_to_update: Optional[ShipmentPayroll] = db_session.scalar(stmt)

        if entry_to_update is None:
            logger.error(
                "update collection status, payroll not found: %s", payroll_code
            )
            return jsonify({"message": "Planilla no encontrada"}), 404

        # Get the payload
        payload = request.get_json()

        if "collected" not in payload:
            logger.error("update collection status, missing collected field")
            return jsonify({"message": "Campo 'collected' requerido"}), 400

        # Update only the collection-related fields
        entry_to_update.collected = payload["collected"]
        # Set collection_timestamp to current timestamp if collected, otherwise set to None
        if payload["collected"]:
            entry_to_update.collection_timestamp = datetime.now()
        else:
            entry_to_update.collection_timestamp = None

        entry_to_update.modification_user = request.current_user.user_id

        logger.info(
            "update collection status, payroll: %s, status: %s",
            payroll_code,
            "collected" if entry_to_update.collected else "uncollected",
        )

        db_session.commit()

        return (
            jsonify(
                {
                    **asdict(entry_to_update),
                    "message": f"Estado de cobranza actualizado a {'cobrado' if entry_to_update.collected else 'no cobrado'}",
                }
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("invalid collection status update: %s", e)
        return jsonify({"message": f"Error, datos inválidos ({e})"}), 400

    except OperationalError as e:
        db_session.rollback()
        logger.error("update collection status: connection error %s", e)
        return (
            jsonify(
                {
                    "message": "Error al actualizar estado de cobranza: problema de conexión"
                }
            ),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("update collection status, error: %s", e)
        return jsonify({"message": "Error al actualizar estado de cobranza"}), 500


@app.route("/api/shipment-payroll/<int:payroll_code>", methods=["DELETE"])
@token_required
def delete_shipment_payroll(payroll_code: int) -> Tuple[Response, int]:
    try:
        stmt = select(ShipmentPayroll).where(
            ShipmentPayroll.payroll_code == payroll_code,
            ShipmentPayroll.modification_user == request.current_user.user_id,
        )
        existing_entry: Optional[ShipmentPayroll] = db_session.scalar(stmt)

        if existing_entry is None:
            logger.error("delete table ShipmentPayroll, payroll not found")
            return jsonify({"message": "Planilla no encontrada"}), 404

        existing_entry.deleted = True
        existing_entry.modification_user = request.current_user.user_id
        db_session.commit()
        logger.info("delete table ShipmentPayroll: payroll %s", payroll_code)
        return jsonify({"message": "Planilla eliminada exitosamente"}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table ShipmentPayroll, connection error: %s", e)
        return (
            jsonify({"message": "Error al eliminar planilla: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table ShipmentPayroll, error: %s", e)
        return jsonify({"message": "Error al eliminar planilla"}), 500


@app.route("/api/shipment-payrolls", methods=["DELETE"])
@token_required
def delete_shipment_payrolls() -> Tuple[Response, int]:
    if (request.data is None) or (not request.is_json):
        logger.error("delete payrolls table ShipmentPayroll, payroll list is empty")
        return (
            jsonify({"message": "Error al eliminar planilla: planilla no encontrada"}),
            404,
        )

    payroll_list: List[int] = request.get_json()
    logger.debug("delete payrolls table ShipmentPayroll, payload: %s", payroll_list)

    try:
        for payroll_code in payroll_list:
            stmt = select(ShipmentPayroll).where(
                ShipmentPayroll.payroll_code == payroll_code,
                ShipmentPayroll.modification_user == request.current_user.user_id,
            )
            payroll: Optional[ShipmentPayroll] = db_session.scalar(stmt)

            if payroll is None:
                return (
                    jsonify(
                        {
                            "message": "Error al eliminar planilla: planilla no encontrada"
                        }
                    ),
                    404,
                )

            payroll.deleted = True
            payroll.modification_user = request.current_user.user_id
            logger.info("delete table ShipmentPayroll, payroll: %s", payroll_code)

        db_session.commit()
        return jsonify({"message": "Planilla eliminada exitosamente"}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table ShipmentPayroll: connection error %s", e)
        return (
            jsonify({"message": "Error al eliminar planilla: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table ShipmentPayroll, error: %s", e)
        return jsonify({"message": "Error al eliminar planilla"}), 500


@app.route("/api/export-shipment-payrolls", methods=["GET"])
@token_required
def export_shipment_payrolls() -> Tuple[Response, int]:
    # Get date range parameters
    start_date_str = request.args.get("startDate", "")
    end_date_str = request.args.get("endDate", "")

    try:
        # Convert date parameters as needed
        start_date = datetime.fromisoformat(start_date_str) if start_date_str else None
        end_date = datetime.fromisoformat(end_date_str) if end_date_str else None

        # Build query for shipment payrolls in date range
        stmt = select(ShipmentPayroll).where(
            ShipmentPayroll.deleted == False,
            ShipmentPayroll.modification_user == request.current_user.user_id,
        )

        if start_date:
            stmt = stmt.where(ShipmentPayroll.payroll_timestamp >= start_date)
        if end_date:
            stmt = stmt.where(ShipmentPayroll.payroll_timestamp <= end_date)

        stmt = stmt.order_by(desc(ShipmentPayroll.payroll_timestamp))

        payroll_list: Sequence[ShipmentPayroll] = db_session.scalars(stmt).all()

        if not payroll_list:
            logger.warning("export ShipmentPayrolls, no data found in date range")
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
            collection_date = (
                payroll.collection_timestamp.strftime("%d/%m/%Y")
                if payroll.collection_timestamp
                else ""
            )

            row = [
                payroll.payroll_code,
                payroll_date,
                "Sí" if payroll.collected else "No",
                collection_date,
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
            "attachment; filename=lista_de_cobranzas.xlsx"
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
