import io
from datetime import datetime
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import List

from dataclasses import asdict

from flask import request
from flask import jsonify
from flask import Response
from flask import make_response

from sqlalchemy import select
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import OperationalError

from openpyxl import Workbook
from openpyxl.styles import Border
from openpyxl.styles import Side
from openpyxl.utils import get_column_letter

from app_config import logger
from app_config import app
from app_config import db_session
from app_config import RequestWithUser

from decorators.token_required import token_required

from models.driver_payroll import DriverPayroll
from models.driver import Driver
from models.shipment import Shipment

request: RequestWithUser


@app.route("/api/driver-payroll/<int:payroll_code>", methods=["GET"])
@token_required
def get_driver_payroll(payroll_code: int) -> Tuple[Response, int]:
    try:
        stmt = select(DriverPayroll).where(
            DriverPayroll.payroll_code == payroll_code,
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
    driver_payroll_code_param: str | None = request.args.get("driver_payroll_code")

    try:
        stmt = (
            select(DriverPayroll, Driver)
            .join(Driver, DriverPayroll.driver_code == Driver.driver_code)
            .where(
                DriverPayroll.deleted == False,
                DriverPayroll.modification_user == request.current_user.user_id,
            )
            .order_by(asc(DriverPayroll.payroll_timestamp))
        )

        results = db_session.execute(stmt).all()

        # Create file
        output = io.BytesIO()
        workbook = Workbook(write_only=False, iso_dates=False)
        sheet = workbook.active

        headers = ["Código", "Fecha", "Chofer", "Estado de Pago", "Fecha de Pago"]
        sheet.append(headers)

        for col_idx in range(1, len(headers) + 1):
            sheet.column_dimensions[get_column_letter(col_idx)].width = 20

        # Estilo de borde
        border_style = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        # Aplicar el estilo de borde a cada celda en la fila
        for cell in sheet[sheet.max_row]:
            cell.border = border_style

        # Agregar filas de datos
        for payroll, driver in results:
            row = [
                payroll.payroll_code,
                payroll.payroll_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                f"{driver.driver_name} {driver.driver_surname}",
                "Pagado" if payroll.paid else "No Pagado",
                (
                    payroll.paid_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    if payroll.paid_timestamp
                    else ""
                ),
            ]

            sheet.append(row)

            # Aplicar el estilo de borde a cada celda en la fila
            for cell in sheet[sheet.max_row]:
                cell.border = border_style

        # Guardar el archivo Excel en el flujo de salida
        workbook.save(output)
        output.seek(0)

        # Crear la respuesta para el cliente con el archivo Excel
        response = make_response(output.getvalue())
        response.headers["Content-Type"] = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response.headers["Content-Disposition"] = (
            "attachment; filename=liquidaciones_de_choferes.xlsx"
        )

        logger.info("exported DriverPayrolls excel file")

        return response, 200

    except SQLAlchemyError as e:
        logger.error("export DriverPayrolls, error: %s", e)
        return jsonify({"message": "Error al enviar archivo Excel"}), 500
