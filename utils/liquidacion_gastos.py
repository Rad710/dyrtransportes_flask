from flask import request, jsonify
from sqlalchemy.exc import IntegrityError

from dateutil import parser

from app_util import app
from utils.schema import db, LiquidacionGastos


def post_liquidacion_gasto():
    gasto = request.json.get('gasto')
    fecha = parser.isoparse(gasto['fecha']).date()
    chofer = gasto['chofer']
    boleta = gasto['boleta']
    importe = gasto['importe']
    fecha_liquidacion = parser.isoparse(gasto['fechaLiquidacion']).date()
    razon = gasto['razon']

    new_gasto = LiquidacionGastos(
        chofer=chofer,
        fecha=fecha,
        boleta=boleta,
        importe=importe,
        fecha_liquidacion=fecha_liquidacion,
        razon=razon
    )
    try:
        db.session.add(new_gasto)
        db.session.commit()
        return jsonify({'message': 'Liquidacion gasto agregado exitosamente'}), 200

    except Exception:
        return jsonify({'error': 'Error en POST tabla LiquidacionGastos'}), 500



def get_liquidacion_gastos(chofer, fecha):
    try:
        gastos = LiquidacionGastos.query.filter_by(chofer=chofer, fecha_liquidacion=fecha).order_by(LiquidacionGastos.fecha.asc()).all()
        
        result = [{
            'id': gasto.id, 'fecha': gasto.fecha, 'boleta': gasto.boleta,
            'importe': gasto.importe, 'razon': gasto.razon
        } for gasto in gastos]

        return jsonify(result), 200
    
    except Exception:
        return jsonify({'error': 'Error en GET tabla LiquidacionGastos'}), 500


def put_liquidacion_gasto(id):
    gasto = request.json.get('gasto')
    fecha = parser.isoparse(gasto['fecha']).date()
    boleta = gasto['boleta']
    importe = gasto['importe']
    razon = gasto['razon']

    existing_gasto = db.session.get(LiquidacionGastos, id)

    if existing_gasto is None:
        return jsonify({"error": "No se encontró cobranza a actualizar"}), 500

    existing_gasto.fecha = fecha
    existing_gasto.boleta = boleta
    existing_gasto.importe = importe
    existing_gasto.razon = razon
    try:
        db.session.commit()
        app.logger.warning('Liquidacion Gasto actualizado exitosamente')
        return jsonify({"message": "Entrada actualizada exitosamente en la tabla LiquidacionGastos"}), 200    

    except IntegrityError:
        db.session.rollback()
        app.logger.warning('Error al actualizar Liquidacion Gasto')
        return jsonify({"error": "Error al actualizar LiquidacionGasto"}), 500


def delete_liquidacion_gasto(id):
    gasto = db.session.get(LiquidacionGastos, id)

    if gasto:
        try:
            db.session.delete(gasto)
            db.session.commit()
            return jsonify({'message': 'LiquidacionGasto eliminado exitosamente'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Error al eliminar LiquidacionGasto'}), 500
    else:
        return jsonify({'error': 'LiquidacionGasto no encontrado'}), 404