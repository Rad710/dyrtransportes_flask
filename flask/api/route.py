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
from app_config import app

from models.models import Route


from models.database import db_session

from dataclasses import asdict

def validated_route_payload() -> Tuple[str, str, Decimal, Decimal] | None:
    if (request.data is None):
        logger.error("[POST|PATCH /route] Route payload is empty")
        return None

    payload : Dict[str, Any] = request.get_json()
    logger.debug("[POST|PATCH /route] payload: %s", payload)

    required_fields = ['origin', 'destination', 'price', 'payroll_price']
    for field in required_fields:
        if field not in payload:
            logger.error("[POST|PATCH /route] payload missing field: %s", field)
            return None

    origin = payload['origin']
    destination = payload['destination']
    price = payload['price']
    payroll_price = payload['payroll_price']

    if not isinstance(origin, str) or not isinstance(destination, str):
        logger.error("[POST|PATCH /route] payload type error in 'origin' and 'destination'")
        return None
    if not isinstance(price, (int, float)) or not isinstance(payroll_price, (int, float)):
        logger.error("[POST|PATCH /route] payload type error in 'price' and 'payroll_price'")
        return None

    if price <= 0 or payroll_price <= 0:
        logger.error("[POST|PATCH /route] payload value error in 'price' and 'payrollPrice'")
        return None
    
    return origin, destination, Decimal(str(price)), Decimal(str(payroll_price))


@app.route('/route', methods=['POST'])
def post_route() -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    validated_payroll = validated_route_payload()
    if (validated_payroll is None):
        return jsonify({"error": "Error al recibir datos de ruta"}), 500
    
    origin, destination, price, payroll_price = validated_payroll

    stmt = select(Route).where(
        Route.origin == origin, Route.destination == destination,
        Route.deleted == False
    )
    existing_entry : Route | None = db_session.scalar(stmt)

    logger.debug("[POST /route] existing_entry: %s", existing_entry)

    if existing_entry is not None:
        logger.error("[POST /route] duplicate in table Route: %s", existing_entry)
        return jsonify({"error": "Ruta ya existe"}), 500

    new_route = Route(
        origin=origin, destination=destination,
        price=price, payroll_price=payroll_price,
        modification_user=current_user, company_id=company_id
    )

    try:
        db_session.add(new_route)
        db_session.commit()
        logger.info("[POST /route] adding to table Route: %s", new_route)
        return jsonify(
            {
                **asdict(new_route),
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


@app.route('/routes', methods=['GET'])
def get_route_list() -> Tuple[Response, int]:
    company_id = ''
    current_user = ''

    try:
        stmt = select(
            Route
        ).where(
            Route.deleted == False, Route.company_id == company_id,
        ).order_by(
            asc(Route.origin), asc(Route.destination)
        )

        routes : Sequence[Route] = db_session.scalars(stmt).all()
        logger.info("[GET /routes] fetching routes from table Route len: %s", len(routes))
        logger.debug("[GET /routes] fetching routes from table Route routes: %s", routes)
        return jsonify(routes), 200
    
    except SQLAlchemyError as e:
        logger.error("[GET /routes] fetching routes from table Route %s", e)
        return jsonify({"error": "Error al obtener rutas"}), 500


@app.route('/route/<string:route_code>', methods=['GET'])
def get_route(route_code : str) -> Tuple[Response, int]:
    current_user = ''
    company_id = ''
    try:
        stmt = select(
            Route
        ).where(
            Route.route_code == route_code, Route.deleted == False,
            Route.company_id == company_id
        )

        route: Route | None = db_session.scalar(stmt)
        if route is None:
            logger.error("[GET /route] fetching from table Route not found")
            return jsonify({"error": "No se encontró la routa"}), 404
        
        logger.info("[GET /route] fetching from table Route found: %s", route.route_code)
        logger.debug("[GET /route] fetching from table Route found: %s", route)

        return jsonify(route), 200

    except SQLAlchemyError as e:
        logger.error("[GET /route] fetching from table Route %s", e)
        return jsonify({"error": "Error de transacción"}), 500


@app.route('/route/<string:route_code>', methods=['PATCH'])
def patch_route(route_code : str) -> Tuple[Response, int]:
    current_user = ''
    company_id = ''

    validated_payroll = validated_route_payload()
    if (validated_payroll is None):
        return jsonify({"error": "Error al recibir datos"}), 500
    
    origin, destination, price, payroll_price = validated_payroll

    existing_entry : Route | None = db_session.get(Route, route_code)
    if existing_entry:
        if existing_entry.company_id != company_id:
            logger.error("[PATCH /route] updating table Route: invalid company_id: %s", company_id)
            return jsonify({"error": "Error al actualizar ruta"}), 503

        try:
            existing_entry.origin = origin
            existing_entry.destination = destination
            existing_entry.price = price
            existing_entry.payroll_price = payroll_price
            existing_entry.modification_user = current_user

            db_session.commit()
            logger.info("[PATCH /route] updating table Route: %s", route_code)
            return jsonify(
            {
                **asdict(existing_entry),
                "success": "Ruta actualizada exitosamente"
            }), 200
        
        except OperationalError as e:
            db_session.rollback()
            logger.error("[PATCH /route] updating table Route: connection %s", e)

            return jsonify({"error": "Error al actualizar ruta: problema de conexión"}), 503

        except SQLAlchemyError as e:
            db_session.rollback()
            logger.error("[PATCH /route] updating table Route: %s", e)
            return jsonify({"error": "Error al actualizar ruta"}), 500

    return jsonify({'error': 'Ruta no encontrado'}), 404


@app.route('/route/<string:route_code>', methods=['DELETE'])
def delete_route(route_code : str) -> Tuple[Response, int]:
    route : Route | None = db_session.get(Route, id)
    if route:
        try:
            route.deleted = True
            db_session.commit()
            logger.info("[DELETE /route] deleting from table Route: %s", route_code)
            return jsonify({'success': 'Ruta eliminada exitosamente'}), 200

        except OperationalError as e:
            db_session.rollback()
            logger.error("[DELETE /route] deleting table Route: connection %s", e)
            return jsonify({"error": "Error al eliminar ruta: problema de conexión"}), 503

        except SQLAlchemyError as e:
            db_session.rollback()
            logger.error("[DELETE /route] deleting table Route: %s", e)
            return jsonify({"error": "Error al eliminar ruta"}), 500

    return jsonify({'error': 'Ruta no encontrado'}), 404
