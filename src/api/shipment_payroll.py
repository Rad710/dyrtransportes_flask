# from flask import request
# from flask import jsonify
# from flask import Response

# from typing import Sequence
# from typing import Tuple
# from typing import Optional
# from typing import List

# from sqlalchemy import select
# from sqlalchemy import desc
# from sqlalchemy.sql import extract
# from sqlalchemy.exc import SQLAlchemyError
# from sqlalchemy.exc import OperationalError

# from app_config import logger
# from app_config import app

# from backend_flask.src.models.old_schema import ShipmentPayroll

# from app_config import db_session

# from dataclasses import asdict


# @app.route('/shipment-payroll/<int:payroll_code>', methods=['GET'])
# def get_shipment_payroll(payroll_code: int) -> Tuple[Response, int]:
#     current_user = 'dyrtransportes'
#     company_id = 'dyrtransportes'
#     try:
#         stmt = select(ShipmentPayroll).where(
#             ShipmentPayroll.payroll_code == payroll_code,
#             ShipmentPayroll.deleted == False,
#             ShipmentPayroll.company_id == company_id
#         )

#         shipment_payroll: Optional[ShipmentPayroll] = db_session.scalar(stmt)
#         if shipment_payroll is None:
#             logger.error(
#                 "[GET /shipment-payroll] fetching from table ShipmentPayroll not found")
#             return jsonify({"error": "No se encontró la planilla"}), 404

#         logger.info(
#             "[GET /shipment-payroll] fetching from table ShipmentPayroll found: %s", shipment_payroll.payroll_code)
#         logger.debug(
#             "[GET /shipment-payroll] fetching from table ShipmentPayroll found: %s", shipment_payroll)

#         return jsonify(shipment_payroll), 200

#     except SQLAlchemyError as e:
#         logger.error(
#             "[GET /shipment-payroll] fetching from table ShipmentPayroll %s", e)
#         return jsonify({"error": "Error de transacción"}), 500


# @app.route('/shipment-payrolls', methods=['GET'])
# def get_shipment_payroll_list() -> Tuple[Response, int]:
#     company_id = 'dyrtransportes'
#     current_user = 'dyrtransportes'

#     year_param: str | None = request.args.get('year')
#     try:
#         year: Optional[int] = int(year_param) if year_param else None
#     except ValueError as e:
#         logger.error(
#             "[GET /shipment-payrolls] Invalid 'year' parameter %s", e)
#         return jsonify({"error": "Parámetros inválidos"}), 400

#     try:
#         stmt = select(ShipmentPayroll).where(
#             ShipmentPayroll.deleted == False,
#             ShipmentPayroll.company_id == company_id,
#         )

#         if year:
#             stmt = stmt.where(
#                 extract('year', ShipmentPayroll.payroll_timestamp) == year)

#         stmt = stmt.order_by(desc(ShipmentPayroll.payroll_timestamp))

#         shipment_payrolls: Sequence[ShipmentPayroll] = db_session.scalars(
#             stmt).all()
#         logger.info(
#             "[GET /shipment-payrolls] fetching shipment payrolls from table ShipmentPayroll len: %s", len(shipment_payrolls))
#         logger.debug(
#             "[GET /shipment-payrolls] fetching shipment payrolls from table ShipmentPayroll: %s", shipment_payrolls)
#         return jsonify(shipment_payrolls), 200

#     except SQLAlchemyError as e:
#         logger.error(
#             "[GET /shipment-payrolls] fetching shipment payrolls from table ShipmentPayroll %s", e)
#         return jsonify({"error": "Error al obtener planillas"}), 500


# @app.route('/shipment-payroll', methods=['POST'])
# def post_shipment_payroll() -> Tuple[Response, int]:
#     current_user = 'dyrtransportes'
#     company_id = 'dyrtransportes'

#     try:
#         payload = ShipmentPayroll(**request.get_json(),
#                                   modification_user=current_user, company_id=company_id)

#         db_session.add(payload)
#         db_session.commit()
#         logger.info(
#             "[POST /shipment-payroll] adding to table ShipmentPayroll: %s", payload)
#         return jsonify(
#             {
#                 **asdict(payload),
#                 "success": "Planilla agregada exitosamente"
#             }), 200

#     except (TypeError, ValueError, KeyError) as e:
#         logger.error("[POST /shipment-payroll] Invalid payload: %s", e)
#         return jsonify({"error": f"Error, datos de la Planilla inválidos ({e})"}), 500

#     except OperationalError as e:
#         db_session.rollback()
#         logger.error(
#             "[POST /shipment-payroll] adding to table ShipmentPayroll: connection %s", e)

#         return jsonify({"error": "Error al agregar planilla: problema de conexión"}), 503

#     except SQLAlchemyError as e:
#         db_session.rollback()
#         logger.error(
#             "[POST /hipment-payroll] adding to table ShipmentPayroll: %s", e)
#         return jsonify({"error": "Error al agregar planilla"}), 500


# @app.route('/shipment-payroll/<int:payroll_code>', methods=['PUT'])
# def put_shipment_payroll(payroll_code: int) -> Tuple[Response, int]:
#     current_user = 'dyrtransportes'
#     company_id = 'dyrtransportes'

#     try:
#         entry_to_update: Optional[ShipmentPayroll] = db_session.get(
#             ShipmentPayroll, payroll_code)
#         if entry_to_update is None:
#             return jsonify({'error': 'Planilla no encontrada'}), 404

