from flask import request, jsonify
from sqlalchemy import extract

from dateutil import parser
from sqlalchemy.exc import IntegrityError

from app_util import app
from utils.schema import db, Planillas


def post_planilla():
    try:
        fecha = request.json.get('fecha')
        fecha =  parser.isoparse(fecha).date()

        # entrada existe en la tabla de lista de planillas
        existing_entry = Planillas.query.filter_by(fecha=fecha).first()
        if existing_entry is None:
            #  agregar nueva entrada
            new_planilla = Planillas(
                fecha=fecha,
            )

            try:
                db.session.add(new_planilla)
                db.session.commit()
                app.logger.warning("Nueva entrada en lista de planillas")
            except IntegrityError as e:
                db.session.rollback()
                app.logger.warning("Error: No se pudo agregar la entrada a la lista de planillas")
                raise e
        else:
            app.logger.warning("Fecha ya existe en la lista de planillas")
    except Exception:
        return jsonify({"error": "Error al agregar a lista de planillas"}), 500


    return jsonify({"message": "Entrada agregada exitosamente a la lista de planillas"}), 200


# hacer query de todas las fechas de planillas
def get_planillas():
    try:
        # Query the database to get unique "fecha" values
        fechas = Planillas.query.all()
        # Extract the values from the query result
        fechas_ordenadas = sorted(fechas, key=lambda planilla: planilla.fecha)
        return jsonify( [planilla.fecha for planilla in fechas_ordenadas]), 200
    
    except Exception:
        return jsonify({"error": "Error en GET request a lista completa de planillas"}), 500


def delete_planilla(fecha):
    try:
        fecha =  parser.isoparse(fecha).date()
        # Query the Planillas record with the given fecha
        planilla_to_delete = Planillas.query.filter_by(fecha=fecha).first()
        # Check if the planilla exists
        if planilla_to_delete:
            # Delete the planilla
            db.session.delete(planilla_to_delete)
            db.session.commit()

            return jsonify({"message": "Planilla eliminada exitosamente"}), 200
        else:
            return jsonify({"error": "Planilla no encontrada"}), 404

    except Exception:
        return jsonify({"error": "Error en DELETE lista de planillas"}), 500



def get_planilla(year):
    try:
        # Filtrar las planillas por año utilizando SQLAlchemy
        planillas = Planillas.query.filter(extract('year', Planillas.fecha) == year).all()
        # Ordenar las planillas por fecha
        planillas_ordenadas = sorted(planillas, key=lambda planilla: planilla.fecha, reverse=True)
        planillas_ordenadas = [planilla.fecha for planilla in planillas_ordenadas]
        
        return jsonify(planillas_ordenadas)

    except Exception:
        return jsonify({"error": "Error en GET request a lista de planillas por año"}), 500