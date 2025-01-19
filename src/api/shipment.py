from flask import request
from flask import jsonify
from flask import Response

from typing import Sequence
from typing import Tuple
from typing import Optional
from typing import List

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import OperationalError

from app_config import logger
from app_config import app

from models import Shipment

from app_config import db_session

from dataclasses import asdict


@app.route('/shipment/<int:shipment_code>', methods=['GET'])
def get_shipment(shipment_code: int) -> Tuple[Response, int]:
    current_user = 'dyrtransportes'
    company_id = 'dyrtransportes'
    try:
        stmt = select(Shipment).where(
            Shipment.shipment_code == shipment_code,
            Shipment.deleted == False,
            Shipment.company_id == company_id
        )

        shipment_payroll: Optional[Shipment] = db_session.scalar(stmt)
        if shipment_payroll is None:
            logger.error(
                "[GET /shipment] fetching from table Shipment not found")
            return jsonify({"error": "No se encontró la Carga"}), 404

        logger.info(
            "[GET /shipment] fetching from table Shipment found: %s", shipment_payroll.shipment_code)
        logger.debug(
            "[GET /shipment] fetching from table Shipment found: %s", shipment_payroll)

        return jsonify(shipment_payroll), 200

    except SQLAlchemyError as e:
        logger.error(
            "[GET /shipment] fetching from table Shipment %s", e)
        return jsonify({"error": "Error de transacción"}), 500


@app.route('/shipments', methods=['GET'])
def get_shipment_list() -> Tuple[Response, int]:
    company_id = 'dyrtransportes'
    current_user = 'dyrtransportes'

    shipment_payroll_code_param: str | None = request.args.get(
        'shipment_payroll_code')
    try:
        shipment_payroll_code: Optional[int] = int(
            shipment_payroll_code_param) if shipment_payroll_code_param else None
    except ValueError as e:
        logger.error(
            "[GET /shipment-payrolls] Invalid 'shipment_payroll_code' parameter %s", e)
        return jsonify({"error": "Parámetros inválidos"}), 400

    try:
        stmt = select(Shipment).where(
            Shipment.deleted == False,
            Shipment.company_id == company_id,
        )

        if shipment_payroll_code:
            stmt = stmt.where(Shipment.shipment_payroll_code ==
                              shipment_payroll_code)

        shipments: Sequence[Shipment] = db_session.scalars(
            stmt).all()
        logger.info(
            "[GET /shipments] fetching shipments from table Shipment len: %s", len(shipments))
        logger.debug(
            "[GET /shipments] fetching shipments from table Shipment: %s", shipments)
        return jsonify(shipments), 200

    except SQLAlchemyError as e:
        logger.error(
            "[GET /shipments] fetching shipments from table Shipment %s", e)
        return jsonify({"error": "Error al obtener planillas"}), 500


