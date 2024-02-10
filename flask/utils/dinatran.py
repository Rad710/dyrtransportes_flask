from flask import jsonify
from sqlalchemy import text

from dateutil import parser

from app_database import logger
from utils.schema import db


def get_informe_dinatran(fecha_inicio, fecha_fin):
    try:
        fecha_inicio = parser.isoparse(fecha_inicio).date()
        fecha_fin = parser.isoparse(fecha_fin).date()

        params = {'fecha_inicio': fecha_inicio, 'fecha_fin': fecha_fin}

        viajes_query = text("""
                            SELECT 
                                chapa, COUNT(cobranzas.id) as viajes, 
                                SUM(kilos_origen) as total_origen, 
                                SUM(kilos_destino) as total_destino, 
                                SUM(precio * kilos_destino) as total_flete, 
                                SUM(precio_liquidacion * kilos_destino) as total_liquidacion 
                            FROM cobranzas
                            JOIN liquidacion_viajes ON liquidacion_viajes.id = cobranzas.id   
                            WHERE fecha_viaje BETWEEN :fecha_inicio AND :fecha_fin 
                            GROUP BY chapa""")

        # Execute the query with parameters
        viajes = db.session.execute(viajes_query, params).fetchall()

        viajes_parsed = {f'{viaje[0]}': {
            'viajes': viaje[1], 'totalOrigen': viaje[2], 'totalDestino': viaje[3],
            'totalFlete': viaje[4], 'totalLiquidacion': viaje[5]
        } for viaje in viajes}

        return jsonify(viajes_parsed), 200

    except Exception as e:
        error_message = f'Error en GET Statistics {str(e)}'
        logger.warning(error_message)
        return jsonify({'error': error_message}), 500