from flask import request, jsonify

from utils.schema import db, Precios
from utils.utils import agregar_precio


def post_precio():
    viaje = request.json.get('viaje')

    origen = viaje['origen']
    destino = viaje['destino']
    precio = viaje['precio']
    precio_liquidacion = viaje['precioLiquidacion']

    return agregar_precio(origen, destino, precio, precio_liquidacion)


def get_precios():
    try:
        entradas = Precios.query.all()
        entradas_ordenados = sorted(entradas, key=lambda entrada: (entrada.origen, entrada.destino))
        result = [{
            'id': entrada.id, 'origen': entrada.origen, 'destino': entrada.destino, 
            'precio': entrada.precio, 'precioLiquidacion': entrada.precio_liquidacion
            } for entrada in entradas_ordenados]
        
        return jsonify(result), 200
    
    except Exception:
        return jsonify({"error": "Error en GET tabla Precios"}), 500


def get_precio(origen_destino):
    try:
        origen_destino = origen_destino.split('-')
        entrada = Precios.query.filter_by(origen=origen_destino[0], destino=origen_destino[1]).first()

        if entrada is not None:
            result = {'precio': entrada.precio, 'precioLiquidacion': entrada.precio_liquidacion}
            
            return jsonify(result), 200
        else:
            return jsonify({"error": "No se encotro precio en tabla Precios"}), 500
    except Exception:
        return jsonify({"error": "Error en GET tabla Precios"}), 500


def put_precio(id):
    viaje = request.json.get('viaje')
    origen = viaje['origen']
    destino = viaje['destino'] 
    
    precio = viaje['precio']
    precio_liquidacion = viaje['precioLiquidacion']
    
    entrada = db.session.get(Precios, id)
    
    if entrada:
        entrada.origen = origen
        entrada.destino = destino
        entrada.precio = precio
        entrada.precio_liquidacion = precio_liquidacion

        try:
            db.session.commit()
            return jsonify({'message': 'Precio actualizado exitosamente'}), 200
        except Exception:
            db.session.rollback()
            return jsonify({'error': 'Error al actualizar precio'}), 500
    else:
        return jsonify({'error': 'Precio no encontrado'}), 404


def delete_precio(id):
    entrada = db.session.get(Precios, id)
    
    if entrada:
        try:
            db.session.delete(entrada)
            db.session.commit()
            return jsonify({'message': 'Precio eliminado exitosamente'}), 200
        except Exception:
            db.session.rollback()
            return jsonify({'error': 'Error al eliminar precio'}), 500
    else:
        return jsonify({'error': 'Precio no encontrado'}), 404