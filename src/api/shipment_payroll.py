# from flask import request, jsonify
# from sqlalchemy import extract

# from dateutil import parser

# from app_config import logger
# from models import Planillas
# from app_config import db_session

# from app_config import app


# @app.route('/planillas/', methods=['POST'])
# def post_planilla():
#     fecha = request.json.get('fecha')
#     return agregar_planilla(fecha)

# def agregar_planilla(fecha):
#     try:
#         fecha =  parser.isoparse(fecha).date()

#         # entrada existe en la tabla de lista de planillas
#         existing_entry = Planillas.query.filter_by(fecha=fecha).first()
#         if existing_entry is None:
#             #  agregar nueva entrada
#             new_planilla = Planillas(
#                 fecha=fecha,
#             )

#             try:
#                 db_session.add(new_planilla)
#                 db_session.commit()
#                 logger.warning("Nueva entrada en lista de planillas")
#             except Exception as e:
#                 db_session.rollback()
#                 logger.warning(f"Error: No se pudo agregar la entrada a la lista de planillas {str(e)}")
#                 raise e
#         else:
#             logger.warning("Fecha ya existe en la lista de planillas")
#     except Exception as e:
#         error_message = f'Error al agregar a lista de planillas {str(e)}'
#         logger.warning(error_message)
#         return jsonify({"error": error_message}), 500


#     return jsonify({"success": "Entrada agregada exitosamente a la lista de planillas"}), 200


# @app.route('/planillas/<fecha>', methods=['DELETE'])
# def delete_planilla(fecha):
#     try:
#         fecha =  parser.isoparse(fecha).date()

#         planilla_to_delete = Planillas.query.filter_by(fecha=fecha).first()
#         # Delete the planilla
#         db_session.delete(planilla_to_delete)
#         db_session.commit()

#         return jsonify({"success": "Planilla y Cobranzas eliminados exitosamente"}), 200

#     except Exception as e:
#         error_message = f'Error en DELETE lista de planillas {str(e)}'
#         logger.warning(error_message)
#         return jsonify({"error": error_message}), 500


# @app.route('/planillas/<year>', methods=['GET'])
# def get_planilla(year):
#     try:
#         # Filtrar las planillas por año utilizando SQLAlchemy
#         planillas = Planillas.query.filter(extract('year', Planillas.fecha) == year).all()
#         # Ordenar las planillas por fecha
#         planillas_ordenadas = sorted(planillas, key=lambda planilla: planilla.fecha, reverse=True)
#         planillas_ordenadas = [planilla.fecha for planilla in planillas_ordenadas]

#         return jsonify(planillas_ordenadas)

#     except Exception as e:
#         error_message = f'Error en GET request a lista de planillas por año {str(e)}'
#         logger.warning(error_message)
#         return jsonify({"error": error_message}), 500

from flask import request
from flask import jsonify
from flask import Response

from typing import List
from typing import Sequence
from typing import Tuple
from typing import Optional

from sqlalchemy import select
from sqlalchemy import asc
from sqlalchemy.sql import extract
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import OperationalError

from app_config import logger
from app_config import app

from models import ShipmentPayroll

from app_config import db_session

from dataclasses import asdict


@app.route('/shipment-payroll/<int:payroll_code>', methods=['GET'])
def get_shipment_payroll(payroll_code: int) -> Tuple[Response, int]:
    current_user = ''
    company_id = ''
    try:
        stmt = select(ShipmentPayroll).where(
            ShipmentPayroll.payroll_code == payroll_code,
            ShipmentPayroll.deleted == False,
            ShipmentPayroll.company_id == company_id
        )

        shipment_payroll: Optional[ShipmentPayroll] = db_session.scalar(stmt)
        if shipment_payroll is None:
            logger.error(
                "[GET /shipment-payroll] fetching from table ShipmentPayroll not found")
            return jsonify({"error": "No se encontró la planilla"}), 404

        logger.info(
            "[GET /shipment-payroll] fetching from table ShipmentPayroll found: %s", shipment_payroll.payroll_code)
        logger.debug(
            "[GET /shipment-payroll] fetching from table ShipmentPayroll found: %s", shipment_payroll)

        return jsonify(shipment_payroll), 200

    except SQLAlchemyError as e:
        logger.error(
            "[GET /shipment-payroll] fetching from table ShipmentPayroll %s", e)
        return jsonify({"error": "Error de transacción"}), 500


