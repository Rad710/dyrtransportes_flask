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

from models import Route


from app_config import db_session

from dataclasses import asdict


@app.route('/route/<int:route_code>', methods=['GET'])
def get_route(route_code: int) -> Tuple[Response, int]:
    company_id = ''
    try:
        stmt = select(Route).where(
            Route.route_code == route_code, Route.deleted == False,
            Route.company_id == company_id
        )

        route: Route | None = db_session.scalar(stmt)
        if route is None:
            logger.error("[GET /route] fetching from table Route not found")
            return jsonify({"error": "No se encontró la routa"}), 404

        logger.info(
            "[GET /route] fetching from table Route found: %s", route.route_code)
        logger.debug("[GET /route] fetching from table Route found: %s", route)

        return jsonify(route), 200

    except SQLAlchemyError as e:
        logger.error("[GET /route] fetching from table Route %s", e)
        return jsonify({"error": "Error de transacción"}), 500


@app.route('/routes', methods=['GET'])
def get_route_list() -> Tuple[Response, int]:
    company_id = ''

    try:
        stmt = select(Route).where(
            Route.deleted == False,
            Route.company_id == company_id,
        ).order_by(
            asc(Route.origin), asc(Route.destination)
        )

        routes: Sequence[Route] = db_session.scalars(stmt).all()
        logger.info(
            "[GET /routes] fetching routes from table Route len: %s", len(routes))
        logger.debug(
            "[GET /routes] fetching routes from table Route routes: %s", routes)
        return jsonify(routes), 200

    except SQLAlchemyError as e:
        logger.error("[GET /routes] fetching routes from table Route %s", e)
        return jsonify({"error": "Error al obtener rutas"}), 500


def validated_route_payload() -> Route | None:
    if ((request.data is None) or (not request.is_json)):
        logger.error("[POST|PATCH /route] Route payload is empty")
        return None

    try:
        # create class using dict json
        payload = Route(**request.get_json())
    except (TypeError, ValueError, KeyError) as e:
        logger.error("[POST|PATCH /product] Invalid payload: %s", e)
        return None

    logger.debug("[POST|PATCH /route] payload: %s", payload)

    # validate required fields
    required_fields = ['origin', 'destination', 'price', 'payroll_price']
    missing_field = any(getattr(payload, field)
                        is None for field in required_fields)
    if missing_field:
        logger.error(
            "[POST|PATCH /route] payload missing required fields: %s", payload)
        return None

    if not isinstance(payload.origin, str) or not isinstance(payload.destination, str):
        logger.error(
            "[POST|PATCH /route] payload type error in 'origin' and 'destination'")
        return None
    if not isinstance(payload.price, (int, float)) or not isinstance(payload.payroll_price, (int, float)):
        logger.error(
            "[POST|PATCH /route] payload type error in 'price' and 'payroll_price'")
        return None

    # cast received as float to Decimal. TODO: check if required to receive as string?
    payload.price = Decimal(payload.price)
    payload.payroll_price = Decimal(payload.payroll_price)
    if payload.price < 0 or payload.payroll_price < 0:
        logger.error(
            "[POST|PATCH /route] payload value error in 'price' and 'payrollPrice'")
        return None

    return payload


