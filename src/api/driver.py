from flask import request
from flask import jsonify
from flask import Response
from flask import make_response


from typing import Dict
from typing import Sequence
from typing import Tuple

from sqlalchemy import select
from sqlalchemy import asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import OperationalError

from typing import Any
from typing import Dict
from typing import Sequence
from typing import Tuple
from typing import List

from app_config import logger
from app_config import app

from models import Driver

import io
from openpyxl import Workbook
from openpyxl.styles import numbers, Border, Side
from openpyxl.utils import get_column_letter


from app_config import db_session

from dataclasses import asdict


@app.route('/driver/<int:driver_code>', methods=['GET'])
def get_driver(driver_code: int) -> Tuple[Response, int]:
    current_user = ''
    company_id = ''
    try:
        stmt = select(Driver).where(
            Driver.driver_code == driver_code,
            Driver.company_id == company_id
        )

        driver: Driver | None = db_session.scalar(stmt)
        if driver is None:
            logger.error("[GET /driver] fetching from table Driver not found")
            return jsonify({"error": "No se encontró al chofer"}), 404

        logger.info(
            "[GET /driver] fetching from table Driver found: %s", driver.driver_code)
        logger.debug(
            "[GET /driver] fetching from table Diver found: %s", driver)

        return jsonify(driver), 200

    except SQLAlchemyError as e:
        logger.error("[GET /driver] fetching from table Driver %s", e)
        return jsonify({"error": "Error de transacción"}), 500


@app.route('/drivers', methods=['GET'])
def get_driver_list():
    company_id = ''
    current_user = ''

    try:
        stmt = select(Driver).where(
            Driver.company_id == company_id,
        ).order_by(
            asc(Driver.driver_name), asc(Driver.driver_surname)
        )

        drivers: Sequence[Driver] = db_session.scalars(stmt).all()
        logger.info(
            "[GET /drivers] fetching drivers from table Driver len: %s", len(drivers))
        logger.debug(
            "[GET /drivers] fetching drivers from table Driver drivers: %s", drivers)
        return jsonify(drivers), 200

    except SQLAlchemyError as e:
        logger.error("[GET /drivers] fetching drivers from table Driver %s", e)
        return jsonify({"error": "Error al obtener la nómina"}), 500


