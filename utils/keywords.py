from flask import jsonify

from sqlalchemy import distinct

from utils.schema import db, Palabras, Cobranzas, Precios


def get_keywords():
    try:
        # conseguir chofer y chapa
        chofer_chapa_lista = Palabras.query.filter_by(
            tipo='chofer/chapa').all()

        lista_chofer = [chofer_chapa.palabra.split('/')[0] for chofer_chapa in chofer_chapa_lista]
        lista_chofer = sorted(lista_chofer)

        lista_producto = db.session.query(distinct(Cobranzas.producto)).order_by(Cobranzas.fecha_viaje.desc()).all()
        lista_producto = [producto[0] for producto in lista_producto]

        lista_origen = db.session.query(distinct(Precios.origen)).all()
        lista_origen = [origen[0] for origen in lista_origen]
        lista_origen = sorted(lista_origen)

        lista_destino = db.session.query(distinct(Precios.destino)).all()
        lista_destino = [destino[0] for destino in lista_destino]
        lista_destino = sorted(lista_destino)

        result = {
            'chofer': lista_chofer,
            'producto': lista_producto,
            'origen': lista_origen,
            'destino': lista_destino
        }

        return jsonify(result), 200

    except Exception:
        return jsonify({"error": "Error en GET de keywords"}), 500


def get_nomina():
    try:
        keywords = Palabras.query.filter_by(tipo='chofer/chapa').all()
        result = [{
            'id': keyword.id,
            'chofer': keyword.palabra.split('/')[0],
            'chapa': keyword.palabra.split('/')[1]
        } for keyword in keywords]

        return jsonify(result), 200

    except Exception:
        return jsonify({"error": "Error en GET tabla Nomina"}), 500


def delete_nomina(id):
    entrada = db.session.get(Palabras, id)

    if entrada:
        try:
            db.session.delete(entrada)
            db.session.commit()
            return jsonify({'message': 'Nomina eliminada exitosamente'}), 200
        except Exception:
            db.session.rollback()
            return jsonify({'error': 'Error al eliminar nomina'}), 500
    else:
        return jsonify({'error': 'Nomina no encontrado'}), 404
