from flask import request
from flask import jsonify
from flask import Response
from flask import make_response

from typing import Any
from typing import Dict
from typing import Sequence
from typing import Tuple
from typing import List

from decimal import Decimal
from sqlalchemy import select
from sqlalchemy import asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import OperationalError

import io
from openpyxl import Workbook
from openpyxl.styles import numbers, Border, Side
from openpyxl.utils import get_column_letter

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


def validated_product_payload() -> str | None:
    if ((request.data is None) or (not request.is_json)):
        logger.error("[POST|PATCH /product] Product payload is empty")
        return None

    payload: Dict[str, str] = request.get_json()
    logger.debug("[POST|PATCH /product] payload: %s", payload)

    if "product_name" not in payload:
        logger.error(
            "[POST|PATCH /product] payload missing field: product_name")
        return None

    product_name = payload["product_name"]
    return product_name


@app.route('/product', methods=['POST'])
def post_product() -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    validated_payload = validated_product_payload()
    if (validated_payload is None):
        return jsonify({"error": "Error al recibir datos del producto"}), 500

    product_name = validated_payload

    stmt = select(Product).where(
        Product.product_name == product_name,
        Product.deleted == False
    )

    existing_entry: Product | None = db_session.scalar(stmt)

    logger.debug("[POST /product] existing_entry: %s", existing_entry)

    if existing_entry is not None:
        logger.error(
            "[POST /product] duplicate in table Product: %s", existing_entry)
        return jsonify({"error": "Producto ya existe"}), 500

    new_product = Product(
        product_name=product_name,
        modification_user=current_user, company_id=company_id
    )

    try:
        db_session.add(new_product)
        db_session.commit()
        logger.info("[POST /product] adding to table Product: %s", new_product)
        return jsonify(
            {
                **asdict(new_product),
                "success": "Producto agregado exitosamente"
            }), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error(
            "[POST /product] adding to table Product: connection %s", e)

        return jsonify({"error": "Error al agregar producto: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("[POST /product] adding to table Product: %s", e)
        return jsonify({"error": "Error al agregar producto"}), 500


@app.route('/product/<int:product_code>', methods=['PATCH'])
def patch_product(product_code: int) -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    validated_payload = validated_product_payload()
    if (validated_payload is None):
        return jsonify({"error": "Error al recibir datos"}), 500

    product_name = validated_payload

    stmt = select(Product).where(
        Product.product_name == product_name,
        Product.deleted == False
    )

    existing_entry: Product | None = db_session.scalar(stmt)
    logger.debug("[PATCH /product] existing_entry: %s", existing_entry)

    if (existing_entry is not None) and (existing_entry.product_code != product_code):
        logger.error(
            "[PATCH /product] duplicate in table Product: %s", existing_entry)
        return jsonify({"error": "Producto ya existe"}), 500

    entry_to_update: Product | None = db_session.get(Product, product_code)
    if entry_to_update is None:
        return jsonify({'error': 'Producto no encontrado'}), 404

    if entry_to_update.company_id != company_id:
        logger.error(
            "[PATCH /producto] updating table Producto: invalid company_id: %s", company_id)
        return jsonify({"error": "Error al actualizar producto"}), 503

    try:
        entry_to_update.product_name = product_name
        entry_to_update.modification_user = current_user

        db_session.commit()
        logger.info(
            "[PATCH /producto] updating table Producto: %s", product_code)
        return jsonify(
            {
                **asdict(entry_to_update),
                "success": "Producto actualizado exitosamente"
            }), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error(
            "[PATCH /producto] updating table Producto: connection %s", e)

        return jsonify({"error": "Error al actualizar producto: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("[PATCH /producto] updating table producto: %s", e)
        return jsonify({"error": "Error al actualizar producto"}), 500


@app.route('/product/<int:product_code>', methods=['DELETE'])
def delete_product(product_code: int) -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    existing_entry: Product | None = db_session.get(Product, product_code)
    if existing_entry is None:
        return jsonify({'error': 'Producto no encontrado'}), 404

    if existing_entry.company_id != company_id:
        logger.error(
            "[PATCH /product] deleting table Producto: invalid company_id: %s", company_id)
        return jsonify({"error": "Error al eliminar producto"}), 503

    try:
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
