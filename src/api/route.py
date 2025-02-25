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

from models.route import Route

request: RequestWithUser


@app.route("/api/route/<int:route_code>", methods=["GET"])
@token_required
def get_route(route_code: int) -> Tuple[Response, int]:
    try:
        stmt = select(Route).where(
            Route.route_code == route_code,
            Route.deleted == False,
            Route.modification_user == request.current_user.user_id,
        )

        route: Optional[Route] = db_session.scalar(stmt)
        if route is None:
            logger.error("fetch table Route, not found")
            return jsonify({"message": "No se encontró la routa"}), 404

        logger.info("fetch table Route, found: %s", route.route_code)
        logger.debug("fetch table Route, found: %s", route)

        return jsonify(route), 200

    except SQLAlchemyError as e:
        logger.error("fetch table Route, error: %s", e)
        return jsonify({"message": "Error de transacción"}), 500


@app.route("/api/routes", methods=["GET"])
@token_required
def get_route_list() -> Tuple[Response, int]:
    try:
        stmt = (
            select(Route)
            .where(
                Route.deleted == False,
                Route.modification_user == request.current_user.user_id,
            )
            .order_by(asc(Route.origin), asc(Route.destination))
        )

        routes: Sequence[Route] = db_session.scalars(stmt).all()
        logger.info("fetch routes table Route, len: %s", len(routes))
        logger.debug("fetch routes table Route, routes: %s", routes)
        return jsonify(routes), 200

    except SQLAlchemyError as e:
        logger.error("fetch routes table Route, error: %s", e)
        return jsonify({"message": "Error al obtener rutas"}), 500


@app.route("/api/route", methods=["POST"])
@token_required
def post_route() -> Tuple[Response, int]:
    try:
        # json to db object
        payload = Route(
            **request.get_json(), modification_user=request.current_user.user_id
        )

        # add to database
        logger.debug("insert table Route, payload: %s", payload)
        db_session.add(payload)

        db_session.commit()
        logger.info("inserted table Route, route: %s", payload.route_code)
        return (
            jsonify({**asdict(payload), "message": "Ruta agregada exitosamente"}),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("insert table Route, invalid route error: %s", e)
        return jsonify({"message": f"Error, datos de la Ruta inválidos ({e})"}), 500

    except OperationalError as e:
        db_session.rollback()
        logger.error("insert table Route, connection error: %s", e)

        return jsonify({"message": "Error al agregar ruta: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("insert table Route, error: %s", e)
        return jsonify({"message": "Error al agregar ruta"}), 500


@app.route("/api/route/<int:route_code>", methods=["PUT"])
@token_required
def put_route(route_code: int) -> Tuple[Response, int]:
    try:
        # get entry to update
        stmt = select(Route).where(
            Route.route_code == route_code,
            Route.modification_user == request.current_user.user_id,
        )
        entry_to_update: Optional[Route] = db_session.scalar(stmt)

        if entry_to_update is None:
            logger.error("update table Route, route not found")
            return jsonify({"message": "Ruta no encontrado"}), 404

        # json to db object
        payload = Route(
            **request.get_json(), modification_user=request.current_user.user_id
        )

        entry_to_update.origin = payload.origin
        entry_to_update.destination = payload.destination
        entry_to_update.price = payload.price
        entry_to_update.payroll_price = payload.payroll_price
        entry_to_update.modification_user = payload.modification_user

        logger.info("update table Route, payload: %s", entry_to_update)

        db_session.commit()
        logger.info("updated table Route, route: %s", route_code)
        return (
            jsonify(
                {**asdict(entry_to_update), "message": "Ruta actualizada exitosamente"}
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("invalid route: %s", e)
        return jsonify({"message": f"Error, datos de la Ruta inválidos ({e})"}), 500

    except OperationalError as e:
        db_session.rollback()
        logger.error("update table Route: connection error %s", e)

        return (
            jsonify({"message": "Error al actualizar ruta: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("update table Route, error: %s", e)
        return jsonify({"message": "Error al actualizar ruta"}), 500


@app.route("/api/route/<int:route_code>", methods=["DELETE"])
@token_required
def delete_route(route_code: int) -> Tuple[Response, int]:
    try:
        stmt = select(Route).where(
            Route.route_code == route_code,
            Route.modification_user == request.current_user.user_id,
        )
        existing_entry: Optional[Route] = db_session.scalar(stmt)

        if existing_entry is None:
            logger.error("delete table Route, route not found")
            return jsonify({"message": "Ruta no encontrado"}), 404

        existing_entry.deleted = True
        existing_entry.modification_user = request.current_user.user_id
        db_session.commit()
        logger.info("delete table Route: route %s", route_code)
        return jsonify({"message": "Ruta eliminada exitosamente"}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table Route, connection error: %s", e)
        return jsonify({"message": "Error al eliminar ruta: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table Route, error: %s", e)
        return jsonify({"message": "Error al eliminar ruta"}), 500


@app.route("/api/routes", methods=["DELETE"])
@token_required
def delete_routes() -> Tuple[Response, int]:
    if (request.data is None) or (not request.is_json):
        logger.error("delete routes table Route, route list is empty")
        return jsonify({"message": "Error al eliminar ruta: ruta no encontrada"}), 404

    route_list: List[int] = request.get_json()
    logger.debug("delete routes table Route, payload: %s", route_list)

    try:
        for route_code in route_list:
            stmt = select(Route).where(
                Route.route_code == route_code,
                Route.modification_user == request.current_user.user_id,
            )
            route: Optional[Route] = db_session.scalar(stmt)

            if route is None:
                return (
                    jsonify({"message": "Error al eliminar ruta: ruta no encontrada"}),
                    404,
                )

            route.deleted = True
            route.modification_user = request.current_user.user_id
            logger.info("delete table Route, route: %s", route_code)

        db_session.commit()
        return jsonify({"message": "Ruta eliminada exitosamente"}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table Route: connection error %s", e)
        return jsonify({"message": "Error al eliminar ruta: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table Route, error: %s", e)
        return jsonify({"message": "Error al eliminar ruta"}), 500


@app.route("/api/export-routes", methods=["GET"])
@token_required
def export_routes() -> Tuple[Response, int]:
    route_response, code = get_route_list()

    if code != 200 or not route_response.is_json or route_response.json is None:
        logger.error("export Routes, fetch Routes error")
        return jsonify({"message": "Error enviar archivo Excel"}), 500

    route_list = [Route(**x) for x in route_response.json]

    # Create file
    output = io.BytesIO()
    workbook = Workbook(write_only=False, iso_dates=False)
    sheet = workbook.active

    headers = ["Origen", "Destino", "Precio", "Precio de Liquidación"]
    sheet.append(headers)

    for col_idx in range(1, 5):
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
    for route in route_list:
        row = [route.origin, route.destination, route.price, route.payroll_price]

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
    response.headers["Content-Type"] = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response.headers["Content-Disposition"] = (
        "attachment; filename=lista_de_precios.xlsx"
    )

    logger.info("exported Routes excel file")

    return response, 200
