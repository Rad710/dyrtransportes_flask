from flask import request
from flask import jsonify
from flask import Response

from typing import List
from typing import Sequence
from typing import Tuple

from sqlalchemy import select
from sqlalchemy import asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import OperationalError

from app_config import logger
from app_config import app

from models import Product


from app_config import db_session

from dataclasses import asdict


@app.route('/product/<int:product_code>', methods=['GET'])
def get_product(product_code: int) -> Tuple[Response, int]:
    current_user = ''
    company_id = ''
    try:
        stmt = select(Product).where(
            Product.product_code == product_code, Product.deleted == False,
            Product.company_id == company_id
        )

        product: Product | None = db_session.scalar(stmt)
        if product is None:
            logger.error(
                "[GET /product] fetching from table Product not found")
            return jsonify({"error": "No se encontró el producto"}), 404

        logger.info(
            "[GET /product] fetching from table Product found: %s", product.product_code)
        logger.debug(
            "[GET /product] fetching from table Product found: %s", product)

        return jsonify(product), 200

    except SQLAlchemyError as e:
        logger.error("[GET /product] fetching from table Product %s", e)
        return jsonify({"error": "Error de transacción"}), 500


@app.route('/products', methods=['GET'])
def get_product_list() -> Tuple[Response, int]:
    company_id = ''
    current_user = ''

    try:
        stmt = select(Product).where(
            Product.deleted == False,
            Product.company_id == company_id,
        ).order_by(
            asc(Product.product_name)
        )

        products: Sequence[Product] = db_session.scalars(stmt).all()
        logger.info(
            "[GET /products] fetching products from table Product len: %s", len(products))
        logger.debug(
            "[GET /products] fetching products from table Product products: %s", products)
        return jsonify(products), 200

    except SQLAlchemyError as e:
        logger.error(
            "[GET /products] fetching products from table Product %s", e)
        return jsonify({"error": "Error al obtener productos"}), 500


@app.route('/product', methods=['POST'])
def post_product() -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    try:
        payload = Product(**request.get_json(),
                          modification_user=current_user, company_id=company_id)

        db_session.add(payload)
        db_session.commit()
        logger.info("[POST /product] adding to table Product: %s", payload)
        return jsonify(
            {
                **asdict(payload),
                "success": "Producto agregado exitosamente"
            }), 200

    except (TypeError, ValueError, KeyError) as e:
        logger.error("[POST /product] Invalid payload: %s", e)
        return jsonify({"error": f"Error, datos del producto inválidos ({e})"}), 500

    except OperationalError as e:
        db_session.rollback()
        logger.error(
            "[POST /product] adding to table Product: connection %s", e)

        return jsonify({"error": "Error al agregar producto: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("[POST /product] adding to table Product: %s", e)
        return jsonify({"error": "Error al agregar producto"}), 500


@app.route('/product/<int:product_code>', methods=['PUT'])
def put_product(product_code: int) -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    try:
        entry_to_update: Product | None = db_session.get(Product, product_code)
        if entry_to_update is None:
            return jsonify({'error': 'Producto no encontrado'}), 404

        if entry_to_update.company_id != company_id:
            logger.error(
                "[PUT /producto] updating table Producto: invalid company_id: %s", company_id)
            return jsonify({"error": "Error al actualizar producto"}), 503

        payload = Product(**request.get_json(),
                          modification_user=current_user, company_id=company_id)

        entry_to_update.product_name = payload.product_name
        entry_to_update.modification_user = payload.modification_user

        db_session.commit()
        logger.info(
            "[PUT /producto] updating table Producto: %s", product_code)
        return jsonify(
            {
                **asdict(entry_to_update),
                "success": "Producto actualizado exitosamente"
            }), 200

    except (TypeError, ValueError, KeyError) as e:
        logger.error("[PUT /product] Invalid payload: %s", e)
        return jsonify({"error": f"Error, datos del producto inválidos ({e})"}), 500

    except OperationalError as e:
        db_session.rollback()
        logger.error(
            "[PUT /producto] updating table Producto: connection %s", e)

        return jsonify({"error": "Error al actualizar producto: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("[PUT /producto] updating table producto: %s", e)
        return jsonify({"error": "Error al actualizar producto"}), 500


@app.route('/product/<int:product_code>', methods=['DELETE'])
def delete_product(product_code: int) -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    try:
        existing_entry: Product | None = db_session.get(Product, product_code)
        if existing_entry is None:
            return jsonify({'error': 'Producto no encontrado'}), 404

        if existing_entry.company_id != company_id:
            logger.error(
                "[DELETE /product] deleting table Producto: invalid company_id: %s", company_id)
            return jsonify({"error": "Error al eliminar producto"}), 503

        existing_entry.deleted = True
        existing_entry.modification_user = current_user
        db_session.commit()
        logger.info(
            "[DELETE /product] deleting table Producto: %s", product_code)
        return jsonify({'success': 'Producto eliminada exitosamente'}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error(
            "[DELETE /producto] deleting table Producto: connection %s", e)
        return jsonify({"error": "Error al eliminar producto: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("[DELETE /producto] deleting table Producto: %s", e)
        return jsonify({"error": "Error al eliminar producto"}), 500


@app.route('/products', methods=['DELETE'])
def delete_products() -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    if ((request.data is None) or (not request.is_json)):
        logger.error("[DELETE /products] Product list payload is empty")
        return jsonify({'error': 'Error al eliminar producto: producto no encontrado'}), 404

    product_list: List[int] = request.get_json()
    logger.debug("[DELETE /products] route_list: %s", product_list)

    try:
        for product_code in product_list:
            product: Product | None = db_session.get(Product, product_code)

            if product is None:
                return jsonify({'error': 'Error al eliminar producto: producto no encontrado'}), 404

            if product.company_id != company_id:
                logger.error(
                    "[DELETE /product] deleting from table Product: invalid company_id: %s", company_id)
                return jsonify({"error": "Error al eliminar producto"}), 503

            product.deleted = True
            product.modification_user = current_user
            logger.info(
                "[DELETE /products] deleting from table Product: %s", product_code)

        db_session.commit()
        return jsonify({'success': 'Ruta eliminada exitosamente'}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error(
            "[DELETE /routes] deleting table Route: connection %s", e)
        return jsonify({"error": "Error al eliminar ruta: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("[DELETE /routes] deleting table Route: %s", e)
        return jsonify({"error": "Error al eliminar ruta"}), 500
