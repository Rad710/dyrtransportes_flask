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
from openpyxl.styles import Border, Side
from openpyxl.utils import get_column_letter

from app_config import logger
from app_config import app
from app_config import db_session
from app_config import RequestWithUser

from decorators.token_required import token_required

from models.product import Product

request: RequestWithUser


@app.route("/api/product/<int:product_code>", methods=["GET"])
@token_required
def get_product(product_code: int) -> Tuple[Response, int]:
    try:
        stmt = select(Product).where(
            Product.product_code == product_code,
            Product.deleted == False,
            Product.modification_user == request.current_user.user_id,
        )

        product: Optional[Product] = db_session.scalar(stmt)
        if product is None:
            logger.error("fetch table Product, not found")
            return jsonify({"message": "No se encontró el producto"}), 404

        logger.info("fetch table Product, found: %s", product.product_code)
        logger.debug("fetch table Product, found: %s", product)

        return jsonify(product), 200

    except SQLAlchemyError as e:
        logger.error("fetch table Product, error: %s", e)
        return jsonify({"message": "Error de transacción"}), 500


@app.route("/api/products", methods=["GET"])
@token_required
def get_product_list() -> Tuple[Response, int]:
    try:
        stmt = (
            select(Product)
            .where(
                Product.deleted == False,
                Product.modification_user == request.current_user.user_id,
            )
            .order_by(asc(Product.product_name))
        )

        products: Sequence[Product] = db_session.scalars(stmt).all()
        logger.info("fetch products table Product, len: %s", len(products))
        logger.debug("fetch products table Product, products: %s", products)
        return jsonify(products), 200

    except SQLAlchemyError as e:
        logger.error("fetch products table Product, error: %s", e)
        return jsonify({"message": "Error al obtener productos"}), 500


@app.route("/api/product", methods=["POST"])
@token_required
def post_product() -> Tuple[Response, int]:
    try:
        # json to db object
        payload = Product(
            **request.get_json(), modification_user=request.current_user.user_id
        )

        # add to database
        logger.debug("insert table Product, payload: %s", payload)
        db_session.add(payload)

        db_session.commit()
        logger.info("inserted table Product, product: %s", payload.product_code)
        return (
            jsonify({**asdict(payload), "message": "Producto agregado exitosamente"}),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("insert table Product, invalid product error: %s", e)
        return jsonify({"message": f"Error, datos del producto inválidos ({e})"}), 500

    except OperationalError as e:
        db_session.rollback()
        logger.error("insert table Product, connection error: %s", e)

        return (
            jsonify({"message": "Error al agregar producto: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("insert table Product, error: %s", e)
        return jsonify({"message": "Error al agregar producto"}), 500


@app.route("/api/product/<int:product_code>", methods=["PUT"])
@token_required
def put_product(product_code: int) -> Tuple[Response, int]:
    try:
        # get entry to update
        stmt = select(Product).where(
            Product.product_code == product_code,
            Product.modification_user == request.current_user.user_id,
        )
        entry_to_update: Optional[Product] = db_session.scalar(stmt)

        if entry_to_update is None:
            logger.error("update table Product, product not found")
            return jsonify({"message": "Producto no encontrado"}), 404

        # json to db object
        payload = Product(
            **request.get_json(), modification_user=request.current_user.user_id
        )

        entry_to_update.product_name = payload.product_name
        entry_to_update.modification_user = payload.modification_user

        logger.info("update table Product, payload: %s", entry_to_update)

        db_session.commit()
        logger.info("updated table Product, product: %s", product_code)
        return (
            jsonify(
                {
                    **asdict(entry_to_update),
                    "message": "Producto actualizado exitosamente",
                }
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("invalid product: %s", e)
        return jsonify({"message": f"Error, datos del producto inválidos ({e})"}), 500

    except OperationalError as e:
        db_session.rollback()
        logger.error("update table Product: connection error %s", e)

        return (
            jsonify({"message": "Error al actualizar producto: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("update table Product, error: %s", e)
        return jsonify({"message": "Error al actualizar producto"}), 500


@app.route("/api/product/<int:product_code>", methods=["DELETE"])
@token_required
def delete_product(product_code: int) -> Tuple[Response, int]:
    try:
        stmt = select(Product).where(
            Product.product_code == product_code,
            Product.modification_user == request.current_user.user_id,
        )
        existing_entry: Optional[Product] = db_session.scalar(stmt)

        if existing_entry is None:
            logger.error("delete table Product, product not found")
            return jsonify({"message": "Producto no encontrado"}), 404

        existing_entry.deleted = True
        existing_entry.modification_user = request.current_user.user_id
        db_session.commit()
        logger.info("delete table Product: product %s", product_code)
        return jsonify({"message": "Producto eliminado exitosamente"}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table Product, connection error: %s", e)
        return (
            jsonify({"message": "Error al eliminar producto: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table Product, error: %s", e)
        return jsonify({"message": "Error al eliminar producto"}), 500


@app.route("/api/products", methods=["DELETE"])
@token_required
def delete_products() -> Tuple[Response, int]:
    if (request.data is None) or (not request.is_json):
        logger.error("delete products table Product, product list is empty")
        return (
            jsonify({"message": "Error al eliminar producto: producto no encontrado"}),
            404,
        )

    product_list: List[int] = request.get_json()
    logger.debug("delete products table Product, payload: %s", product_list)

    try:
        for product_code in product_list:
            stmt = select(Product).where(
                Product.product_code == product_code,
                Product.modification_user == request.current_user.user_id,
            )
            product: Optional[Product] = db_session.scalar(stmt)

            if product is None:
                return (
                    jsonify(
                        {
                            "message": "Error al eliminar producto: producto no encontrado"
                        }
                    ),
                    404,
                )

            product.deleted = True
            product.modification_user = request.current_user.user_id
            logger.info("delete table Product, product: %s", product_code)

        db_session.commit()
        return jsonify({"message": "Producto eliminado exitosamente"}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table Product: connection error %s", e)
        return (
            jsonify({"message": "Error al eliminar producto: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table Product, error: %s", e)
        return jsonify({"message": "Error al eliminar producto"}), 500


@app.route("/api/export-products", methods=["GET"])
@token_required
def export_products() -> Tuple[Response, int]:
    product_response, code = get_product_list()

    if code != 200 or not product_response.is_json or product_response.json is None:
        logger.error("export Products, fetch Products error")
        return jsonify({"message": "Error enviar archivo Excel"}), 500

    product_list = [Product(**x) for x in product_response.json]

    # Create file
    output = io.BytesIO()
    workbook = Workbook(write_only=False, iso_dates=False)
    sheet = workbook.active

    headers = ["Código", "Nombre de Producto"]
    sheet.append(headers)

    for col_idx in range(1, 3):
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
    for product in product_list:
        row = [product.product_code, product.product_name]

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
        "attachment; filename=lista_de_productos.xlsx"
    )

    logger.info("exported Products excel file")

    return response, 200
