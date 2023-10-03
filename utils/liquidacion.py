from flask import request, jsonify
from sqlalchemy.exc import IntegrityError
from sqlalchemy import distinct

from app_util import app
from utils.schema import db, Liquidaciones
from utils.utils import agregar_liquidacion, agregar_keywords


def post_liquidacion():
    chofer = request.json.get('chofer')

    try:
        agregar_liquidacion(chofer)
        agregar_keywords(chofer, '', '', '', '')
        return jsonify({"message": "Entrada agregada exitosamente a la tabla Liquidaciones"}), 200

    except Exception:
        return jsonify({"error": "Error al agregar a tabla del Liquidaciones"}), 500
    

def get_liquidacion(chofer, fecha):
    try:
        liquidacion = Liquidaciones.query.filter_by(chofer=chofer, fecha_liquidacion=fecha).first()
        return jsonify({'id': liquidacion.id, 'pagado': liquidacion.pagado}), 200

    except Exception:
        return jsonify({'error': f'Error GET Tabla Liquidaciones {chofer}/{fecha}'}), 404


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
        return jsonify({"message": "Entrada actualizada exitosamente en la tabla Liquidaciones"}), 200    

    except IntegrityError:
        db.session.rollback()
        app.logger.warning('Error al actualizar Liquidacion')
        return jsonify({"error": "Error al actualizar Liquidacion"}), 500


def get_liquidaciones():
    try:
        liquidaciones = db.session.query(distinct(Liquidaciones.chofer)).all()
        liquidaciones = sorted(
            liquidaciones, key=lambda liquidacion: liquidacion)
        return jsonify([liquidacion[0] for liquidacion in liquidaciones]), 200

    except Exception:
        return jsonify({"error": "Error en GET Tabla Liquidaciones"}), 500


def delete_liquidaciones(chofer):
    liquidaciones = Liquidaciones.query.filter_by(chofer=chofer).all()

    if liquidaciones:
        try:
            for liquidacion in liquidaciones:
                db.session.delete(liquidacion)

            db.session.commit()
            return jsonify({'message': f'Liquidaciones de {chofer} eliminadas exitosamente'}), 200
        except Exception:
            db.session.rollback()
            return jsonify({'error': 'Error al eliminar Liquidaciones'}), 500
    else:
        return jsonify({'error': 'Liquidaciones no encontradas'}), 404


def get_liquidaciones_chofer(chofer):
    try:
        liquidaciones = Liquidaciones.query.filter_by(chofer=chofer).all()
        liquidaciones_ordenadas = sorted(
            liquidaciones, key=lambda liquidacion: liquidacion.fecha_liquidacion, reverse=True)

        return jsonify([liquidacion.fecha_liquidacion for liquidacion in liquidaciones_ordenadas]), 200

    except Exception:
        return jsonify({'error': f'Liquidaciones de {chofer} no encontradas'}), 404


def delete_liquidaciones_chofer(chofer, fecha):
    liquidacion = Liquidaciones.query.filter_by(
        chofer=chofer, fecha_liquidacion=fecha).first()

    if liquidacion:
        try:
            db.session.delete(liquidacion)
            db.session.commit()
            return jsonify({'message': f'Liquidaciones de {chofer}/{fecha} eliminadas exitosamente'}), 200
        except Exception:
            db.session.rollback()
            return jsonify({'error': 'Error al eliminar Liquidaciones'}), 500
    else:
        return jsonify({'error': 'Liquidaciones no encontradas'}), 404