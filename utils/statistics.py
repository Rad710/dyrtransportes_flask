from flask import jsonify, request
from sqlalchemy import text

from dateutil import parser

from utils.schema import db

from app_database import app

def get_statistics(fecha_inicio, fecha_fin):
    try:
        ipread1 = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        app.logger.warning(f"The client IP is: {ipread1}")

        fecha_inicio = parser.isoparse(fecha_inicio).date()
        fecha_fin = parser.isoparse(fecha_fin).date()

        params = {'fecha_inicio': fecha_inicio, 'fecha_fin': fecha_fin}

        viajes_query = text("""
                            SELECT
                                chofer, COUNT(cobranzas.id) as viajes,
                                SUM(kilos_origen) as total_origen,
                                SUM(kilos_destino) as total_destino,
                                SUM(precio * kilos_destino) as total_flete,
                                SUM(precio_liquidacion * kilos_destino) as total_liquidacion
                            FROM cobranzas
                            JOIN liquidacion_viajes ON liquidacion_viajes.id = cobranzas.id
                            WHERE fecha_viaje BETWEEN :fecha_inicio AND :fecha_fin
                            GROUP BY chofer
                            """)

        # Execute the query with parameters
        viajes = db.session.execute(viajes_query, params).fetchall()

        facturado_query = text("""
                            SELECT chofer, SUM(importe) as total_facturado 
                            FROM liquidacion_gastos
                            JOIN liquidaciones ON liquidacion_gastos.id_liquidacion = liquidaciones.id
                            WHERE (fecha BETWEEN :fecha_inicio AND :fecha_fin) AND boleta IS NOT NULL
                            GROUP BY chofer;
                            """)

        gasto_facturado = db.session.execute(facturado_query, params).fetchall()

        no_facturado_query = text("""
                            SELECT chofer, SUM(importe) as total_facturado 
                            FROM liquidacion_gastos
                            JOIN liquidaciones ON liquidacion_gastos.id_liquidacion = liquidaciones.id
                            WHERE (fecha BETWEEN :fecha_inicio AND :fecha_fin) AND boleta IS NULL
                            GROUP BY chofer;
                            """)

        gasto_no_facturado = db.session.execute(no_facturado_query, params).fetchall()

        result = {}
        result_total = {'viajes': 0, 'kgOrigen': 0, 'kgDestino': 0, 'totalFletes': 0, 'totalPerdidas': 0,
                        'totalLiquidacionViajes': 0, 'totalGastoFacturado': 0, 'totalGastoNoFacturado': 0}

        default_chofer =  {
                'viajes': 0, 'totalOrigen': 0, 'totalDestino': 0, 'totalFlete': 0,
                'totalLiquidacion': 0, 'totalFacturado': 0, 'totalNoFacturado': 0
            }

        for viaje in viajes:
            chofer = viaje[0]
            viajes = viaje[1]
            total_origen = viaje[2]
            total_destino = viaje[3]
            total_fletes = viaje[4]
            total_liquidacion = viaje[5]

            result_total['viajes'] += viajes
            result_total['kgOrigen'] += total_origen
            result_total['kgDestino'] += total_destino
            result_total['totalFletes'] += total_fletes
            result_total['totalLiquidacionViajes'] += total_liquidacion

            if chofer not in result:
                result[chofer] = default_chofer.copy()

            result[chofer].update({
                'viajes': viajes, 'totalOrigen': total_origen, 'totalDestino': total_destino,
                'totalFlete': total_fletes, 'totalLiquidacion': total_liquidacion
            })


        for gasto in gasto_facturado:
            chofer = gasto[0]
            total_facturado = gasto[1]
            result_total['totalGastoFacturado'] += total_facturado

            if chofer not in result:
                result[chofer] = default_chofer.copy()

            result[chofer].update({'totalFacturado': total_facturado})

        for gasto in gasto_no_facturado:
            chofer = gasto[0]
            total_no_facturado = gasto[1]
            result_total['totalGastoNoFacturado'] = total_no_facturado

            if chofer not in result:
                result[chofer] = default_chofer.copy()

            result[chofer].update({'totalNoFacturado': total_no_facturado})

        for _, datos in result.items():
            total_perdida = datos['totalLiquidacion'] - (datos['totalFacturado'] + datos['totalNoFacturado'])
            if total_perdida < 0:
                result_total['totalPerdidas'] += abs(total_perdida)

        return jsonify({'choferes': result, 'totales': result_total}), 200

    except Exception as e:
        error_message = f"Error en GET Statistics {str(e)}"
        app.logger.warning(error_message)
        return jsonify({'error': error_message}), 500
