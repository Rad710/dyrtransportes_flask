# from flask import make_response

# from datetime import datetime
# from dateutil import parser

# import io
# from openpyxl import Workbook
# from openpyxl.styles import Alignment, numbers, Border, Side, Font, PatternFill
# from openpyxl.utils import get_column_letter

# from app_config import logger
# from backend_flask.src.models.old_schema import Cobranzas, Precios, LiquidacionViajes, LiquidacionGastos, Liquidaciones

# from app_config import db_session

# from app_config import app

# from typing import Dict, List


# @app.route('/exportar_informe/<string:fecha_inicio>/<string:fecha_fin>', methods=['GET'])
# def exportar_informe_planillas(fecha_inicio, fecha_fin):
#     fecha_inicio_parsed = parser.isoparse(fecha_inicio).date()
#     fecha_fin_parsed = parser.isoparse(fecha_fin).date()

#     # Query the database for records within the date range
#     cobranzas = Cobranzas.query.filter(Cobranzas.fecha_creacion.between(
#         fecha_inicio_parsed, fecha_fin_parsed)).all()

#     # Ordena las cobranzas por las columnas 'origen' y 'destino'
#     cobranzas_ordenadas = sorted(
#         cobranzas, key=lambda cobranza: cobranza.chapa)

#     # Crear un archivo Excel en memoria
#     output = io.BytesIO()
#     workbook = Workbook()
#     sheet = workbook.active

#     sheet.column_dimensions['A'].width = 2.64
#     sheet.column_dimensions['B'].width = 11.00
#     sheet.column_dimensions['C'].width = 20.55
#     sheet.column_dimensions['D'].width = 9.09
#     sheet.column_dimensions['E'].width = 11.82
#     sheet.column_dimensions['F'].width = 18.64
#     sheet.column_dimensions['G'].width = 17.64
#     sheet.column_dimensions['H'].width = 9.91
#     sheet.column_dimensions['I'].width = 10.91
#     sheet.column_dimensions['J'].width = 11.09
#     sheet.column_dimensions['K'].width = 7.18
#     sheet.column_dimensions['L'].width = 6.27
#     sheet.column_dimensions['M'].width = 6.36
#     sheet.column_dimensions['N'].width = 6.27
#     sheet.column_dimensions['O'].width = 14.64

#     # Agregar encabezados
#     encabezados = ['N°', 'Fecha', 'Chofer', 'Chapa', 'Producto', 'Origen', 'Destino', 'Tiquet',
#                    'Kilos Origen', 'Kilos Destino', 'Dif.', 'Tolera', 'Dif. Tol.', 'Precio', 'Total']
#     sheet.append(encabezados)

#     # Congelar la fila del encabezado
#     sheet.freeze_panes = 'A2'

#     # Agregar filas de datos
#     contador = 2
#     for cobranza in cobranzas_ordenadas:
#         fila = [contador - 1,
#                 cobranza.fecha_viaje.strftime('%d/%m/%Y'),
#                 cobranza.chofer,
#                 cobranza.chapa,
#                 cobranza.producto,
#                 cobranza.origen,
#                 cobranza.destino,
#                 cobranza.tiquet,
#                 cobranza.kilos_origen,
#                 cobranza.kilos_destino,
#                 f'=+J{contador}-I{contador}',
#                 f'=ROUND(J{contador}*0.002, 0)',
#                 f'=+L{contador}+K{contador}',
#                 cobranza.precio,
#                 f'=ROUND(J{contador}*N{contador}, 0)']

#         sheet.append(fila)

#         for col in range(8, 16):
#             cell = sheet.cell(row=sheet.max_row, column=col)

#             if col == 14:
#                 cell.number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED2
#             else:
#                 cell.number_format = "#,##0"

#         contador += 1

#     # Guardar el archivo Excel en el flujo de salida
#     workbook.save(output)
#     output.seek(0)

#     # Crear la respuesta para el cliente con el archivo Excel
#     response = make_response(output.getvalue())
#     response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#     response.headers[
#         'Content-Disposition'] = f'attachment; filename=informe_{fecha_inicio}-{fecha_fin}.xlsx'
#     logger.warning(f'Informe exportado: {fecha_inicio}-{fecha_fin}')

#     return response
