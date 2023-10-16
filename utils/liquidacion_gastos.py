from flask import request, jsonify

from dateutil import parser

from app_database import app
from utils.schema import db, LiquidacionGastos, Liquidaciones


def post_liquidacion_gasto():
    gasto = request.json.get('gasto')
    fecha = parser.isoparse(gasto['fecha']).date()
    chofer = gasto['chofer']
    boleta = gasto['boleta']
    importe = gasto['importe']
    fecha_liquidacion = parser.isoparse(gasto['fechaLiquidacion']).date()
    razon = gasto['razon']

    try:
        liq_id = Liquidaciones.query.filter_by(chofer=chofer, fecha_liquidacion=fecha_liquidacion).first().id

        new_gasto = LiquidacionGastos(
            fecha=fecha,
            boleta=boleta,
            importe=importe,
            razon=razon,
            id_liquidacion=liq_id
        )

        db.session.add(new_gasto)
        db.session.commit()
        return jsonify({'success': 'Liquidacion gasto agregado exitosamente'}), 200

    except Exception as e:
        db.session.rollback()
        error_message = f'Error en POST tabla LiquidacionGastos {str(e)}'
        app.logger.warning(error_message)
        return jsonify({'error': error_message}), 500



def get_liquidacion_gastos(chofer, fecha):
    try:
        gastos = db.session.query(LiquidacionGastos, Liquidaciones).join(
            Liquidaciones,
            Liquidaciones.id == LiquidacionGastos.id_liquidacion
        ).filter(
            Liquidaciones.chofer == chofer,
            Liquidaciones.fecha_liquidacion == fecha
        ).order_by(LiquidacionGastos.fecha.asc()).all()

        result = [{
            'id': gasto.id, 'fecha': gasto.fecha, 'boleta': gasto.boleta,
            'importe': gasto.importe, 'razon': gasto.razon
        } for gasto, _ in gastos]

        return jsonify(result), 200
    
    except Exception as e:
        error_message = f'Error en GET tabla LiquidacionGastos {str(e)}'
        app.logger.warning(error_message)
        return jsonify({'error': error_message}), 500


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
        return jsonify({"success": "Entrada actualizada exitosamente en la tabla LiquidacionGastos"}), 200    

    except Exception as e:
        db.session.rollback()
        error_message = f"Error al actualizar LiquidacionGasto {str(e)}"
        app.logger.warning(error_message)
        return jsonify({"error": error_message}), 500


def delete_liquidacion_gasto(id):
    gasto = db.session.get(LiquidacionGastos, id)

    if gasto:
        try:
            db.session.delete(gasto)
            db.session.commit()
            return jsonify({'success': 'LiquidacionGasto eliminado exitosamente'}), 200
        except Exception as e:
            db.session.rollback()
            error_message = f'Error al eliminar LiquidacionGasto {str(e)}'
            app.logger.warning(error_message)
            return jsonify({'error': error_message}), 500
    else:
        return jsonify({'error': 'LiquidacionGasto no encontrado'}), 404