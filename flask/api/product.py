from flask import request
from flask import jsonify
from flask import Response

from typing import Any
from typing import Dict
from typing import Sequence
from typing import Tuple

from decimal import Decimal
from sqlalchemy import select
from sqlalchemy import asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import OperationalError

from app_config import logger
from models.models import Product

from app_config import app

from models.database import db_session


def validated_product_payload() -> Tuple[str, str, Decimal, Decimal] | None:
    if (request.data is None):
        logger.error("[POST /product] Product payload is empty")
        return None
    
    # shipment_code = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    # shipment_date = Column(Date, nullable=False)
    # driver_code = Column(Integer, ForeignKey('driver.driver_code'), nullable=False)
    # product_code = Column(Integer, ForeignKey('product.product_code'), nullable=False)
    # route_code = Column(Integer, ForeignKey('route.route_code'), nullable=False)
    # price = Column(Numeric(10, 2), default=0, nullable=False)
    # payroll_price = Column(Numeric(10, 2), default=0, nullable=False)
    # ticket_code = Column(String(100), nullable=False)
    # origin_weight = Column(Integer, nullable=False)
    # destination_weight = Column(Integer, nullable=False)
    # shipment_payroll_code = Column(Integer, ForeignKey('shipment_payroll.payroll_code'), nullable=False)
    # driver_payroll_code = Column(Integer, ForeignKey('driver_payroll.payroll_code'), nullable=False)
    # deleted = Column(Boolean, default=False, nullable=False)
    # company_id = Column(String(100), nullable=False)
    # modification_user = Column(String(100), nullable=False)

    payload : Dict[str, Any] = request.get_json()
    logger.debug("[POST /product] payload: %s", payload)

    required_fields = ['origin', 'destination', 'price', 'payrollPrice']
    for field in required_fields:
        if field not in payload:
            logger.error("[POST /product] payload missing field: %s", field)
            return None

    origin = payload['origin']
    destination = payload['destination']
    price = payload['price']
    payroll_price = payload['payroll_price']

    if not isinstance(origin, str) or not isinstance(destination, str):
        logger.error("[POST /product] payload type error in 'origin' and 'destination'")
        return None
    if not isinstance(price, (int, float)) or not isinstance(payroll_price, (int, float)):
        logger.error("[POST /product] payload type error in 'price' and 'payroll_price'")
        return None

    if price <= 0 or payroll_price <= 0:
        logger.error("[POST /product] payload value error in 'price' and 'payrollPrice'")
        return None
    
    return origin, destination, Decimal(str(price)), Decimal(str(payroll_price))


@app.route('/product', methods=['POST'])
def post_product() -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    validated_payroll = validated_product_payload()
    if (validated_payroll is None):
        return jsonify({"error": "Error al recibir datos de producto"}), 500
    
    origin, destination, price, payroll_price = validated_payroll

    stmt = select(product).where(
        product.origin == origin, product.destination == destination,
        product.deleted == False
    )
    existing_entry : product | None = db_session.scalar(stmt)

    logger.debug("[POST /product] existing_entry: %s", existing_entry)

    if existing_entry is not None:
        logger.error("[POST /product] duplicate in table product: %s", existing_entry)
        return jsonify({"error": "Ruta ya existe"}), 500

    new_product = product(
        origin=origin, destination=destination,
        price=price, payroll_price=payroll_price,
        modification_user=current_user, company_id=company_id
    )

    try:
        db_session.add(new_product)
        db_session.commit()
        logger.info("[POST /product] adding to table product: %s", new_product)
        return jsonify({"success": "Ruta agregada exitosamente"}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("[POST /product] adding to table product: connection %s", e)

        return jsonify({"error": "Error al agregar ruta: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("[POST /product] adding to table product: %s", e)
        return jsonify({"error": "Error al agregar ruta"}), 500


@app.route('/products', methods=['GET'])
def get_product_list() -> Tuple[Response, int]:
    company_id = ''
    current_user = ''

    try:
        stmt = select(
            product
        ).where(
            product.deleted == False, product.company_id == company_id,
        ).order_by(
            asc(product.origin), asc(product.destination)
        )

        products : Sequence[product] = db_session.scalars(stmt).all()
        logger.info("[GET /products] fetching products from table product len: %s", len(products))
        logger.debug("[GET /products] fetching products from table product products: %s", products)
        return jsonify(products), 200
    
    except SQLAlchemyError as e:
        logger.error("[GET /products] fetching products from table product %s", e)
        return jsonify({"error": "Error al obtener rutas"}), 500


@app.route('/product/<string:product_code>', methods=['PATCH'])
def patch_product(product_code : str) -> Tuple[Response, int]:
    validated_payroll = validated_product_payload()

    if (validated_payroll is None):
        return jsonify({"error": "Error al recibir datos"}), 500
    
    origin, destination, price, payroll_price = validated_payroll

    existing_entry : product | None = db_session.get(product, product_code)
    
    if existing_entry:
        try:
            existing_entry.origin = origin
            existing_entry.destination = destination
            existing_entry.price = price
            existing_entry.payroll_price = payroll_price

            db_session.commit()
            logger.info("[PATCH /product] updating table product: %s", product_code)
            return jsonify({'success': 'Ruta actualizada exitosamente'}), 200
        
        except OperationalError as e:
            db_session.rollback()
            logger.error("[PATCH /product] updating table product: connection %s", e)

            return jsonify({"error": "Error al actualizar ruta: problema de conexión"}), 503

        except SQLAlchemyError as e:
            db_session.rollback()
            logger.error("[PATCH /product] updating table product: %s", e)
            return jsonify({"error": "Error al actualizar ruta"}), 500

    return jsonify({'error': 'Ruta no encontrado'}), 404


@app.route('/product/<string:product_code>', methods=['DELETE'])
def delete_precio(product_code : str) -> Tuple[Response, int]:
    product : product | None = db_session.get(product, id)
    if product:
        try:
            product.deleted = True
            db_session.commit()
            logger.info("[DELETE /product] deleting from table product: %s", product_code)
            return jsonify({'success': 'Ruta eliminada exitosamente'}), 200

        except OperationalError as e:
            db_session.rollback()
            logger.error("[DELETE /product] deleting table product: connection %s", e)

            return jsonify({"error": "Error al eliminar ruta: problema de conexión"}), 503

        except SQLAlchemyError as e:
            db_session.rollback()
            logger.error("[DELETE /product] deleting table product: %s", e)
            return jsonify({"error": "Error al eliminar ruta"}), 500

    return jsonify({'error': 'Ruta no encontrado'}), 404