@app.route('/shipment-payrolls', methods=['GET'])
def get_shipment_payroll_list() -> Tuple[Response, int]:
    company_id = ''
    current_user = ''

    try:
        stmt = select(ShipmentPayroll).where(
            ShipmentPayroll.deleted == False,
            ShipmentPayroll.company_id == company_id,
        )

        year: Optional[int] = request.args.get('year', type=int)
        if year:
            stmt = stmt.where(
                extract('year', ShipmentPayroll.creation_timestamp) == year)

        stmt = stmt.order_by(asc(ShipmentPayroll.creation_timestamp))

        shipment_payrolls: Sequence[ShipmentPayroll] = db_session.scalars(
            stmt).all()
        logger.info(
            "[GET /shipment-payrolls] fetching shipment payrolls from table ShipmentPayroll len: %s", len(shipment_payrolls))
        logger.debug(
            "[GET /shipment-payrolls] fetching shipment payrolls from table ShipmentPayroll: %s", shipment_payrolls)
        return jsonify(shipment_payrolls), 200

    except SQLAlchemyError as e:
        logger.error(
            "[GET /shipment-payrolls] fetching shipment payrolls from table ShipmentPayroll %s", e)
        return jsonify({"error": "Error al obtener planillas"}), 500


@app.route('/shipment-payroll', methods=['POST'])
def post_shipment_payroll() -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    try:
        payload = ShipmentPayroll(**request.get_json(),
                                  modification_user=current_user, company_id=company_id)

        db_session.add(payload)
        db_session.commit()
        logger.info(
            "[POST /shipment-payroll] adding to table ShipmentPayroll: %s", payload)
        return jsonify(
            {
                **asdict(payload),
                "success": "Planilla agregada exitosamente"
            }), 200

    except (TypeError, ValueError, KeyError) as e:
        logger.error("[POST /shipment-payroll] Invalid payload: %s", e)
        return jsonify({"error": f"Error, datos de la Planilla inválidos ({e})"}), 500

    except OperationalError as e:
        db_session.rollback()
        logger.error(
            "[POST /shipment-payroll] adding to table ShipmentPayroll: connection %s", e)

        return jsonify({"error": "Error al agregar planilla: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error(
            "[POST /hipment-payroll] adding to table ShipmentPayroll: %s", e)
        return jsonify({"error": "Error al agregar planilla"}), 500


# @app.route('/product/<int:product_code>', methods=['PUT'])
# def put_product(product_code: int) -> Tuple[Response, int]:
#     current_user = ''
#     company_id = ''

#     try:
#         entry_to_update: Optional[Product] = db_session.get(Product, product_code)
#         if entry_to_update is None:
#             return jsonify({'error': 'Producto no encontrado'}), 404

#         if entry_to_update.company_id != company_id:
#             logger.error(
#                 "[PUT /producto] updating table Producto: invalid company_id: %s", company_id)
#             return jsonify({"error": "Error al actualizar producto"}), 503

#         payload = Product(**request.get_json(),
#                           modification_user=current_user, company_id=company_id)

#         entry_to_update.product_name = payload.product_name
#         entry_to_update.modification_user = payload.modification_user

#         db_session.commit()
#         logger.info(
#             "[PUT /producto] updating table Producto: %s", product_code)
#         return jsonify(
#             {
#                 **asdict(entry_to_update),
#                 "success": "Producto actualizado exitosamente"
#             }), 200

#     except (TypeError, ValueError, KeyError) as e:
#         logger.error("[PUT /product] Invalid payload: %s", e)
#         return jsonify({"error": f"Error, datos del producto inválidos ({e})"}), 500

#     except OperationalError as e:
#         db_session.rollback()
#         logger.error(
#             "[PUT /producto] updating table Producto: connection %s", e)

#         return jsonify({"error": "Error al actualizar producto: problema de conexión"}), 503

#     except SQLAlchemyError as e:
#         db_session.rollback()
#         logger.error("[PUT /producto] updating table producto: %s", e)
#         return jsonify({"error": "Error al actualizar producto"}), 500


# @app.route('/product/<int:product_code>', methods=['DELETE'])
# def delete_product(product_code: int) -> Tuple[Response, int]:
#     current_user = ''
#     company_id = ''

#     try:
#         existing_entry: Optional[Product] = db_session.get(Product, product_code)
#         if existing_entry is None:
#             return jsonify({'error': 'Producto no encontrado'}), 404

#         if existing_entry.company_id != company_id:
#             logger.error(
#                 "[DELETE /product] deleting table Producto: invalid company_id: %s", company_id)
#             return jsonify({"error": "Error al eliminar producto"}), 503

#         existing_entry.deleted = True
#         existing_entry.modification_user = current_user
#         db_session.commit()
#         logger.info(
#             "[DELETE /product] deleting table Producto: %s", product_code)
#         return jsonify({'success': 'Producto eliminada exitosamente'}), 200

#     except OperationalError as e:
#         db_session.rollback()
#         logger.error(
#             "[DELETE /producto] deleting table Producto: connection %s", e)
#         return jsonify({"error": "Error al eliminar producto: problema de conexión"}), 503

#     except SQLAlchemyError as e:
#         db_session.rollback()
#         logger.error("[DELETE /producto] deleting table Producto: %s", e)
#         return jsonify({"error": "Error al eliminar producto"}), 500
