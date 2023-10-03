from flask import request, jsonify
from sqlalchemy.exc import IntegrityError

from dateutil import parser

from flask_app import app
from utils.schema import db, LiquidacionViajes, Cobranzas
from utils.utils import agregar_cobranza


def post_liquidacion_viaje():
    liquidacion_viaje = request.json.get('liquidacionViaje')

    fecha_viaje = parser.isoparse(liquidacion_viaje['fechaViaje']).date()
    chofer = liquidacion_viaje['chofer']
    chapa = liquidacion_viaje['chapa']
    producto = liquidacion_viaje['producto']
    origen = liquidacion_viaje['origen']
    destino = liquidacion_viaje['destino']
    tiquet = liquidacion_viaje['tiquet']
    kilos_origen = liquidacion_viaje['kgOrigen']
    kilos_destino = liquidacion_viaje['kgDestino']
    precio = liquidacion_viaje['precio']
    precio_liquidacion = liquidacion_viaje['precioLiquidacion']
    fecha_liquidacion = parser.isoparse(
        liquidacion_viaje['fechaLiquidacion']).date()

    try:
        id_cobranza = agregar_cobranza(fecha_viaje, chofer, chapa, producto, origen, destino,
                                       tiquet, kilos_origen, kilos_destino, precio, None)
    except Exception:
        return jsonify({"error": "Error al agregar entrada a la tabla Cobranzas"}), 500

    liq = LiquidacionViajes(
        id=id_cobranza, precio_liquidacion=precio_liquidacion, fecha_liquidacion=fecha_liquidacion)

    try:
        db.session.add(liq)
        db.session.commit()
        app.logger.warning("Nueva entrada en lista de liquidaciones agregada")
        return jsonify({'message': 'Liquidaciones Viaje agregado exitosamente'}), 200
    except IntegrityError as e:
        db.session.rollback()
        app.logger.warning("No se pudo cargar nueva entrada en lista de liquidaciones")
        return jsonify({'error': 'Error al cargar en tabla Liquidaciones Viajes'}), 500


def get_liquidacion_viajes(chofer, fecha):
    try:
        viajes = (
            db.session.query(Cobranzas, LiquidacionViajes)
            .join(
                LiquidacionViajes,
                Cobranzas.id == LiquidacionViajes.id
            )
            .filter(
                LiquidacionViajes.fecha_liquidacion == fecha,
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

    except Exception:
        return jsonify({'error': 'Error en GET tabla Liquidaciones Viajes'}), 500
    

def put_liquidacion_viaje(id):
    viaje = request.json.get('liquidacionViaje')

    fecha_viaje = parser.isoparse(viaje['fechaViaje']).date()
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
    try:
        db.session.commit()
        app.logger.warning('Liquidacion Viaje y Cobranza actualizada exitosamente')
    except IntegrityError:
        db.session.rollback()
        app.logger.warning('Error al actualizar Liquidacion Viaje y Cobranza')
        return jsonify({"error": "Error al actualizar Liquidacion Viaje y Cobranza"}), 500

    return jsonify({"message": "Entrada actualizada exitosamente en la tabla Cobranzas y LiquidacionViajes"}), 200    


def delete_liquidacion_viaje(id):
    viaje = db.session.get(LiquidacionViajes, id)

    if viaje:
        try:
            db.session.delete(viaje)
            db.session.commit()
            return jsonify({'message': 'Viaje eliminada exitosamente'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Error al eliminar la Viaje'}), 500
    else:
        return jsonify({'error': 'Viaje no encontrada'}), 404