@app.route('/route', methods=['POST'])
def post_route() -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    # validate payload
    payload = validated_route_payload()
    if (payload is None):
        return jsonify({"error": "Error al recibir datos de ruta"}), 500

    payload.modification_user = current_user
    payload.company_id = company_id

    # add to database
    try:
        db_session.add(payload)
        db_session.commit()
        logger.info("[POST /route] adding to table Route: %s", payload)
        return jsonify(
            {
                **asdict(payload),
                "success": "Ruta agregada exitosamente"
            }), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("[POST /route] adding to table Route: connection %s", e)

        return jsonify({"error": "Error al agregar ruta: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("[POST /route] adding to table Route: %s", e)
        return jsonify({"error": "Error al agregar ruta"}), 500


@app.route('/route/<int:route_code>', methods=['PUT'])
def put_route(route_code: int) -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    # validate
    payload = validated_route_payload()
    if (payload is None):
        return jsonify({"error": "Error al recibir datos"}), 500

    # get entry to update
    entry_to_update: Route | None = db_session.get(Route, route_code)
    if entry_to_update is None:
        return jsonify({'error': 'Ruta no encontrado'}), 404

    if entry_to_update.company_id != company_id:
        logger.error(
            "[PUT /route] updating table Route: invalid company_id: %s", company_id)
        return jsonify({"error": "Error al actualizar ruta"}), 503

    try:
        entry_to_update.origin = payload.origin
        entry_to_update.destination = payload.destination
        entry_to_update.price = payload.price
        entry_to_update.payroll_price = payload.payroll_price
        entry_to_update.modification_user = current_user

        db_session.commit()
        logger.info("[PUT /route] updating table Route: %s", route_code)
        return jsonify(
            {
                **asdict(entry_to_update),
                "success": "Ruta actualizada exitosamente"
            }), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error(
            "[PUT /route] updating table Route: connection %s", e)

        return jsonify({"error": "Error al actualizar ruta: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("[PUT /route] updating table Route: %s", e)
        return jsonify({"error": "Error al actualizar ruta"}), 500


@app.route('/route/<int:route_code>', methods=['DELETE'])
def delete_route(route_code: int) -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    existing_entry: Route | None = db_session.get(Route, route_code)
    if existing_entry is None:
        return jsonify({'error': 'Ruta no encontrado'}), 404

    if existing_entry.company_id != company_id:
        logger.error(
            "[PATCH /route] deleting table Route: invalid company_id: %s", company_id)
        return jsonify({"error": "Error al eliminar ruta"}), 503

    try:
        existing_entry.deleted = True
        existing_entry.modification_user = current_user
        db_session.commit()
        logger.info(
            "[DELETE /route] deleting table Route: %s", route_code)
        return jsonify({'success': 'Ruta eliminada exitosamente'}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error(
            "[DELETE /route] deleting table Route: connection %s", e)
        return jsonify({"error": "Error al eliminar ruta: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("[DELETE /route] deleting table Route: %s", e)
        return jsonify({"error": "Error al eliminar ruta"}), 500


@app.route('/routes', methods=['DELETE'])
def delete_routes() -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    if ((request.data is None) or (not request.is_json)):
        logger.error("[DELETE /routes] Route list payload is empty")
        return jsonify({'error': 'Error al eliminar ruta: ruta no encontrada'}), 404

    route_list: List[int] = request.get_json()
    logger.debug("[DELETE /routes] route_list: %s", route_list)

    try:
        for route_code in route_list:
            route: Route | None = db_session.get(Route, route_code)

            if route is None:
                return jsonify({'error': 'Error al eliminar ruta: ruta no encontrada'}), 404

            if route.company_id != company_id:
                logger.error(
                    "[PATCH /route] deleting table Route: invalid company_id: %s", company_id)
                return jsonify({"error": "Error al eliminar ruta"}), 503

            route.deleted = True
            route.modification_user = current_user
            logger.info(
                "[DELETE /routes] deleting from table Route: %s", route_code)

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


@app.route('/export-routes', methods=['GET'])
def export_routes() -> Tuple[Response, int]:
    route_response, code = get_route_list()
    logger.debug("[GET /export-routes] jsonify response: %s",
                 route_response.get_json())

    if code != 200 or not route_response.is_json or route_response.json is None:
        return jsonify({"error": "Error enviar archivo Excel"}), 500

    route_list = [Route(**x) for x in route_response.json]

    # Create file
    output = io.BytesIO()
    workbook = Workbook(write_only=False, iso_dates=False)
    sheet = workbook.active

    headers = ['Origen', 'Destino', 'Precio', 'Precio de Liquidación']
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
    for route in route_list:
        row = [route.origin, route.destination,
               route.price, route.payroll_price]

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
    response.headers['Content-Disposition'] = 'attachment; filename=lista_de_precios.xlsx'

    logger.warning("Lista de Precios exportada")
    return response, 200
