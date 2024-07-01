from flask import request
from flask import jsonify
from flask import Response

from typing import Dict
from typing import Sequence
from typing import Tuple

from sqlalchemy import select
from sqlalchemy import asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import OperationalError

from app_config import logger
from app_config import app

from models import Driver


from app_config import db_session

from dataclasses import asdict


@app.route('/driver/<int:driver_code>', methods=['GET'])
def get_driver(driver_code: int) -> Tuple[Response, int]:
    current_user = ''
    company_id = ''
    try:
        stmt = select(Driver).where(
            Driver.driver_code == driver_code, Driver.deleted == False,
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
            Driver.deleted == False,
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


def validated_driver_payload() -> Dict[str, str] | None:
    if ((request.data is None) or (not request.is_json)):
        logger.error("[POST|PATCH /driver] Driver payload is empty")
        return None

    payload: Dict[str, str] = request.get_json()
    logger.debug("[POST|PATCH /driver] payload: %s", payload)

    required_fields = ['driver_id', 'driver_name',
                       'driver_surname', 'truck_plate', 'trailer_plate']
    for field in required_fields:
        if field not in payload:
            logger.error(
                "[POST|PATCH /driver] payload missing field: %s", field)
            return None

    return payload


@app.route('/driver', methods=['POST'])
def post_driver() -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    validated_payload = validated_driver_payload()
    if (validated_payload is None):
        return jsonify({"error": "Error al recibir datos de conductor"}), 500

    new_driver = Driver(
        driver_id=validated_payload['driver_id'],
        driver_name=validated_payload['driver_name'],
        driver_surname=validated_payload['driver_surname'],
        truck_plate=validated_payload['truck_plate'],
        trailer_plate=validated_payload['trailer_plate'],
        modification_user=current_user,
        company_id=company_id
    )

    try:
        db_session.add(new_driver)
        db_session.commit()
        logger.info("[POST /driver] adding to table Driver: %s", new_driver)
        return jsonify(
            {
                **asdict(new_driver),
                "success": "Conductor agregado exitosamente"
            }), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("[POST /driver] adding to table Driver: connection %s", e)

        return jsonify({"error": "Error al agregar driver: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("[POST /driver] adding to table Driver: %s", e)
        return jsonify({"error": "Error al agregar conductor"}), 500


@app.route('/driver/<int:driver_code>', methods=['PATCH'])
def patch_driver(driver_code: int) -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    validated_payload = validated_driver_payload()
    if (validated_payload is None):
        return jsonify({"error": "Error al recibir datos de conductor"}), 500

    existing_entry: Driver | None = db_session.get(Driver, driver_code)
    if existing_entry is None:
        return jsonify({'error': 'Conductor no encontrado'}), 404

    if existing_entry.company_id != company_id:
        logger.error(
            "[PATCH /driver] updating table Driver: invalid company_id: %s", company_id)
        return jsonify({"error": "Error al actualizar conductor"}), 503

    try:
        existing_entry.driver_id = validated_payload['driver_id']
        existing_entry.driver_name = validated_payload['driver_name']
        existing_entry.driver_surname = validated_payload['driver_surname']
        existing_entry.truck_plate = validated_payload['truck_plate']
        existing_entry.trailer_plate = validated_payload['trailer_plate']
        existing_entry.modification_user = current_user

        db_session.commit()
        logger.info("[PATCH /driver] updating table Driver: %s", driver_code)
        return jsonify(
            {
                **asdict(existing_entry),
                "success": "Conductor actualizada exitosamente"
            }), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error(
            "[PATCH /driver] updating table Driver: connection %s", e)

        return jsonify({"error": "Error al actualizar conductor: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("[PATCH /driver] updating table Driver: %s", e)
        return jsonify({"error": "Error al actualizar conductor"}), 500


@app.route('/driver/<int:driver_code>', methods=['DELETE'])
def delete_driver(driver_code: int) -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    existing_entry: Driver | None = db_session.get(Driver, driver_code)
    if existing_entry is None:
        return jsonify({'error': 'Conductor no encontrado'}), 404

    if existing_entry.company_id != company_id:
        logger.error(
            "[PATCH /driver] deleting table Driver: invalid company_id: %s", company_id)
        return jsonify({"error": "Error al eliminar conductor"}), 503

    try:
        existing_entry.deleted = True
        existing_entry.modification_user = current_user
        db_session.commit()
        logger.info(
            "[DELETE /driver] deleting from table Driver: %s", driver_code)
        return jsonify({'success': 'Conductor eliminada exitosamente'}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error(
            "[DELETE /driver] deleting table driver: connection %s", e)
        return jsonify({"error": "Error al eliminar conductor: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("[DELETE /driver] deleting table Driver: %s", e)
        return jsonify({"error": "Error al eliminar conductor"}), 500
