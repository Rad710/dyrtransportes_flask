from flask import request, jsonify

from dateutil import parser
from decimal import localcontext, Decimal, ROUND_HALF_UP

from app_database import logger
from utils.schema import db, Cobranzas, LiquidacionViajes
from utils.utils import agregar_cobranza, agregar_liquidacion, agregar_liquidacion_viaje, string_to_int

from sqlalchemy.exc import IntegrityError

import re

def post_cobranza():
    cobranza = request.json.get('cobranza')
    return crear_cobranza_liquidacion(cobranza)


def crear_cobranza_liquidacion(cobranza):
    print(f'Cobranza: {cobranza}')
    fecha_viaje = parser.isoparse(re.sub(r'\s+', ' ', str(cobranza['fechaViaje']).strip())).date()
    chofer = re.sub(r'\s+', ' ', str(cobranza['chofer'])).strip()
    chapa = re.sub(r'\s+', ' ', str(cobranza['chapa'])).strip()
    producto = re.sub(r'\s+', ' ', str(cobranza['producto'])).strip()
    origen = re.sub(r'\s+', ' ', str(cobranza['origen'])).strip()
    destino = re.sub(r'\s+', ' ', str(cobranza['destino'])).strip()
    tiquet = string_to_int(re.sub(r'\s+', ' ', str(cobranza['tiquet'])).strip())
    kilos_origen = string_to_int(re.sub(r'\s+', ' ', str(cobranza['kgOrigen'])).strip())
    kilos_destino = string_to_int(re.sub(r'\s+', ' ', str(cobranza['kgDestino'])).strip())
    precio = re.sub(r'\s+', ' ', str(cobranza['precio'])).strip()
    precio_liquidacion = re.sub(r'\s+', ' ', str(cobranza['precioLiquidacion'])).strip()
    fecha_creacion = parser.isoparse(re.sub(r'\s+', ' ', str(cobranza['fechaCreacion'])).strip()).date()

    try:
        id_cobranza = agregar_cobranza(fecha_viaje, chofer, chapa, producto, origen, destino, 
                        tiquet, kilos_origen, kilos_destino, precio, fecha_creacion)
    except IntegrityError as e:
        error_message = f"Entrada duplicada {str(e)}"
        logger.warning(error_message)
        return jsonify({"error": error_message}), 500
    except Exception as e:
        error_message = f"Error al agregar entrada a la tabla Cobranzas {str(e)}"
        logger.warning(error_message)
        return jsonify({"error": error_message}), 500

    try:
        fecha_liquidacion = agregar_liquidacion(chofer)
    except Exception as e:
        error_message = f"Error al agregar nueva liquidacion {str(e)}"
        logger.warning(error_message)
        return jsonify({"error": error_message}), 500

    try:
        agregar_liquidacion_viaje(id_cobranza, precio_liquidacion, fecha_liquidacion, chofer)
    except Exception as e:
        error_message = f"Error al agregar a liquidacion del chofer {str(e)}"
        logger.warning(error_message)
        return jsonify({"error": error_message}), 500

    return jsonify({"success": "Entrada agregada exitosamente a la tabla Cobranzas"}), 200


