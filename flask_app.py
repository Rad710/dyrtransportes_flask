from flask import send_file

import subprocess

from app_database import app, user, password, host, db_name
import utils.planillas as planillas
import utils.cobranzas as cobranzas
import utils.keywords as nomina
import utils.precio as precio
import utils.liquidacion as liquidacion
import utils.liquidacion_viajes as liquidacion_viajes
import utils.liquidacion_gastos as liquidacion_gastos
import utils.export as export
import utils.statistics as statistics
import utils.dinatran as dinatran


@app.route('/')
def index():
    return "Hello, World!"

app.route('/planillas/', methods=['POST'])(planillas.post_planilla)

app.route('/planillas/', methods=['GET'])(planillas.get_planillas)

app.route('/planillas/<fecha>', methods=['DELETE'])(planillas.delete_planilla)

app.route('/planillas/<year>', methods=['GET'])(planillas.get_planilla)

app.route('/exportar_informe/<string:fecha_inicio>/<string:fecha_fin>', methods=['GET'])(export.exportar_informe)

app.route('/cobranzas/', methods=['POST'])(cobranzas.post_cobranza)

app.route('/cobranzas/<string:fecha_creacion>', methods=['GET'])(cobranzas.get_cobranza)

app.route('/cobranzas/<string:id>', methods=['PUT'])(cobranzas.put_cobranza)

app.route('/cobranza/<string:id>', methods=['DELETE'])(cobranzas.delete_cobranza)

app.route('/exportar_cobranza/<string:fecha_creacion>', methods=['GET'])(export.exportar_cobranza)

app.route('/keywords/', methods=['GET'])(nomina.get_keywords)

app.route('/precios/', methods=['POST'])(precio.post_precio)

app.route('/precios/', methods=['GET'])(precio.get_precios)

app.route('/precios/<string:origen_destino>', methods=['GET'])(precio.get_precio)

app.route('/precios/<string:id>', methods=['PUT'])(precio.put_precio)

app.route('/precios/<string:id>', methods=['DELETE'])(precio.delete_precio)

app.route('/exportar_precios', methods=['GET'])(export.exportar_precios)

app.route('/nomina/', methods=['GET'])(nomina.get_nomina)

app.route('/nomina/<string:id>', methods=['DELETE'])(nomina.delete_nomina)

app.route('/liquidacion', methods=['POST'])(liquidacion.post_liquidacion)

app.route('/liquidacion/<string:chofer>/<string:fecha>', methods=['GET'])(liquidacion.get_liquidacion)

app.route('/liquidacion/<string:id>', methods=['PUT'])(liquidacion.put_liquidacion)

app.route('/liquidaciones', methods=['GET'])(liquidacion.get_liquidaciones)

app.route('/liquidaciones/<string:chofer>', methods=['GET'])(liquidacion.get_liquidaciones_chofer)

app.route('/liquidaciones/<string:chofer>', methods=['DELETE'])(liquidacion.delete_liquidaciones)

app.route('/liquidaciones/<string:chofer>/<string:fecha>', methods=['DELETE'])(liquidacion.delete_liquidaciones_chofer)

app.route('/liquidacion_viaje', methods=['POST'])(liquidacion_viajes.post_liquidacion_viaje)

app.route('/liquidacion_viajes/<string:chofer>/<string:fecha>', methods=['GET'])(liquidacion_viajes.get_liquidacion_viajes)

app.route('/liquidacion_viajes/<string:id>', methods=['PUT'])(liquidacion_viajes.put_liquidacion_viaje)

app.route('/liquidacion_viaje/<string:id>', methods=['DELETE'])(liquidacion_viajes.delete_liquidacion_viaje)

app.route('/liquidacion_gasto', methods=['POST'])(liquidacion_gastos.post_liquidacion_gasto)

app.route('/liquidacion_gastos/<string:chofer>/<string:fecha>', methods=['GET'])(liquidacion_gastos.get_liquidacion_gastos)

app.route('/liquidacion_gasto/<string:id>', methods=['PUT'])(liquidacion_gastos.put_liquidacion_gasto)

app.route('/liquidacion_gasto/<string:id>', methods=['DELETE'])(liquidacion_gastos.delete_liquidacion_gasto)

app.route('/exportar_liquidacion/<string:chofer>/<string:fecha>', methods=['GET'])(export.exportar_liquidacion)

app.route('/statistics/<string:fecha_inicio>/<string:fecha_fin>', methods=['GET'])(statistics.get_statistics)

app.route('/dinatran/<string:fecha_inicio>/<string:fecha_fin>', methods=['GET'])(dinatran.get_informe_dinatran)


# Route to return a copy of the database file
@app.route('/database_backup', methods=['GET'])
def database_backup():
    try:
        dump_file = 'dump_filename.sql'

        # Use mysqldump to create a SQL dump of your MySQL database
        subprocess.run(["mysqldump", "-u", user, "-p" + password, "-h", host, "--set-gtid-purged=OFF", "--no-tablespaces", db_name, "--result-file=" + dump_file])
        # Open the dump file for reading and send it as an attachment
        return send_file(f'../{dump_file}', as_attachment=True)

    except Exception as e:
        return str(e), 500



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)