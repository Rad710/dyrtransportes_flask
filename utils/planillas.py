from flask import request, jsonify
from sqlalchemy import extract

from dateutil import parser

from app_database import app
from utils.schema import db, Planillas

def post_planilla():
    fecha = request.json.get('fecha')
    return post_planilla(fecha)

def agregar_planilla(fecha):
    try:
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
            except Exception as e:
                db.session.rollback()
                app.logger.warning(f"Error: No se pudo agregar la entrada a la lista de planillas {str(e)}")
                raise e
        else:
            app.logger.warning("Fecha ya existe en la lista de planillas")
    except Exception as e:
        error_message = f'Error al agregar a lista de planillas {str(e)}'
        app.logger.warning(error_message)
        return jsonify({"error": error_message}), 500


    return jsonify({"success": "Entrada agregada exitosamente a la lista de planillas"}), 200


# hacer query de todas las fechas de planillas
def get_planillas():
    try:
        # Query the database to get unique "fecha" values
        fechas = Planillas.query.all()
        # Extract the values from the query result
        fechas_ordenadas = sorted(fechas, key=lambda planilla: planilla.fecha)
        return jsonify( [planilla.fecha for planilla in fechas_ordenadas]), 200
    
    except Exception as e:
        error_message = f'Error en GET request a lista completa de planillas {str(e)}'
        app.logger.warning(error_message)
        return jsonify({"error": error_message}), 500


def delete_planilla(fecha):
    try:
        fecha =  parser.isoparse(fecha).date()

        planilla_to_delete = Planillas.query.filter_by(fecha=fecha).first()
        # Delete the planilla
        db.session.delete(planilla_to_delete)
        db.session.commit()

        return jsonify({"success": "Planilla y Cobranzas eliminados exitosamente"}), 200

    except Exception as e:
        error_message = f'Error en DELETE lista de planillas {str(e)}'
        app.logger.warning(error_message)
        return jsonify({"error": error_message}), 500



def get_planilla(year):
    try:
        # Filtrar las planillas por año utilizando SQLAlchemy
        planillas = Planillas.query.filter(extract('year', Planillas.fecha) == year).all()
        # Ordenar las planillas por fecha
        planillas_ordenadas = sorted(planillas, key=lambda planilla: planilla.fecha, reverse=True)
        planillas_ordenadas = [planilla.fecha for planilla in planillas_ordenadas]
        
        return jsonify(planillas_ordenadas)

    except Exception as e:
        error_message = f'Error en GET request a lista de planillas por año {str(e)}'
        app.logger.warning(error_message)
        return jsonify({"error": error_message}), 500