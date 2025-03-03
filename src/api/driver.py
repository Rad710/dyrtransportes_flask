import io

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
from sqlalchemy import asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import OperationalError

from openpyxl import Workbook
from openpyxl.styles import numbers, Border, Side
from openpyxl.utils import get_column_letter

from app_config import logger
from app_config import app
from app_config import db_session
from app_config import RequestWithUser

from decorators.token_required import token_required

from models.driver import Driver

request: RequestWithUser


@app.route("/api/driver/<int:driver_code>", methods=["GET"])
@token_required
def get_driver(driver_code: int) -> Tuple[Response, int]:
    try:
        stmt = select(Driver).where(
            Driver.driver_code == driver_code,
            Driver.modification_user == request.current_user.user_id,
        )

        driver: Optional[Driver] = db_session.scalar(stmt)
        if driver is None:
            logger.error("fetch table Driver, not found")
            return jsonify({"message": "No se encontró el chofer"}), 404

        logger.info("fetch table Driver, found: %s", driver.driver_code)
        logger.debug("fetch table Driver, found: %s", driver)

        return jsonify(driver), 200

    except SQLAlchemyError as e:
        logger.error("fetch table Driver, error: %s", e)
        return jsonify({"message": "Error de transacción"}), 500


@app.route("/api/drivers", methods=["GET"])
@token_required
def get_driver_list() -> Tuple[Response, int]:
    try:
        stmt = (
            select(Driver)
            .where(
                Driver.modification_user == request.current_user.user_id,
            )
            .order_by(asc(Driver.driver_name), asc(Driver.driver_surname))
        )

        drivers: Sequence[Driver] = db_session.scalars(stmt).all()
        logger.info("fetch drivers table Driver, len: %s", len(drivers))
        logger.debug("fetch drivers table Driver, drivers: %s", drivers)
        return jsonify(drivers), 200

    except SQLAlchemyError as e:
        logger.error("fetch drivers table Driver, error: %s", e)
        return jsonify({"message": "Error al obtener choferes"}), 500