def get_cobranza(fecha_creacion):
    try:
        fecha_creacion =  parser.isoparse(fecha_creacion).date()
        cobranzas = (
            db.session.query(Cobranzas, LiquidacionViajes)
            .join(LiquidacionViajes, Cobranzas.id == LiquidacionViajes.id)
            .filter(Cobranzas.fecha_creacion == fecha_creacion)
            .order_by(Cobranzas.chofer, Cobranzas.fecha_viaje)
            .all()
        )

        cobranzas_agrupadas = {}
        #calcula los subtotales
        for cobranza, liquidacion_viaje in cobranzas:
            origen_destino = f'{cobranza.producto}|{cobranza.origen}|{cobranza.destino}'

            if origen_destino not in cobranzas_agrupadas:
                cobranzas_agrupadas[origen_destino] = {
                    'viajes' : [], 'subtotalOrigen': 0, 'subtotalDestino': 0, 'subtotalDiferencia': 0, 'subtotalGS': 0
                }

            kilos_origen = int(cobranza.kilos_origen)
            kilos_destino = int(cobranza.kilos_destino)
            precio = Decimal(cobranza.precio)
            precio_liquidacion = Decimal(liquidacion_viaje.precio_liquidacion)

            cobranzas_agrupadas[origen_destino]['viajes'] += [{
                'id': cobranza.id, 'fechaViaje': cobranza.fecha_viaje, 'chofer': cobranza.chofer, 'chapa': 
                cobranza.chapa, 'producto': cobranza.producto, 'origen': cobranza.origen, 'destino': cobranza.destino, 
                'tiquet': cobranza.tiquet, 'kgOrigen': kilos_origen, 'kgDestino': kilos_destino, 
                'precio': precio, 'precioLiquidacion': precio_liquidacion
            }]

            cobranzas_agrupadas[origen_destino]['subtotalOrigen'] += kilos_origen
            cobranzas_agrupadas[origen_destino]['subtotalDestino'] += kilos_destino
            cobranzas_agrupadas[origen_destino]['subtotalDiferencia'] += kilos_destino - kilos_origen

            total_gs = precio * Decimal(kilos_destino)
            with localcontext() as ctx:
                ctx.rounding = ROUND_HALF_UP
                total_gs = int(total_gs.to_integral_value())

            cobranzas_agrupadas[origen_destino]['subtotalGS'] +=  total_gs

        result = list(cobranzas_agrupadas.items())
        result.sort(key=lambda x: x[0].split('|'))
        result = [pair[1] for pair in result]
        # result.sort(key=lambda x: (x['chofer'], x['fechaViaje']))
        return jsonify(result), 200
    
    except Exception as e:
        error_message = f"Error en GET cobranza {str(e)}"
        logger.warning(error_message)
        return jsonify({"error": error_message}), 500


def put_cobranza(id):
    cobranza = request.json.get('cobranza')

    fecha_viaje = parser.isoparse(cobranza['fechaViaje']).date()
    fecha_creacion = parser.isoparse(cobranza['fechaCreacion']).date()
    chofer = cobranza['chofer']
    chapa = cobranza['chapa']
    producto = cobranza['producto']
    origen = cobranza['origen']
    destino = cobranza['destino']
    tiquet = cobranza['tiquet']
    kilos_origen = cobranza['kgOrigen']
    kilos_destino = cobranza['kgDestino']
    precio = cobranza['precio']
    precio_liquidacion = cobranza['precioLiquidacion']

    existing_cobranza = Cobranzas.query.filter_by(id=id).first()
    existing_liquidacion = LiquidacionViajes.query.filter_by(id=id).first()

    if existing_cobranza is None or existing_liquidacion is None:
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
    existing_cobranza.fecha_creacion = fecha_creacion

    existing_liquidacion.precio_liquidacion = precio_liquidacion

    try:
        db.session.commit()
        logger.warning('Cobranza actualizada exitosamente')
    except Exception as e:
        db.session.rollback()
        error_message = f"Error al actualizar Cobranzas {str(e)}"
        logger.warning(error_message)
        return jsonify({"error": error_message}), 500

    return jsonify({"success": "Entrada actualizada exitosamente en la tabla Cobranzas"}), 200    


def delete_cobranza(id):
    cobranza = db.session.get(Cobranzas, id)
    if cobranza:
        try:
            db.session.delete(cobranza)
            db.session.commit()
            return jsonify({'success': 'Cobranza eliminada exitosamente'}), 200
        except Exception as e:
            db.session.rollback()
            error_message = f'Error al eliminar la cobranza {str(e)}'
            logger.warning(error_message)
            return jsonify({'error': error_message}), 500
    else:
        return jsonify({'error': 'Cobranza no encontrada'}), 404
