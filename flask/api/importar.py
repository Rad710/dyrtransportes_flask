from flask import request, jsonify, send_file
import pandas as pd
import datetime

from app_database import logger
from utils.cobranzas import crear_cobranza_liquidacion
from utils.planillas import agregar_planilla


def importar_cobranza():
    if 'file' not in request.files:
        return jsonify({"error": "Error, archivo no enviado"}), 400

    file = request.files['file']
    fecha_creacion = request.form['fechaCreacion']

    if file.filename == '' or not file:
        return jsonify({"error": "Error, no se seleccionó un archivo"}), 400

    try:
        response = agregar_planilla(fecha_creacion)[0].get_json()

        if "error" in response:
            raise Exception(
                f"Error en post table planillas importadas. Planilla no pudo ser creada. {response['error']}")
    
        df = pd.read_excel(file, header=None)
        df = df.iloc[:, :15]

        header = ["N", "FECHA", "CHOFER", "CHAPA", "PRODUCTO", "ORIGEN", "DESTINO",
                  "Tiquet N", "KILOS ORIGEN", "KILOS DESTINO", "DIF", "Tolera",
                  "Dif + Tolerancia", "PRECIO", "TOTAL"]
        df.columns = header

        columns_to_keep = ["FECHA", "CHOFER", "CHAPA", "PRODUCTO", "ORIGEN", "DESTINO",
                           "Tiquet N", "KILOS ORIGEN", "KILOS DESTINO", "PRECIO"]
        df = df.loc[:, columns_to_keep]

        df.dropna(inplace=True)
        df = df[~df['CHOFER'].str.lower().str.contains('chofer')]
        df.reset_index(drop=True, inplace=True)
        df['FECHA CREACION'] = fecha_creacion
        df["Tiquet N"] = df["Tiquet N"].astype(str)
        df["KILOS ORIGEN"] = df["KILOS ORIGEN"].astype(str)
        df["KILOS DESTINO"] = df["KILOS DESTINO"].astype(str)

        df.apply(process_row, axis=1)

        logger.warning("File processed successfully")
        return jsonify({"success": "File processed successfully"}), 200
    except Exception as e:
        error_message = f"Error procesando el archivo {str(e)}"
        logger.warning(error_message)
        return jsonify({"error": error_message}), 500


def process_row(row):
    fecha_viaje = (
        datetime.datetime.strptime(row['FECHA'], "%d/%m/%Y")
        if isinstance(row['FECHA'], str)
        else row['FECHA']
    ).strftime("%Y-%m-%d")
    print(fecha_viaje)
    print(row['FECHA CREACION'])
    cobranza = {
        "fechaViaje": fecha_viaje,
        "chofer": row['CHOFER'],
        "chapa": row['CHAPA'],
        "producto": row['PRODUCTO'],
        "origen": row['ORIGEN'],
        "destino": row['DESTINO'],
        "tiquet": row['Tiquet N'],
        "kgOrigen": row['KILOS ORIGEN'],
        "kgDestino": row['KILOS DESTINO'],
        "precio": row['PRECIO'],
        "fechaCreacion": row['FECHA CREACION']
    }

    response = crear_cobranza_liquidacion(cobranza)[0].get_json()

    if "error" in response:
        raise Exception(
            f"Error en post table cobranzas importadas. Planilla cargada parcialmente. {response['error']}")

def exportar_formato_cobranza():
    return send_file('files/planilla_formato.xlsx', as_attachment=True, download_name='planilla_formato.xlsx')