@app.route("/api/driver", methods=["POST"])
@token_required
def post_driver() -> Tuple[Response, int]:
    try:
        # json to db object
        payload = Driver(
            **request.get_json(), modification_user=request.current_user.user_id
        )

        # add to database
        logger.debug("insert table Driver, payload: %s", payload)
        db_session.add(payload)

        db_session.commit()
        logger.info("inserted table Driver, driver: %s", payload.driver_code)
        return (
            jsonify({**asdict(payload), "message": "Chofer agregado exitosamente"}),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("insert table Driver, invalid driver error: %s", e)
        return jsonify({"message": f"Error, datos del Chofer inválidos ({e})"}), 500

    except OperationalError as e:
        db_session.rollback()
        logger.error("insert table Driver, connection error: %s", e)

        return (
            jsonify({"message": "Error al agregar chofer: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("insert table Driver, error: %s", e)
        return jsonify({"message": "Error al agregar chofer"}), 500


@app.route("/api/driver/<int:driver_code>", methods=["PUT"])
@token_required
def put_driver(driver_code: int) -> Tuple[Response, int]:
    try:
        # get entry to update
        stmt = select(Driver).where(
            Driver.driver_code == driver_code,
            Driver.modification_user == request.current_user.user_id,
        )
        entry_to_update: Optional[Driver] = db_session.scalar(stmt)

        if entry_to_update is None:
            logger.error("update table Driver, driver not found")
            return jsonify({"message": "Chofer no encontrado"}), 404

        # json to db object
        payload = Driver(
            **request.get_json(), modification_user=request.current_user.user_id
        )

        entry_to_update.driver_id = payload.driver_id
        entry_to_update.driver_name = payload.driver_name
        entry_to_update.driver_surname = payload.driver_surname
        entry_to_update.truck_plate = payload.truck_plate
        entry_to_update.trailer_plate = payload.trailer_plate
        entry_to_update.modification_user = payload.modification_user

        logger.info("update table Driver, payload: %s", entry_to_update)

        db_session.commit()
        logger.info("updated table Driver, driver: %s", driver_code)
        return (
            jsonify(
                {
                    **asdict(entry_to_update),
                    "message": "Chofer actualizado exitosamente",
                }
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("invalid driver: %s", e)
        return jsonify({"message": f"Error, datos del Chofer inválidos ({e})"}), 500

    except OperationalError as e:
        db_session.rollback()
        logger.error("update table Driver: connection error %s", e)

        return (
            jsonify({"message": "Error al actualizar chofer: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("update table Driver, error: %s", e)
        return jsonify({"message": "Error al actualizar chofer"}), 500


@app.route("/api/driver/<int:driver_code>/active-status", methods=["PATCH"])
@token_required
def update_driver_active_status(
    driver_code: int,
) -> Tuple[Response, int]:
    try:
        # Get the entry to update
        stmt = select(Driver).where(
            Driver.driver_code == driver_code,
            Driver.modification_user == request.current_user.user_id,
        )
        entry_to_update: Optional[Driver] = db_session.scalar(stmt)

        if entry_to_update is None:
            logger.error(
                "update driver active status, Driver not found: %s", driver_code
            )
            return jsonify({"message": "Chofer no encontrado"}), 404

        # Get the payload
        payload = request.get_json()

        if "deleted" not in payload:
            logger.error("update deleted status, missing deleted field")
            return jsonify({"message": "Campo 'deleted' requerido"}), 400

        entry_to_update.deleted = payload["deleted"]
        entry_to_update.modification_user = request.current_user.user_id

        logger.info(
            "update deleted status, Driver: %s, status: %s",
            driver_code,
            "deleted" if entry_to_update.deleted else "active",
        )

        db_session.commit()

        return (
            jsonify(
                {
                    **asdict(entry_to_update),
                    "message": f"Estado de Chofer a {'desactivado' if entry_to_update.deleted else 'activo'}",
                }
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("invalid deleted status update: %s", e)
        return jsonify({"message": f"Error, datos inválidos ({e})"}), 400

    except OperationalError as e:
        db_session.rollback()
        logger.error("update deleted status: connection error %s", e)
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
        logger.error("update deleted status, error: %s", e)
        return jsonify({"message": "Error al actualizar estado de cobranza"}), 500


@app.route("/api/driver/<int:driver_code>", methods=["DELETE"])
@token_required
def delete_driver(driver_code: int) -> Tuple[Response, int]:
    try:
        stmt = select(Driver).where(
            Driver.driver_code == driver_code,
            Driver.modification_user == request.current_user.user_id,
        )
        existing_entry: Optional[Driver] = db_session.scalar(stmt)

        if existing_entry is None:
            logger.error("delete table Driver, driver not found")
            return jsonify({"message": "Chofer no encontrado"}), 404

        existing_entry.deleted = True
        existing_entry.modification_user = request.current_user.user_id
        db_session.commit()
        logger.info("delete table Driver: driver %s", driver_code)
        return jsonify({"message": "Chofer eliminado exitosamente"}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table Driver, connection error: %s", e)
        return (
            jsonify({"message": "Error al eliminar chofer: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table Driver, error: %s", e)
        return jsonify({"message": "Error al eliminar chofer"}), 500


@app.route("/api/drivers", methods=["DELETE"])
@token_required
def delete_drivers() -> Tuple[Response, int]:
    if (request.data is None) or (not request.is_json):
        logger.error("delete drivers table Driver, driver list is empty")
        return (
            jsonify({"message": "Error al eliminar chofer: chofer no encontrado"}),
            404,
        )

    driver_list: List[int] = request.get_json()
    logger.debug("delete drivers table Driver, payload: %s", driver_list)

    try:
        for driver_code in driver_list:
            stmt = select(Driver).where(
                Driver.driver_code == driver_code,
                Driver.modification_user == request.current_user.user_id,
            )
            driver: Optional[Driver] = db_session.scalar(stmt)

            if driver is None:
                return (
                    jsonify(
                        {"message": "Error al eliminar chofer: chofer no encontrado"}
                    ),
                    404,
                )

            driver.deleted = True
            driver.modification_user = request.current_user.user_id
            logger.info("delete table Driver, driver: %s", driver_code)

        db_session.commit()
        return jsonify({"message": "Chofer eliminado exitosamente"}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table Driver: connection error %s", e)
        return (
            jsonify({"message": "Error al eliminar chofer: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table Driver, error: %s", e)
        return jsonify({"message": "Error al eliminar chofer"}), 500


@app.route("/api/driver/<int:driver_code>", methods=["PATCH"])
@token_required
def restore_driver(driver_code: int) -> Tuple[Response, int]:
    try:
        stmt = select(Driver).where(
            Driver.driver_code == driver_code,
            Driver.modification_user == request.current_user.user_id,
        )
        existing_entry: Optional[Driver] = db_session.scalar(stmt)

        if existing_entry is None:
            logger.error("restore table Driver, driver not found")
            return jsonify({"message": "Chofer no encontrado"}), 404

        existing_entry.deleted = False
        existing_entry.modification_user = request.current_user.user_id
        db_session.commit()
        logger.info("restore table Driver: driver %s", driver_code)
        return jsonify({"message": "Chofer restaurado exitosamente"}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("restore table Driver, connection error: %s", e)
        return (
            jsonify({"message": "Error al restaurar chofer: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("restore table Driver, error: %s", e)
        return jsonify({"message": "Error al restaurar chofer"}), 500


@app.route("/api/export-drivers", methods=["GET"])
@token_required
def export_drivers() -> Tuple[Response, int]:
    try:
        stmt = (
            select(Driver)
            .where(
                Driver.deleted == False,
                Driver.modification_user == request.current_user.user_id,
            )
            .order_by(asc(Driver.driver_name), asc(Driver.driver_surname))
        )

        driver_list: Sequence[Driver] = db_session.scalars(stmt).all()

        # Create file
        output = io.BytesIO()
        workbook = Workbook(write_only=False, iso_dates=False)
        sheet = workbook.active

        headers = ["C.I.", "Nombre", "Apellido", "Chapa Camión", "Chapa Carreta"]
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
        for driver in driver_list:
            row = [
                driver.driver_id,
                driver.driver_name,
                driver.driver_surname,
                driver.truck_plate,
                driver.trailer_plate,
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
            "attachment; filename=nomina_de_choferes.xlsx"
        )

        logger.info("exported Drivers excel file")

        return response, 200

    except SQLAlchemyError as e:
        logger.error("export Drivers, error: %s", e)
        return jsonify({"message": "Error al enviar archivo Excel"}), 500
