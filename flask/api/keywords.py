from flask import jsonify

from sqlalchemy import distinct

from app_config import logger
from models.models import Palabras, Cobranzas, Precios

from models.database import db_session

from app_config import app


@app.route('/keywords/', methods=['GET'])
def get_keywords():
    try:
        # conseguir chofer y chapa
        chofer_chapa_lista = Palabras.query.filter_by(
            tipo='chofer/chapa').all()

        lista_chofer = [chofer_chapa.palabra.split('/')[0] for chofer_chapa in chofer_chapa_lista]
        lista_chofer = sorted(lista_chofer)

        lista_producto = db_session.query(distinct(Cobranzas.producto), Cobranzas.fecha_viaje).order_by(Cobranzas.fecha_viaje.desc()).all()
        lista_producto = [producto[0] for producto in lista_producto]

        lista_origen = db_session.query(distinct(Precios.origen)).all()
        lista_origen = [origen[0] for origen in lista_origen]
        lista_origen = sorted(lista_origen)

        lista_destino = db_session.query(distinct(Precios.destino)).all()
        lista_destino = [destino[0] for destino in lista_destino]
        lista_destino = sorted(lista_destino)

        result = {
            'chofer': lista_chofer,
            'producto': lista_producto,
            'origen': lista_origen,
            'destino': lista_destino
        }

        return jsonify(result), 200

    except Exception as e:
        error_message = f"Error en GET de keywords: {str(e)}"
        logger.warning(error_message)
        return jsonify({"error": error_message}), 500


@app.route('/nomina/', methods=['GET'])
def get_nomina():
    try:
        keywords = Palabras.query.filter_by(tipo='chofer/chapa').all()
        result = [{
            'id': keyword.id,
            'chofer': keyword.palabra.split('/')[0],
            'chapa': keyword.palabra.split('/')[1]
        } for keyword in keywords]

        return jsonify(result), 200

    except Exception as e:
        error_message = f"Error en GET tabla Nomina {str(e)}"
        logger.warning(error_message)
        return jsonify({f"error": error_message}), 500


@app.route('/nomina/<string:id>', methods=['DELETE'])
def delete_nomina(id):
    entrada = db_session.get(Palabras, id)

    if entrada:
        try:
            db_session.delete(entrada)
            db_session.commit()
            return jsonify({'success': 'Nomina eliminada exitosamente'}), 200
        except Exception as e:
            db_session.rollback()
            error_message = f'Error al eliminar nomina {str(e)}'
            logger.warning(error_message)
            return jsonify({'error': error_message}), 500
    else:
        return jsonify({'error': 'Nomina no encontrado'}), 404
