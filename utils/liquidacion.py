from flask import request, jsonify
from sqlalchemy import distinct, desc
from app_database import app
from utils.schema import db, Liquidaciones
from utils.utils import agregar_liquidacion, agregar_keywords

import re

def post_liquidacion():
    chofer = request.json.get('chofer')
    chofer = re.sub(r'\s+', ' ', str(chofer)).strip()
    try:
        agregar_liquidacion(chofer)
        agregar_keywords(chofer, '', '', '', '')
        return jsonify({"success": "Entrada agregada exitosamente a la tabla Liquidaciones"}), 200

    except Exception as e:
        error_message = f'Error al agregar a tabla del Liquidaciones {str(e)}'
        app.logger.warning(error_message)
        return jsonify({"error": error_message}), 500
    

def get_liquidacion(chofer, fecha):
    try:
        liquidacion = Liquidaciones.query.filter_by(chofer=chofer, fecha_liquidacion=fecha).first()
        return jsonify({'id': liquidacion.id, 'pagado': liquidacion.pagado}), 200

    except Exception as e:
        error_message = f'Error GET Tabla Liquidaciones {chofer}/{fecha} {str(e)}'
        app.logger.warning(error_message)
        return jsonify({'error': error_message}), 500


def put_liquidacion(id):
    liquidacion = request.json.get('liquidacion')
    app.logger.warning(liquidacion)
    # fecha_liquidacion = parser.isoparse(liquidacion['fechaLiquidacion']).date()
    # chofer = liquidacion['chofer']
    pagado = liquidacion['pagado']

    existing_liquidacion = db.session.get(Liquidaciones, id)

    if existing_liquidacion is None:
        return jsonify({"error": "No se encontró Liquidacion a actualizar"}), 404

    existing_liquidacion.pagado = pagado
    try:
        db.session.commit()
        app.logger.warning('Liquidacion actualizada exitosamente')
        return jsonify({"success": "Entrada actualizada exitosamente en la tabla Liquidaciones"}), 200    

    except Exception as e:
        db.session.rollback()
        error_message = f'Error al actualizar Liquidacion {str(e)}'
        app.logger.warning(error_message)
        return jsonify({"error": error_message}), 500


def get_liquidaciones():
    try:
        liquidaciones = db.session.query(distinct(Liquidaciones.chofer)).all()
        liquidaciones = sorted(
            liquidaciones, key=lambda liquidacion: liquidacion)
        return jsonify([liquidacion[0] for liquidacion in liquidaciones]), 200

    except Exception as e:
        error_message = f'Error en GET Tabla Liquidaciones {str(e)}'
        app.logger.warning(error_message)
        return jsonify({"error": error_message}), 500


def delete_liquidaciones(chofer):
    liquidaciones = Liquidaciones.query.filter_by(chofer=chofer).all()

    if liquidaciones:
        try:
            for liquidacion in liquidaciones:
                db.session.delete(liquidacion)

            db.session.commit()
            return jsonify({'success': f'Liquidaciones de {chofer} eliminadas exitosamente'}), 200
        except Exception as e:
            db.session.rollback()
            error_message = f'Error al eliminar Liquidaciones {str(e)}'
            app.logger.warning(error_message)
            return jsonify({'error': error_message}), 500
    else:
        return jsonify({'error': 'Liquidaciones no encontradas'}), 404


def get_liquidaciones_chofer(chofer):
    try:
        liquidaciones = Liquidaciones.query.filter_by(chofer=chofer).order_by(desc(Liquidaciones.fecha_liquidacion)).all()
        return jsonify([
            {
                'fechaLiquidacion': liquidacion.fecha_liquidacion, 'pagado': liquidacion.pagado
            } for liquidacion in liquidaciones
            ]), 200

    except Exception as e:
        error_message = f'Liquidaciones de {chofer} no encontradas {str(e)}'
        app.logger.warning(error_message)
        return jsonify({'error': error_message}), 500


def delete_liquidaciones_chofer(chofer, fecha):
    liquidacion = Liquidaciones.query.filter_by(
        chofer=chofer, fecha_liquidacion=fecha).first()

    if liquidacion:
        try:
            db.session.delete(liquidacion)
            db.session.commit()
            return jsonify({'success': f'Liquidaciones de {chofer}/{fecha} eliminadas exitosamente'}), 200
        except Exception as e:
            db.session.rollback()
            error_message = f'Error al eliminar Liquidaciones {str(e)}'
            app.logger.warning(error_message)
            return jsonify({'error': error_message}), 500
    else:
        return jsonify({'error': 'Liquidaciones no encontradas'}), 404