@app.route('/shipment', methods=['POST'])
def post_shipment() -> Tuple[Response, int]:
    current_user = 'dyrtransportes'
    company_id = 'dyrtransportes'

    try:
        payload = Shipment(**request.get_json(),
                           modification_user=current_user, company_id=company_id)

        db_session.add(payload)
        db_session.commit()
        logger.info(
            "[POST /shipment] adding to table Shipment: %s", payload)
        return jsonify(
            {
                **asdict(payload),
                "success": "Carga agregada exitosamente"
            }), 200

    except (TypeError, ValueError, KeyError) as e:
        logger.error("[POST /shipment] Invalid payload: %s", e)
        return jsonify({"error": f"Error, datos de la Carga inválidos ({e})"}), 500

    except OperationalError as e:
        db_session.rollback()
        logger.error(
            "[POST /shipment] adding to table Shipment: connection %s", e)

        return jsonify({"error": "Error al agregar Carga: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error(
            "[POST /shipment] adding to table Shipment: %s", e)
        return jsonify({"error": "Error al agregar Carga"}), 500


@app.route('/shipment/<int:shipment_code>', methods=['PUT'])
def put_shipment(shipment_code: int) -> Tuple[Response, int]:
    current_user = 'dyrtransportes'
    company_id = 'dyrtransportes'

    try:
        entry_to_update: Optional[Shipment] = db_session.get(
            Shipment, shipment_code)
        if entry_to_update is None:
            return jsonify({'error': 'Carga no encontrada'}), 404

        if entry_to_update.company_id != company_id:
            logger.error(
                "[PUT /shipment] updating table Shipment: invalid company_id: %s", company_id)
            return jsonify({"error": "Error al actualizar Carga"}), 503

        payload = Shipment(**request.get_json(),
                           modification_user=current_user, company_id=company_id)

        entry_to_update.shipment_date = payload.shipment_date
        entry_to_update.driver_code = payload.driver_code
        entry_to_update.product_code = payload.product_code
        entry_to_update.route_code = payload.route_code
        entry_to_update.price = payload.price
        entry_to_update.payroll_price = payload.payroll_price
        entry_to_update.dispatch_code = payload.dispatch_code
        entry_to_update.receipt_code = payload.receipt_code
        entry_to_update.origin_weight = payload.origin_weight
        entry_to_update.destination_weight = payload.destination_weight
        entry_to_update.shipment_payroll_code = payload.shipment_payroll_code
        entry_to_update.driver_payroll_code = payload.driver_payroll_code
        entry_to_update.deleted = payload.deleted

        db_session.commit()
        logger.info(
            "[PUT /shipment] updating table Shipment: %s", shipment_code)
        return jsonify(
            {
                **asdict(entry_to_update),
                "success": "Planilla actualizada exitosamente"
            }), 200

    except (TypeError, ValueError, KeyError) as e:
        logger.error("[PUT /shipment] Invalid payload: %s", e)
        return jsonify({"error": f"Error, datos del planilla inválidos ({e})"}), 500

    except OperationalError as e:
        db_session.rollback()
        logger.error(
            "[PUT /shipment] updating table Shipment: connection %s", e)

        return jsonify({"error": "Error al actualizar planilla: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error(
            "[PUT /shipment] updating table Shipment: %s", e)
        return jsonify({"error": "Error al actualizar planilla"}), 500


@app.route('/shipment/<int:shipment_code>', methods=['DELETE'])
def delete_shipment(shipment_code: int) -> Tuple[Response, int]:
    current_user = 'dyrtransportes'
    company_id = 'dyrtransportes'

    try:
        existing_entry: Optional[Shipment] = db_session.get(
            Shipment, shipment_code)
        if existing_entry is None:
            return jsonify({'error': 'Carga no encontrado'}), 404

        if existing_entry.company_id != company_id:
            logger.error(
                "[DELETE /shipment] deleting table Shipment: invalid company_id: %s", company_id)
            return jsonify({"error": "Error al eliminar Carga"}), 503

        existing_entry.deleted = True
        existing_entry.modification_user = current_user
        db_session.commit()
        logger.info(
            "[DELETE /shipment] deleting table Shipment: %s", shipment_code)
        return jsonify({'success': 'Carga eliminada exitosamente'}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error(
            "[DELETE /shipment] deleting table Shipment: connection %s", e)
        return jsonify({"error": "Error al eliminar Carga: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error(
            "[DELETE /shipment] deleting table Shipment: %s", e)
        return jsonify({"error": "Error al eliminar Carga"}), 500


@app.route('/shipments', methods=['DELETE'])
def delete_shipment_list() -> Tuple[Response, int]:
    current_user = 'dyrtransportes'
    company_id = 'dyrtransportes'

    if ((request.data is None) or (not request.is_json)):
        logger.error(
            "[DELETE /shipment] Shipment list payload is empty")
        return jsonify({'error': 'Error al eliminar Carga: Carga no encontrado'}), 404

    shipment_list: List[int] = request.get_json()
    logger.debug(
        "[DELETE /shipment] shipment_list: %s", shipment_list)

    try:
        for shipment_code in shipment_list:
            shipment: Optional[Shipment] = db_session.get(
                Shipment, shipment_code)

            if shipment is None:
                return jsonify({'error': 'Error al eliminar Carga: Carga no encontrado'}), 404

            if shipment.company_id != company_id:
                logger.error(
                    "[DELETE /shipment] deleting from table Shipment: invalid company_id: %s", company_id)
                return jsonify({"error": "Error al eliminar Carga"}), 503

            shipment.deleted = True
            shipment.modification_user = current_user
            logger.info(
                "[DELETE /shipment] deleting from table Shipment: %s", shipment_code)

        db_session.commit()
        return jsonify({'success': 'Carga eliminada exitosamente'}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error(
            "[DELETE /shipment] deleting table Shipment: connection %s", e)
        return jsonify({"error": "Error al eliminar Carga: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error(
            "[DELETE /shipment] deleting table Shipment: %s", e)
        return jsonify({"error": "Error al eliminar Carga"}), 500