@app.route('/driver', methods=['POST'])
def post_driver() -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    try:
        # json to db object
        payload = Driver(**request.get_json(),
                         modification_user=current_user, company_id=company_id)

        db_session.add(payload)
        db_session.commit()
        logger.info("[POST /driver] adding to table Driver: %s", payload)
        return jsonify(
            {
                **asdict(payload),
                "success": "Conductor agregado exitosamente"
            }), 200

    except (TypeError, ValueError, KeyError) as e:
        logger.error("[POST /driver] Invalid Driver: %s", e)
        return jsonify({"error": f"Error, datos del Chofer inválidos ({e})"}), 500

    except OperationalError as e:
        db_session.rollback()
        logger.error("[POST /driver] adding to table Driver: connection %s", e)

        return jsonify({"error": "Error al agregar driver: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("[POST /driver] adding to table Driver: %s", e)
        return jsonify({"error": "Error al agregar conductor"}), 500


@app.route('/driver/<int:driver_code>', methods=['PUT'])
def put_driver(driver_code: int) -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    try:
        existing_entry: Driver | None = db_session.get(Driver, driver_code)
        if existing_entry is None:
            return jsonify({'error': 'Conductor no encontrado'}), 404

        if existing_entry.company_id != company_id:
            logger.error(
                "[PUT /driver] updating table Driver: invalid company_id: %s", company_id)
            return jsonify({"error": "Error al actualizar conductor"}), 403

        payload = Driver(**request.get_json(),
                         modification_user=current_user, company_id=company_id)

        existing_entry.driver_id = payload.driver_id
        existing_entry.driver_name = payload.driver_name
        existing_entry.driver_surname = payload.driver_surname
        existing_entry.truck_plate = payload.truck_plate
        existing_entry.trailer_plate = payload.trailer_plate
        existing_entry.modification_user = payload.modification_user

        db_session.commit()
        logger.info("[PUT /driver] updating table Driver: %s", driver_code)
        return jsonify(
            {
                **asdict(existing_entry),
                "success": "Conductor actualizado exitosamente"
            }), 200

    except (TypeError, ValueError, KeyError) as e:
        logger.error("[PUT /driver] Invalid Driver: %s", e)
        return jsonify({"error": f"Error, datos del Chofer inválidos ({e})"}), 500

    except OperationalError as e:
        db_session.rollback()
        logger.error(
            "[PUT /driver] updating table Driver: connection %s", e)

        return jsonify({"error": "Error al actualizar conductor: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("[PUT /driver] updating table Driver: %s", e)
        return jsonify({"error": "Error al actualizar conductor"}), 500


@app.route('/driver/<int:driver_code>', methods=['DELETE'])
def delete_driver(driver_code: int) -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    try:
        existing_entry: Driver | None = db_session.get(Driver, driver_code)
        if existing_entry is None:
            return jsonify({'error': 'Conductor no encontrado'}), 404

        if existing_entry.company_id != company_id:
            logger.error(
                "[DELETE /driver] deleting table Driver: invalid company_id: %s", company_id)
            return jsonify({"error": "Error al eliminar conductor"}), 503

        existing_entry.deleted = True
        existing_entry.modification_user = current_user
        db_session.commit()
        logger.info(
            "[DELETE /driver] deleting from table Driver: %s", driver_code)
        return jsonify({'success': 'Conductor eliminado exitosamente'}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error(
            "[DELETE /driver] deleting table driver: connection %s", e)
        return jsonify({"error": "Error al eliminar conductor: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("[DELETE /driver] deleting table Driver: %s", e)
        return jsonify({"error": "Error al eliminar conductor"}), 500


@app.route('/driver/<int:driver_code>', methods=['PATCH'])
def reactivate_driver(driver_code: int) -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    try:
        existing_entry: Driver | None = db_session.get(Driver, driver_code)
        if existing_entry is None:
            return jsonify({'error': 'Conductor no encontrado'}), 404

        if existing_entry.company_id != company_id:
            logger.error(
                "[PATCH /driver] reactivating table Driver: invalid company_id: %s", company_id)
            return jsonify({"error": "Error al reactivar conductor"}), 503

        existing_entry.deleted = False
        existing_entry.modification_user = current_user
        db_session.commit()
        logger.info(
            "[PATCH /driver] reactivating from table Driver: %s", driver_code)
        return jsonify({'success': 'Conductor eliminado exitosamente'}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error(
            "[PATCH /driver] reactivating table driver: connection %s", e)
        return jsonify({"error": "Error al reactivar conductor: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("[PATCH /driver] reactivating table Driver: %s", e)
        return jsonify({"error": "Error al reactivar conductor"}), 500


@app.route('/export-drivers', methods=['GET'])
def export_drivers() -> Tuple[Response, int]:
    company_id = ''

    stmt = select(Driver).where(
        Driver.company_id == company_id,
        Driver.deleted == False,
    ).order_by(
        asc(Driver.driver_name), asc(Driver.driver_surname)
    )

    driver_list: Sequence[Driver] = db_session.scalars(stmt).all()

    logger.debug(
        "[GET /export-drivers] fetching drivers from table Driver routes: %s", driver_list)

    # Create file
    output = io.BytesIO()
    workbook = Workbook(write_only=False, iso_dates=False)
    sheet = workbook.active

    headers = ['C.I.', 'Nombre', 'Chapa Camión', 'Chapa Carreta']
    sheet.append(headers)

    for col_idx in range(1, 5):
        sheet.column_dimensions[get_column_letter(col_idx)].width = 20

    # Estilo de borde
    border_style = Border(left=Side(style='thin'),
                          right=Side(style='thin'),
                          top=Side(style='thin'),
                          bottom=Side(style='thin'))

    # Aplicar el estilo de borde a cada celda en la fila
    for cell in sheet[sheet.max_row]:
        cell.border = border_style

    # Agregar filas de datos
    for driver in driver_list:
        row = [driver.driver_id, driver.driver_name,
               driver.truck_plate, driver.trailer_plate]

        sheet.append(row)

        for i in range(3, 5):
            cell = sheet.cell(row=sheet.max_row, column=i)
            cell.number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED1  # type: ignore

        # Aplicar el estilo de borde a cada celda en la fila
        for cell in sheet[sheet.max_row]:
            cell.border = border_style

    # Guardar el archivo Excel en el flujo de salida
    workbook.save(output)
    output.seek(0)

    # Crear la respuesta para el cliente con el archivo Excel
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename=nómina_de_choferes.xlsx'

    logger.warning("Nómina de Choferes exportada")
    return response, 200
