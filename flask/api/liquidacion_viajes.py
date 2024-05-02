from flask import request, jsonify

from dateutil import parser

from app_database import logger
from utils.schema import db, LiquidacionViajes, Cobranzas, Liquidaciones
from utils.utils import agregar_cobranza, string_to_int

import re

def post_liquidacion_viaje():
    liquidacion_viaje = request.json.get('liquidacionViaje')

    fecha_viaje = parser.isoparse(re.sub(r'\s+', ' ', str(liquidacion_viaje['fechaViaje'])).strip()).date()

    chofer = re.sub(r'\s+', ' ', str(liquidacion_viaje['chofer'])).strip()
    chapa = re.sub(r'\s+', ' ', str(liquidacion_viaje['chapa'])).strip()
    producto = re.sub(r'\s+', ' ', str(liquidacion_viaje['producto'])).strip()
    origen = re.sub(r'\s+', ' ', str(liquidacion_viaje['origen'])).strip()
    destino = re.sub(r'\s+', ' ', str(liquidacion_viaje['destino'])).strip()
    tiquet = string_to_int(re.sub(r'\s+', ' ', str(liquidacion_viaje['tiquet'])).strip())
    kilos_origen = string_to_int(re.sub(r'\s+', ' ', str(liquidacion_viaje['kgOrigen'])).strip())
    kilos_destino = string_to_int(re.sub(r'\s+', ' ', str(liquidacion_viaje['kgDestino'])).strip())
    precio = re.sub(r'\s+', ' ', str(liquidacion_viaje['precio'])).strip()
    precio_liquidacion = re.sub(r'\s+', ' ', str(liquidacion_viaje['precioLiquidacion'])).strip()
    fecha_liquidacion = parser.isoparse(re.sub(r'\s+', ' ', str(liquidacion_viaje['fechaLiquidacion'])).strip()).date()

    try:
        id_cobranza = agregar_cobranza(fecha_viaje, chofer, chapa, producto, origen, destino,
                                       tiquet, kilos_origen, kilos_destino, precio, None)
    except Exception as e:
        error_message = f"Error al agregar entrada a la tabla Cobranzas {str(e)}"
        logger.warning(error_message)
        return jsonify({"error": error_message}), 500

    try:
        id_liquidacion = Liquidaciones.query.filter_by(chofer=chofer, fecha_liquidacion=fecha_liquidacion).first().id
        liq = LiquidacionViajes(id=id_cobranza, precio_liquidacion=precio_liquidacion, 
                                id_liquidacion=id_liquidacion)
            
        db.session.add(liq)
        db.session.commit()
        logger.warning("Nueva entrada en lista de liquidaciones agregada")
        return jsonify({'success': 'Liquidaciones Viaje agregado exitosamente'}), 200
    except Exception as e:
        db.session.rollback()
        error_message = f'Error al cargar en tabla Liquidaciones Viajes {str(e)}'
        logger.warning(error_message)
        return jsonify({'error': error_message}), 500


def get_liquidacion_viajes(chofer, fecha):
    try:
        id_liquidacion = Liquidaciones.query.filter_by(chofer=chofer, fecha_liquidacion=fecha).first().id

        viajes = (
            db.session.query(Cobranzas, LiquidacionViajes)
            .join(
                LiquidacionViajes,
                Cobranzas.id == LiquidacionViajes.id
            )
            .filter(
                LiquidacionViajes.id_liquidacion == id_liquidacion,
                Cobranzas.chofer == chofer
            )
            # Sort in ascending order by fecha_viaje
            .order_by(Cobranzas.fecha_viaje.asc())
            .all()
        )

        result = [{
            'id': liquidacion.id, 'fechaViaje': cobranza.fecha_viaje, 'chapa': cobranza.chapa, 
            'producto': cobranza.producto, 'origen': cobranza.origen, 'destino': cobranza.destino, 
            'tiquet': cobranza.tiquet, 'kgOrigen': cobranza.kilos_origen, 'kgDestino': cobranza.kilos_destino, 
            'precio': cobranza.precio, 'precioLiquidacion': liquidacion.precio_liquidacion
        } for cobranza, liquidacion in viajes]

        return jsonify(result), 200

    except Exception as e:
        error_message = f'Error en GET tabla Liquidaciones Viajes {str(e)}'
        logger.warning(error_message)
        return jsonify({'error': error_message}), 500
    

def put_liquidacion_viaje(id):
    viaje = request.json.get('liquidacionViaje')

    print(f'Viaje: {viaje}')

    fecha_viaje = parser.isoparse(viaje['fechaViaje']).date()
    fecha_liquidacion = parser.isoparse(viaje['fechaLiquidacion']).date()
    chofer = viaje['chofer']
    chapa = viaje['chapa']
    producto = viaje['producto']
    origen = viaje['origen']
    destino = viaje['destino']
    tiquet = viaje['tiquet']
    kilos_origen = viaje['kgOrigen']
    kilos_destino = viaje['kgDestino']
    precio = viaje['precio']
    precio_liquidacion = viaje['precioLiquidacion']

    existing_cobranza = db.session.get(Cobranzas, id)
    existing_liquidacion_viaje = db.session.get(LiquidacionViajes, id)
    existing_liquidacion_id = Liquidaciones.query.filter_by(chofer=chofer, fecha_liquidacion=fecha_liquidacion).first().id

    if existing_cobranza is None or existing_liquidacion_viaje is None:
        return jsonify({"error": "No se encontró cobranza a actualizar"}), 500

    existing_cobranza.fecha_viaje = fecha_viaje
    existing_cobranza.chofer = chofer
    existing_cobranza.chapa = chapa
    existing_cobranza.producto = producto
    existing_cobranza.origen = origen
    existing_cobranza.destino = destino
    existing_cobranza.tiquet = tiquet
    existing_cobranza.kilos_origen = kilos_origen
    existing_cobranza.kilos_destino = kilos_destino
    existing_cobranza.precio = precio

    existing_liquidacion_viaje.precio_liquidacion = precio_liquidacion
    existing_liquidacion_viaje.id_liquidacion = existing_liquidacion_id

    try:
        db.session.commit()
        logger.warning('Liquidacion Viaje y Cobranza actualizada exitosamente')
    except Exception as e:
        db.session.rollback()
        error_message = f'Error al actualizar Liquidacion Viaje y Cobranza {str(e)}'
        logger.warning(error_message)
        return jsonify({"error": error_message}), 500

    return jsonify({"success": "Entrada actualizada exitosamente en la tabla Cobranzas y LiquidacionViajes"}), 200    


def delete_liquidacion_viaje(id):
    viaje = db.session.get(LiquidacionViajes, id)
    cobranza = db.session.get(Cobranzas, id)

    try:
        if cobranza.fecha_creacion is None:
            db.session.delete(cobranza)

        db.session.delete(viaje)
        db.session.commit()
        return jsonify({'success': 'Viaje eliminado exitosamente'}), 200
    except Exception as e:
        db.session.rollback()
        error_message = f'Error al eliminar Viaje {str(e)}'
        logger.warning(error_message)
        return jsonify({'error': error_message}), 500