from flask import request, jsonify

from sqlalchemy.exc import IntegrityError
from dateutil import parser
from decimal import Decimal

from flask_app import app
from utils.schema import db, Cobranzas
from utils.utils import agregar_cobranza, agregar_liquidacion, agregar_liquidacion_viaje, redondear


def post_cobranza():
    cobranza = request.json.get('cobranza')

    fecha_viaje = parser.isoparse(cobranza['fechaViaje']).date()
    chofer = cobranza['chofer']
    chapa = cobranza['chapa']
    producto = cobranza['producto']
    origen = cobranza['origen']
    destino = cobranza['destino']
    tiquet = cobranza['tiquet']
    kilos_origen = cobranza['kgOrigen']
    kilos_destino = cobranza['kgDestino']
    precio = cobranza['precio']
    fecha_creacion = parser.isoparse(cobranza['fechaCreacion']).date()

    try:
        id_cobranza = agregar_cobranza(fecha_viaje, chofer, chapa, producto, origen, destino, 
                        tiquet, kilos_origen, kilos_destino, precio, fecha_creacion)
    except Exception:
        return jsonify({"error": "Error al agregar entrada a la tabla Cobranzas"}), 500

    try:
        fecha_liquidacion = agregar_liquidacion(chofer)
    except IntegrityError:
        return jsonify({"error": "Error al agregar nueva liquidacion"}), 500

    try:
        agregar_liquidacion_viaje(id_cobranza, precio, fecha_liquidacion)
    except IntegrityError:
        return jsonify({"error": "Error al agregar a liquidacion del chofer"}), 500

    return jsonify({"message": "Entrada agregada exitosamente a la tabla Cobranzas"}), 200


def get_cobranza(fecha_creacion):
    try:
        fecha_creacion =  parser.isoparse(fecha_creacion).date()
        cobranzas = Cobranzas.query.filter_by(fecha_creacion=fecha_creacion).all()

        # Ordena las cobranzas por las columnas 'origen' y 'destino'
        cobranzas_ordenadas = sorted(cobranzas, key=lambda cobranza: (cobranza.origen, cobranza.destino, cobranza.fecha_viaje, cobranza.chofer))

        cobranzas_agrupadas = {}
        #calcula los subtotales
        for cobranza in cobranzas_ordenadas:
            origen_destino = f'{cobranza.origen}/{cobranza.destino}'

            if origen_destino not in cobranzas_agrupadas:
                cobranzas_agrupadas[origen_destino] = {
                    'viajes' : [], 'subtotalOrigen': 0, 'subtotalDestino': 0, 'subtotalDiferencia': 0, 'subtotalGS': 0
                }

            kilos_origen = int(cobranza.kilos_origen)
            kilos_destino = int(cobranza.kilos_destino)
            precio = Decimal(cobranza.precio)

            cobranzas_agrupadas[origen_destino]['viajes'] += [{
                'id': cobranza.id, 'fechaViaje': cobranza.fecha_viaje, 'chofer': cobranza.chofer, 'chapa': 
                cobranza.chapa, 'producto': cobranza.producto, 'origen': cobranza.origen, 'destino': cobranza.destino, 
                'tiquet': cobranza.tiquet, 'kgOrigen': kilos_origen, 'kgDestino': kilos_destino, 'precio': precio
            }]

            cobranzas_agrupadas[origen_destino]['subtotalOrigen'] += kilos_origen
            cobranzas_agrupadas[origen_destino]['subtotalDestino'] += kilos_destino
            cobranzas_agrupadas[origen_destino]['subtotalDiferencia'] += kilos_destino - kilos_origen
            cobranzas_agrupadas[origen_destino]['subtotalGS'] +=  redondear(precio * Decimal(kilos_destino))


        return jsonify(cobranzas_agrupadas), 200
    
    except Exception:
        return jsonify({"error": "Error en GET cobranza"}), 500


def put_cobranza(id):
    cobranza = request.json.get('cobranza')

    fecha_viaje = parser.isoparse(cobranza['fechaViaje']).date()
    chofer = cobranza['chofer']
    chapa = cobranza['chapa']
    producto = cobranza['producto']
    origen = cobranza['origen']
    destino = cobranza['destino']
    tiquet = cobranza['tiquet']
    kilos_origen = cobranza['kgOrigen']
    kilos_destino = cobranza['kgDestino']
    precio = cobranza['precio']

    existing_cobranza = Cobranzas.query.filter_by(id=id).first()

    if existing_cobranza is None:
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
    try:
        db.session.commit()
        app.logger.warning('Cobranza actualizada exitosamente')
    except IntegrityError:
        db.session.rollback()
        app.logger.warning('Error al actualizar cobranza')
        return jsonify({"error": "Error al actualizar Cobranzas"}), 500

    return jsonify({"message": "Entrada actualizada exitosamente en la tabla Cobranzas"}), 200    


def delete_cobranza(id):
    cobranza = db.session.get(Cobranzas, id)
    if cobranza:
        try:
            db.session.delete(cobranza)
            db.session.commit()
            return jsonify({'message': 'Cobranza eliminada exitosamente'}), 200
        except Exception:
            db.session.rollback()
            return jsonify({'error': 'Error al eliminar la cobranza'}), 500
    else:
        return jsonify({'error': 'Cobranza no encontrada'}), 404