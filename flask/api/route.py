from flask import request, jsonify

from app.app_config import logger
from models.schema import Route
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from app.app import app
from sqlalchemy import asc
from typing import List

from models.database import db_session


@app.route('/route', methods=['POST'])
def post_route():
    if (not request.data):
        logger.warning("Route request.data is empty: %s", request.data)
        return jsonify({"error": "Data could not be received"}), 500

    payload = request.get_json()

    logger.debug("payload: %s", payload)

    origin: str | None = payload['origin']
    destination = payload['destination']
    price = payload['price']
    payrollPrice = payload['payroll_price']

    current_user = ''
    company_id = ''

    existing_entry: Route | None = Route.query.filter_by(
        origin=origin, destination=destination, deleted = False
    ).first()

    logger.debug("existing_entry: %s", existing_entry)


    if existing_entry is not None:
        logger.warning("Duplicate Route: %s", existing_entry)
        return jsonify({"error": "Entrada ya existe en la tabla Precios"}), 500

    new_route = Route(origin=origin, destination=destination,
                      price=price, payroll_price=payrollPrice,
                      modification_user=current_user, company_id=company_id)

    try:
        db_session.add(new_route)
        db_session.commit()
        logger.info("new_route added to Route: %s", new_route)
        return jsonify({"success": "Entrada agregada exitosamente a la tabla Precios"}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("Error en Tabla Route: problema de conexión con la base de datos %s", e)  # Might be more severe

        return jsonify({"error": 
            f"Error en Tabla Route: problema de conexión con la base de datos {str(e)}"
        }), 503  # Service unavailableposible

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("Error al agregar a tabla Route %s", e)
        return jsonify({"error": f"Error al agregar a tabla Route {str(e)}"}), 500


@app.route('/routes', methods=['GET'])
def get_route_list():
    try:
        current_user = ''
        company_id = ''

        routes: List[Route] = Route.query.filter_by(
            deleted = False, company_id = company_id
        ).order_by(
            asc(Route.origin),
            asc(Route.destination)
        ).all()

        result = [{
                'routeCode': route.route_code, 
                'origin': route.origin, 'destination': route.destination, 
                'price': route.price, 'payrollPrice': route.payroll_price
            } for route in routes]
        
        logger.info("Returned Route list of length: %s", len(result))
        
        return jsonify(result), 200
    
    except SQLAlchemyError as e:
        logger.error("Error in GET /routes %s", e)
        return jsonify({"error": f"Error en GET tabla Route {str(e)}"}), 500


@app.route('/route/<string:route_code>', methods=['GET'])
def get_route(route_code):
    try:
        current_user = ''
        company_id = ''

        route : Route = Route.query.filter_by(
            route_code=route_code, deleted=False,
            company_id=company_id
            ).first()

        if route is None:
            return jsonify({"error": "No se encontro precio en tabla Precios"}), 404
        
        result = {
            'routeCode': route.route_code,
            'origin': route.origin, 'destination': route.destination,
            'price': route.price, 'payrollPrice': route.payroll_price
        }

        logger.info("Returned matching route with code: %s", result['routeCode'])

        return jsonify(result), 200

    except SQLAlchemyError as e:
        logger.error("Error in GET /route/<string:code> %s", e)
        return jsonify({"error": f"Error en GET tabla Route {str(e)}"}), 500


@app.route('/precios/<string:route_code>', methods=['PATCH'])
def put_precio(route_code):
    viaje = request.json.get('viaje')
    origen = viaje['origen']
    destino = viaje['destino'] 
    
    precio = viaje['precio']
    precio_liquidacion = viaje['precioLiquidacion']
    
    entrada = db_session.get(Route, route_code)
    
    if entrada:
        try:
            entrada.origen = origen
            entrada.destino = destino
            entrada.precio = precio
            entrada.precio_liquidacion = precio_liquidacion

            db_session.commit()
            return jsonify({'success': 'Precio actualizado exitosamente'}), 200
        except Exception as e:
            db_session.rollback()
            error_message = f"Error al actualizar precio {str(e)}"
            logger.warning(error_message)
            return jsonify({'error': error_message}), 500
    else:
        return jsonify({'error': 'Precio no encontrado'}), 404



@app.route('/precios/<string:route_code>', methods=['DELETE'])
def soft_delete_precio(route_code):
    route = db_session.get(Route, id)
    
    if route:
        try:
            route.deleted = True
            db_session.commit()
            return jsonify({'success': 'Precio eliminado exitosamente'}), 200
        except Exception as e:
            db_session.rollback()
            error_message = f"Error al eliminar precio {str(e)}"
            logger.warning(error_message)
            return jsonify({'error': error_message}), 500
    else:
        return jsonify({'error': 'Precio no encontrado'}), 404