#         if entry_to_update.company_id != company_id:
#             logger.error(
#                 "[PUT /shipment-payroll] updating table ShipmentPayroll: invalid company_id: %s", company_id)
#             return jsonify({"error": "Error al actualizar planilla"}), 503

#         payload = ShipmentPayroll(**request.get_json(),
#                                   modification_user=current_user, company_id=company_id)

#         entry_to_update.payroll_timestamp = payload.payroll_timestamp
#         entry_to_update.collected = payload.collected
#         entry_to_update.collection_timestamp = payload.collection_timestamp
#         entry_to_update.deleted = payload.deleted
#         entry_to_update.modification_user = payload.modification_user

#         db_session.commit()
#         logger.info(
#             "[PUT /shipment-payroll] updating table ShipmentPayroll: %s", payroll_code)
#         return jsonify(
#             {
#                 **asdict(entry_to_update),
#                 "success": "Planilla actualizada exitosamente"
#             }), 200

#     except (TypeError, ValueError, KeyError) as e:
#         logger.error("[PUT /shipment-payroll] Invalid payload: %s", e)
#         return jsonify({"error": f"Error, datos del planilla inválidos ({e})"}), 500

#     except OperationalError as e:
#         db_session.rollback()
#         logger.error(
#             "[PUT /shipment-payroll] updating table ShipmentPayroll: connection %s", e)

#         return jsonify({"error": "Error al actualizar planilla: problema de conexión"}), 503

#     except SQLAlchemyError as e:
#         db_session.rollback()
#         logger.error(
#             "[PUT /shipment-payroll] updating table ShipmentPayroll: %s", e)
#         return jsonify({"error": "Error al actualizar planilla"}), 500


# @app.route('/shipment-payroll/<int:payroll_code>', methods=['DELETE'])
# def delete_shipment_payroll(payroll_code: int) -> Tuple[Response, int]:
#     current_user = 'dyrtransportes'
#     company_id = 'dyrtransportes'

#     try:
#         existing_entry: Optional[ShipmentPayroll] = db_session.get(
#             ShipmentPayroll, payroll_code)
#         if existing_entry is None:
#             return jsonify({'error': 'Planilla no encontrado'}), 404

#         if existing_entry.company_id != company_id:
#             logger.error(
#                 "[DELETE /shipment-payroll] deleting table ShipmentPayroll: invalid company_id: %s", company_id)
#             return jsonify({"error": "Error al eliminar Planilla"}), 503

#         existing_entry.deleted = True
#         existing_entry.modification_user = current_user
#         db_session.commit()
#         logger.info(
#             "[DELETE /shipment-payroll] deleting table ShipmentPayroll: %s", payroll_code)
#         return jsonify({'success': 'Planilla eliminada exitosamente'}), 200

#     except OperationalError as e:
#         db_session.rollback()
#         logger.error(
#             "[DELETE /shipment-payroll] deleting table ShipmentPayroll: connection %s", e)
#         return jsonify({"error": "Error al eliminar Planilla: problema de conexión"}), 503

#     except SQLAlchemyError as e:
#         db_session.rollback()
#         logger.error(
#             "[DELETE /shipment-payroll] deleting table ShipmentPayroll: %s", e)
#         return jsonify({"error": "Error al eliminar Planilla"}), 500


# @app.route('/shipment-payrolls', methods=['DELETE'])
# def delete_shipment_payrolls() -> Tuple[Response, int]:
#     current_user = 'dyrtransportes'
#     company_id = 'dyrtransportes'

#     if ((request.data is None) or (not request.is_json)):
#         logger.error(
#             "[DELETE /shipment-payrolls] ShipmentPayroll list payload is empty")
#         return jsonify({'error': 'Error al eliminar Planilla: planilla no encontrado'}), 404

#     payroll_list: List[int] = request.get_json()
#     logger.debug(
#         "[DELETE /shipment-payrolls] shipment_payroll_list: %s", payroll_list)

#     try:
#         for payroll_code in payroll_list:
#             payroll: Optional[ShipmentPayroll] = db_session.get(
#                 ShipmentPayroll, payroll_code)

#             if payroll is None:
#                 return jsonify({'error': 'Error al eliminar planilla: planilla no encontrado'}), 404

#             if payroll.company_id != company_id:
#                 logger.error(
#                     "[DELETE /shipment-payrolls] deleting from table ShipmentPayroll: invalid company_id: %s", company_id)
#                 return jsonify({"error": "Error al eliminar planilla"}), 503

#             payroll.deleted = True
#             payroll.modification_user = current_user
#             logger.info(
#                 "[DELETE /shipment-payrolls] deleting from table ShipmentPayroll: %s", payroll_code)

#         db_session.commit()
#         return jsonify({'success': 'Planilla eliminada exitosamente'}), 200

#     except OperationalError as e:
#         db_session.rollback()
#         logger.error(
#             "[DELETE /shipment-payrolls] deleting table ShipmentPayroll: connection %s", e)
#         return jsonify({"error": "Error al eliminar Planilla: problema de conexión"}), 503

#     except SQLAlchemyError as e:
#         db_session.rollback()
#         logger.error(
#             "[DELETE /shipment-payrolls] deleting table ShipmentPayroll: %s", e)
#         return jsonify({"error": "Error al eliminar Planilla"}), 500
