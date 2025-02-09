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

# @app.route('/exportar_cobranza/<string:fecha_creacion>', methods=['GET'])
# def exportar_cobranza(fecha_creacion):
#     cobranzas_ordenadas = Cobranzas.query.filter_by(fecha_creacion=fecha_creacion).order_by(Cobranzas.producto, Cobranzas.origen, Cobranzas.destino, Cobranzas.chofer, Cobranzas.fecha_viaje).all()
#     # Crea un diccionario para almacenar las sumas de subtotales por grupo

#     subtotales_grupo = {}
#     default_grupo = {'origen': 0, 'destino': 0, 'diferencia': '', 'tolerancia': '', 'last_row': 0, 
#                      'diferencia_tolerancia': '', 'subtotal': '', 'ultima_entrada': '', 'producto': ''}

#     group_counter = 6
#     first_row = 0
#     for cobranza in cobranzas_ordenadas:
#         grupo = (cobranza.origen, cobranza.destino, cobranza.producto)

#         if grupo not in subtotales_grupo:
#             group_counter += 1
#             subtotales_grupo[grupo] = default_grupo.copy()
#             first_row = group_counter
#             subtotales_grupo[grupo]['producto'] = cobranza.producto

#         subtotales_grupo[grupo]['origen'] += cobranza.kilos_origen
#         subtotales_grupo[grupo]['destino'] += cobranza.kilos_destino
#         subtotales_grupo[grupo]['diferencia'] = f'=SUM(K{first_row}:K{group_counter})'
#         subtotales_grupo[grupo]['tolerancia'] = f'=SUM(L{first_row}:L{group_counter})'
#         subtotales_grupo[grupo]['diferencia_tolerancia'] = f'=SUM(M{first_row}:M{group_counter})'
#         subtotales_grupo[grupo]['subtotal'] = f'=SUM(O{first_row}:O{group_counter})'

#         subtotales_grupo[grupo]['ultima_entrada'] = cobranza.tiquet
#         subtotales_grupo[grupo]['last_row'] = group_counter

#         group_counter += 1

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

#     # Agregar la fecha como la primera fila
#     sheet.append([])  # Agregar una fila en blanco después de la fecha
#     # Agregar una fila en blanco después de la fecha
#     sheet.append(['D & R TRANSPORTES'])

#     # Obtener el rango de columnas con valores None
#     inicio_columna = 1  # Cambiar al índice de la primera columna con valor None
#     fin_columna = 15   # Cambiar al índice de la última columna con valor None

#     # Combinar las celdas en el rango de columnas
#     sheet.merge_cells(start_row=sheet.max_row, start_column=inicio_columna,
#                       end_row=sheet.max_row, end_column=fin_columna)

#     # Centrar el contenido en la celda combinada
#     merged_cell = sheet.cell(row=sheet.max_row, column=inicio_columna)
#     merged_cell.alignment = Alignment(horizontal='center', vertical='center')

#     # Aplicar el estilo de fuente deseado (Arial Black, size 22, purple color)
#     # Using a standard purple color index
#     font = Font(name='Arial Black', size=22, color="800080")
#     merged_cell.font = font

#     sheet.row_dimensions[2].height = 35

#     sheet.append([])  # Agregar una fila en blanco después de la fecha
#     sheet.append([None, datetime.now().strftime('%d/%m/%Y')])
#     sheet.append([])  # Agregar una fila en blanco después de la fecha

#     # Agregar encabezados
#     encabezados = ['N°', 'Fecha', 'Chofer', 'Chapa', 'Producto', 'Origen', 'Destino', 'Tiquet',
#                    'Kilos Origen', 'Kilos Destino', 'Dif.', 'Tolera', 'Dif. Tol.', 'Precio', 'Total']
#     sheet.append(encabezados)

#     # Aplicar bordes y relleno a las celdas del encabezado
#     for col_idx, _ in enumerate(encabezados, start=1):
#         col_letter = get_column_letter(col_idx)
#         cell = sheet[f'{col_letter}6']

#         # Aplicar bordes
#         thin_border = Border(left=Side(style='thin'), right=Side(
#             style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
#         cell.border = thin_border

#         # Aplicar relleno con el color Gold, Accent 4, Lighter 40%
#         fill = PatternFill(start_color="FFC000",
#                            end_color="FFC000", fill_type="solid")
#         cell.fill = fill

#     # Aplicar alineación vertical y horizontal en la celda
#         cell.alignment = Alignment(horizontal='left', vertical='bottom')

#     sheet.row_dimensions[6].height = 30

#     # Agregar filas de datos
#     index = 1
#     contador = 7
#     for cobranza in cobranzas_ordenadas:
#         fila = [index,
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

#         for col in range(1, 16):
#             cell = sheet.cell(row=sheet.max_row, column=col)
#             thin_border = Border(left=Side(style='thin'), right=Side(
#                 style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
#             cell.border = thin_border

#         grupo = (cobranza.origen, cobranza.destino, cobranza.producto)
#         if subtotales_grupo[grupo]['ultima_entrada'] == cobranza.tiquet:
#             contador += 1

#             sheet.append(['Subtotal', None, None, None, None, None, None, None,
#                           subtotales_grupo[grupo]['origen'],
#                           subtotales_grupo[grupo]['destino'],
#                           subtotales_grupo[grupo]['diferencia'],
#                           subtotales_grupo[grupo]['tolerancia'],
#                           subtotales_grupo[grupo]['diferencia_tolerancia'],
#                           None, subtotales_grupo[grupo]['subtotal']
#                           ])

#             # Obtener el rango de columnas con valores None
#             inicio_columna = 1  # Cambiar al índice de la primera columna con valor None
#             fin_columna = 8   # Cambiar al índice de la última columna con valor None

#             # Combinar las celdas en el rango de columnas
#             sheet.merge_cells(start_row=sheet.max_row, start_column=inicio_columna,
#                               end_row=sheet.max_row, end_column=fin_columna)

#             # Centrar el contenido en la celda combinada
#             merged_cell = sheet.cell(row=sheet.max_row, column=inicio_columna)
#             merged_cell.alignment = Alignment(
#                 horizontal='center', vertical='center')

#             # Formatear columnas 8 a 15 como números
#             for col in range(8, 16):
#                 cell = sheet.cell(row=sheet.max_row, column=col)

#                 if col == 14:
#                     cell.number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED2
#                 else:
#                     cell.number_format = "#,##0"

#             for col in range(1, 16):
#                 cell = sheet.cell(row=sheet.max_row, column=col)
#                 thin_border = Border(left=Side(style='thin'), right=Side(
#                     style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
#                 cell.border = thin_border

#                 # Aplicar relleno con el color Gray, Accent 4, Lighter 60%
#                 # Gray, Accent 4, Lighter 60%
#                 fill = PatternFill(start_color="969696",
#                                    end_color="969696", fill_type="solid")
#                 cell.fill = fill

#         contador += 1
#         index += 1

#     total = {'origen': '=', 'destino': '=', 'diferencia': '=', 'tolerancia': '=', 'diferencia_tolerancia': '=', 'total': '=', 'productos': {}}
#     last_row = None
#     for grupo, subtotal_agrupado in subtotales_grupo.items():
#         last_row = subtotal_agrupado["last_row"] + 1

#         total['origen'] += f'+I{last_row}'
#         total['destino'] += f'+J{last_row}'
#         total['diferencia'] += f'+K{last_row}'
#         total['tolerancia'] += f'+L{last_row}'
#         total['diferencia_tolerancia'] += f'+M{last_row}'
#         subtotal_row = f'+O{last_row}'
#         total['total'] += subtotal_row

#         producto = subtotal_agrupado['producto']
#         if producto not in total['productos']:
#             total['productos'][producto] = '='

#         total['productos'][producto] += subtotal_row


#     sheet.append(['TOTAL', None, None, None, None, None, None, None,
#                   total['origen'],
#                   total['destino'],
#                   total['diferencia'],
#                   total['tolerancia'],
#                   total['diferencia_tolerancia'],
#                   None, total['total']])

#     # Obtener el rango de columnas con valores None
#     inicio_columna = 1  # Cambiar al índice de la primera columna con valor None
#     fin_columna = 8   # Cambiar al índice de la última columna con valor None

#     # Combinar las celdas en el rango de columnas
#     sheet.merge_cells(start_row=sheet.max_row, start_column=inicio_columna,
#                       end_row=sheet.max_row, end_column=fin_columna)

#     # Centrar el contenido en la celda combinada
#     merged_cell = sheet.cell(row=sheet.max_row, column=inicio_columna)
#     merged_cell.alignment = Alignment(horizontal='center', vertical='center')

#     # Formatear columnas 8 a 15 como números
#     for col in range(8, 16):
#         cell = sheet.cell(row=sheet.max_row, column=col)

#         if col == 14:
#             cell.number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED2
#         else:
#             cell.number_format = "#,##0"

#     for col in range(1, 16):
#         cell = sheet.cell(row=sheet.max_row, column=col)
#         thin_border = Border(left=Side(style='thin'), right=Side(
#             style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
#         cell.border = thin_border

#         fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
#         cell.fill = fill

#     sheet.append([None, None, None, None, None, None, None, None,
#                 None,  None, None, None, None, None, f'=+O{last_row + 1}/11'])
#     cell = sheet.cell(row=sheet.max_row, column=15)
#     cell.number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED2

#     sheet.append([])
#     for producto, subtotal in total['productos'].items():
#         sheet.append([None, None, None, None, None, None, None, None,
#                 None,  None, None, None, None, producto, subtotal])
#         cell = sheet.cell(row=sheet.max_row, column=15)
#         cell.number_format = "#,##0"

#     # Guardar el archivo Excel en el flujo de salida
#     workbook.save(output)
#     output.seek(0)

#     # Crear la respuesta para el cliente con el archivo Excel
#     response = make_response(output.getvalue())
#     response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#     response.headers[
#         'Content-Disposition'] = f'attachment; filename=cobranza_{fecha_creacion}.xlsx'
#     logger.warning(f'Cobranza exportada {fecha_creacion}')

#     return response


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


# @app.route('/exportar_liquidacion/<string:chofer>/<string:fecha>', methods=['GET'])
# def exportar_liquidacion(chofer, fecha):
#     liq_id = Liquidaciones.query.filter_by(chofer=chofer, fecha_liquidacion=fecha).first().id

#     viajes = db_session.query(Cobranzas, LiquidacionViajes).join(
#         LiquidacionViajes,
#         Cobranzas.id == LiquidacionViajes.id
#     ).filter(
#         Cobranzas.chofer == chofer,
#         LiquidacionViajes.id_liquidacion == liq_id
#     ).order_by(Cobranzas.fecha_viaje).all()

#     gastos_sin_boleta = LiquidacionGastos.query.filter_by(
#         id_liquidacion = liq_id, boleta=None).all()
#     gastos_con_boleta = LiquidacionGastos.query.filter_by(
#         id_liquidacion = liq_id).filter(LiquidacionGastos.boleta.isnot(None)).all()

#     max_len = max(len(viajes), len(gastos_sin_boleta), len(gastos_con_boleta))

#     # Rellenar las listas para que tengan la misma longitud con None si es necesario
#     viajes += [None] * (max_len - len(viajes))
#     gastos_sin_boleta += [None] * (max_len - len(gastos_sin_boleta))
#     gastos_con_boleta += [None] * (max_len - len(gastos_con_boleta))

#     # Combinar las tres listas en una lista de tuplas usando zip
#     results = zip(viajes, gastos_sin_boleta, gastos_con_boleta)

#     # Crear un archivo Excel en memoria
#     output = io.BytesIO()
#     workbook = Workbook()
#     sheet = workbook.active

#     #define columns 
#     columns = {
#         "code": { "letter": "A", "number": 1 },
#         "shipment_date":  { "letter": "B", "number": 2 },
#         "product": { "letter": "C", "number": 3 },
#         "ticket_number": { "letter": "D", "number": 4 },
#         "origin": { "letter": "E", "number": 5 },
#         "destination": { "letter": "F", "number": 6 },
#         "origin_weight": { "letter": "G", "number": 7 },
#         "destination_weight": { "letter": "H", "number": 8 },
#         "difference": { "letter": "I", "number": 9 },
#         "price_weight": { "letter": "J", "number": 10 },
#         "shipment_amount": { "letter": "K", "number": 11 },
#         "untaxed_expense_date": { "letter": "L", "number": 12 },
#         "untaxed_espense_reason": { "letter": "M", "number": 13 },
#         "untaxed_expense_amount": { "letter": "N", "number": 14 },
#         "taxed_expense_date": { "letter": "O", "number": 15 },
#         "taxed_expense_receipt": { "letter": "P", "number": 16 },
#         "taxed_expense_reason": { "letter": "Q", "number": 17 },
#         "taxed_expense_amount": { "letter": "R", "number": 18 }
#     }

#     columns_length = len(columns)

#     # style
#     border = Border(left=Side(style='thin'), right=Side(
#         style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

#     render_driver_payroll_headers(sheet, columns, chofer, viajes, border)
#     render_driver_payroll_shipment_expense(sheet, columns, results, border)
#     last_row = 5 + max_len

#     untaxed_expense_amount_column = columns["untaxed_expense_amount"]["letter"]
#     taxed_expense_amount_column = columns["taxed_expense_amount"]["letter"]

#     #Subtotals
#     subtotal_sin_boleta = f'=SUM(${untaxed_expense_amount_column}6:${untaxed_expense_amount_column}{last_row})'
#     subtotal_con_boleta = f'=SUM(${taxed_expense_amount_column}6:${taxed_expense_amount_column}{last_row})'
#     subtotales = [
#         None, None, None, None, None, None, None, None, None, None, None,
#         'Subtotal', None, subtotal_sin_boleta, 'Subtotal', None, None, subtotal_con_boleta
#     ]
#     sheet.append(subtotales)

#     for col in range(1, columns_length + 1):
#         cell = sheet.cell(row=sheet.max_row, column=col)
#         cell.border = border
#         cell.font = Font(bold=True)

#     for col in [columns['untaxed_expense_date']['number'], columns_length]:
#         cell = sheet.cell(row=sheet.max_row, column=col)
#         cell.number_format = "#,##0"
#         cell.border = border


#     shipment_amount_column = columns["shipment_amount"]["letter"]
#     untaxed_expense_amount_column = columns["untaxed_expense_amount"]["letter"]
#     taxed_expense_amount_column = columns["taxed_expense_amount"]["letter"]

#     # TOTAL SHIPMENT-EXPENSE
#     total_gastos = f'=+${untaxed_expense_amount_column}{last_row + 1}+${taxed_expense_amount_column}{last_row + 1}'
#     subtotal_viajes = f'=SUM(${shipment_amount_column}6:${shipment_amount_column}{last_row})'
#     total = [
#         None, None, None, None, None, None, None, None, 'TOTAL FLETES:',
#         None, subtotal_viajes, 'TOTAL GASTOS:', None, None, None, None, None, total_gastos
#     ]
#     sheet.append(total)

#     for col in [columns['shipment_amount']['number'], len(columns)]:
#         cell = sheet.cell(row=sheet.max_row, column=col)
#         cell.number_format = "#,##0"
#         cell.border = border

#     for col in range(1, len(columns) + 1):
#         cell = sheet.cell(row=sheet.max_row, column=col)
#         cell.border = border
#         cell.font = Font(bold=True)

#     sheet.append([None])

#     render_driver_payroll_totals(sheet, columns, border, last_row)

#     # Save and send Excel file
#     workbook.save(output)
#     output.seek(0)
#     response = make_response(output.getvalue())
#     response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#     response.headers['Content-Disposition'] = f'attachment; filename={chofer}_Liquidacion_{fecha}.xlsx'
#     logger.warning('Liquidacion %s %s exportada', chofer, fecha)
#     return response


# def render_driver_payroll_headers(sheet, columns, chofer, viajes, border) :
#     #set column widths
#     sheet.column_dimensions[columns['code']['letter']].width = 2.64
#     sheet.column_dimensions[columns['shipment_date']['letter']].width = 10.6
#     sheet.column_dimensions[columns['product']['letter']].width = 5.00
#     sheet.column_dimensions[columns['ticket_number']['letter']].width = 9.00
#     sheet.column_dimensions[columns['origin']['letter']].width = 16
#     sheet.column_dimensions[columns['destination']['letter']].width = 16
#     sheet.column_dimensions[columns['origin_weight']['letter']].width = 9
#     sheet.column_dimensions[columns['destination_weight']['letter']].width = 9
#     sheet.column_dimensions[columns['difference']['letter']].width = 5
#     sheet.column_dimensions[columns['price_weight']['letter']].width = 7.60
#     sheet.column_dimensions[columns['shipment_amount']['letter']].width = 10.27
#     sheet.column_dimensions[columns['untaxed_expense_date']['letter']].width = 10.82
#     sheet.column_dimensions[columns['untaxed_espense_reason']['letter']].width = 7.0
#     sheet.column_dimensions[columns['untaxed_expense_amount']['letter']].width = 10.27
#     sheet.column_dimensions[columns['taxed_expense_date']['letter']].width = 10.82
#     sheet.column_dimensions[columns['taxed_expense_receipt']['letter']].width = 8.5
#     sheet.column_dimensions[columns['taxed_expense_reason']['letter']].width = 7.0
#     sheet.column_dimensions[columns['taxed_expense_amount']['letter']].width = 10.82

#     # Title
#     sheet.append([])
#     sheet.append(['LIQUIDACION DE FLETES'])

#     sheet.merge_cells(
#         start_row=sheet.max_row, start_column=1,
#         end_row=sheet.max_row, end_column=len(columns)
#     )
#     merged_cell = sheet.cell(row=sheet.max_row, column=1)
#     merged_cell.alignment = Alignment(horizontal='center', vertical='center')


#     for col in range(1, len(columns) + 1):
#         cell = sheet.cell(row=sheet.max_row, column=col)
#         cell.border = border
#         cell.font = Font(bold=True)

#     sheet.row_dimensions[2].height = 21

#     chapa = ""
#     if viajes and viajes[0]:
#         chapa = viajes[0][0].chapa

#     # Driver Information
#     sheet.append(
#         [f'Conductor: {chofer}                Chapa: {chapa}                Fecha: {datetime.now().strftime("%d/%m/%Y")}']
#     )
#     sheet.merge_cells(
#         start_row=sheet.max_row, start_column=1,
#         end_row=sheet.max_row, end_column=len(columns)
#     )
#     merged_cell = sheet.cell(row=sheet.max_row, column=1)
#     merged_cell.alignment = Alignment(horizontal='center', vertical='center')


#     for col in range(1, len(columns) + 1):
#         cell = sheet.cell(row=sheet.max_row, column=col)
#         cell.border = border
#         cell.font = Font(bold=True)

#     sheet.row_dimensions[3].height = 21

#     # Columns division
#     sheet.append([
#         'FLETES', None, None, None, None, None, None, None, None, None, None,
#         'GASTOS (VIATICO/GASOIL)', None, None, None, None
#     ])
    
#     # Merge FLETES title
#     sheet.merge_cells(
#         start_row=sheet.max_row, start_column=1,
#         end_row=sheet.max_row, end_column=columns['shipment_amount']['number']
#     )
#     merged_cell = sheet.cell(row=sheet.max_row, column=1)
#     merged_cell.alignment = Alignment(horizontal='center', vertical='center')

#     for col in range(1, len(columns) + 1):
#         cell = sheet.cell(row=sheet.max_row, column=col)
#         cell.border = border
#         cell.font = Font(bold=True)


#     # Merge GASTOS title
#     sheet.merge_cells(
#         start_row=sheet.max_row,
#         start_column=columns['untaxed_expense_date']['number'],
#         end_row=sheet.max_row, end_column=len(columns)
#     )
#     merged_cell = sheet.cell(
#         row=sheet.max_row, column=columns['untaxed_expense_date']['number']
#     )
#     merged_cell.alignment = Alignment(horizontal='center', vertical='center')


#     for col in range(1, len(columns) + 1):
#         cell = sheet.cell(row=sheet.max_row, column=col)
#         cell.border = border
#         cell.font = Font(bold=True)


#     # Table Header
#     headers = [
#         'N°', 'Fecha', 'Prod.', 'Recepcion N°', 
#         'Origen', 'Destino', 'Kg. Origen', 'Kg. Llegada',
#         'Dif.', 'Gs. p/ Kg', 'Importe Gs.', 
#         'Fecha', 'Razón', 'Importe Gs.', 
#         'Fecha', 'Boleta N°', 'Razón', 'Importe Gs.'
#     ]

#     sheet.append(headers)
#     for col in range(1, len(columns) + 1):
#         cell = sheet.cell(row=sheet.max_row, column=col)
#         cell.border = border
#         cell.font = Font(bold=True)

#     sheet.row_dimensions[5].height = 25


# def render_driver_payroll_shipment_expense(sheet, columns, results, border):
#     origin_weight_column = columns["origin_weight"]["letter"]
#     destination_weight_column = columns["destination_weight"]["letter"]
#     price_weight_column = columns["price_weight"]["letter"]

#     contador = 1
#     for viaje, sin_boleta, con_boleta in results:
#         fila = [contador]

#         if viaje:
#             current_row = contador + 5
#             diferencia = f'=+${destination_weight_column}{current_row}-${origin_weight_column}{current_row}'
#             total_gs = f'=ROUND(${destination_weight_column}{current_row}*${price_weight_column}{current_row}, 0)'

#             viaje_fila = [
#                 viaje[0].fecha_viaje.strftime('%d/%m/%Y'), viaje[0].producto,
#                 viaje[0].tiquet, viaje[0].origen, viaje[0].destino,
#                 viaje[0].kilos_origen, viaje[0].kilos_destino,
#                 diferencia,
#                 viaje[1].precio_liquidacion,
#                 total_gs
#             ]
            
#             fila.extend(viaje_fila)

#         else:
#             fila.extend([None] * 10)

#         if sin_boleta:
#             sin_boleta_fila = [sin_boleta.fecha.strftime(
#                 '%d/%m/%Y'), sin_boleta.razon, sin_boleta.importe]
#             fila.extend(sin_boleta_fila)
#         else:
#             fila.extend([None] * 3)

#         if con_boleta:
#             con_boleta_fila = [con_boleta.fecha.strftime(
#                 '%d/%m/%Y'), con_boleta.boleta, con_boleta.razon, con_boleta.importe]
#             fila.extend(con_boleta_fila)
#         else:
#             fila.extend([None] * 4)

#         sheet.append(fila)

#         for col in range(1, len(columns) + 1):
#             cell = sheet.cell(row=sheet.max_row, column=col)
#             cell.border = border

#             if col == columns['price_weight']['number']:
#                 cell.number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED2
#             else:
#                 cell.number_format = "#,##0"

#         contador += 1


# def render_driver_payroll_totals(sheet, columns, border, last_row):
#     price_weight_column = columns["price_weight"]["letter"]
#     shipment_amount_column = columns["shipment_amount"]["letter"]
#     taxed_expense_amount_column = columns["taxed_expense_amount"]["letter"]

#     totals_start_column = 7
#     totals_end_column = 12
#     title_end_column = 9

#     # PAYROLL TOTAL
#     total_cobrar = [
#         None, None, None, None, None, None,
#         'TOTAL A COBRAR:', None, None,
#         f'=+${shipment_amount_column}{last_row + 2}-${taxed_expense_amount_column}{last_row + 2}',
#         None
#     ]
#     sheet.append(total_cobrar)
#     sheet.merge_cells(
#         start_row=sheet.max_row,
#         start_column=title_end_column + 1,
#         end_row=sheet.max_row,
#         end_column=title_end_column + 2
#     )
#     sheet.merge_cells(
#         start_row=sheet.max_row,
#         start_column=totals_start_column,
#         end_row=sheet.max_row,
#         end_column=title_end_column
#     )

#     for col in range(columns['origin_weight']['number'], columns['shipment_amount']['number']):
#         cell = sheet.cell(row=sheet.max_row, column=col)
#         cell.border = border
#         cell.font = Font(bold=True)

#         if col == columns['shipment_amount']['number']:
#             cell.number_format = "#,##0"


#     total_facturar = [
#         None, None, None, None, None, None,
#         'TOTAL A FACTURAR:', None, None, 
#         f'=+${shipment_amount_column}{last_row + 2}-${taxed_expense_amount_column}{last_row + 1}',
#         None
#     ]
#     sheet.append(total_facturar)
#     sheet.merge_cells(
#         start_row=sheet.max_row,
#         start_column=title_end_column + 1,
#         end_row=sheet.max_row, end_column=title_end_column + 2
#     )
#     sheet.merge_cells(
#         start_row=sheet.max_row,
#         start_column=totals_start_column,
#         end_row=sheet.max_row,
#         end_column=title_end_column
#     )

#     for col in range(columns['origin_weight']['number'], columns['shipment_amount']['number']):
#         cell = sheet.cell(row=sheet.max_row, column=col)
#         cell.border = border
#         cell.font = Font(bold=True)

#         if col == columns['shipment_amount']['number']:
#             cell.number_format = "#,##0"

#     sheet.append([
#         None, None, None, None, None, None,
#         'Facturar a nombre de CARMELO MEDINA. Ruc: 850.299-4', 
#         None, None, None, None
#     ])

#     sheet.merge_cells(
#         start_row=sheet.max_row, start_column=totals_start_column,
#         end_row=sheet.max_row, end_column=totals_end_column
#     )

#     for col in range(totals_start_column, totals_end_column + 1):
#         cell = sheet.cell(row=sheet.max_row, column=col)
#         cell.border = border


#     sheet.append([])
#     sheet.append([
#         None, None, None, None, None, None,
#         'Descripcion', None, None, 'Exenta', 'IVA 5%', 'IVA 10%', None
#     ])
    
#     sheet.merge_cells(
#         start_row=sheet.max_row, start_column=totals_start_column,
#         end_row=sheet.max_row, end_column=title_end_column
#     )

#     for col in range(totals_start_column, totals_end_column + 1):
#         cell = sheet.cell(row=sheet.max_row, column=col)
#         cell.border = border

    
#     sheet.append([
#         None, None, None, None, None, None,
#         'Servicio de Flete', None, None, 0, 0, f'=+${price_weight_column}{last_row + 5}', None
#     ])
    
#     sheet.merge_cells(
#         start_row=sheet.max_row, start_column=totals_start_column,
#         end_row=sheet.max_row, end_column=title_end_column
#     )

#     for col in range(totals_start_column, totals_end_column + 1):
#         cell = sheet.cell(row=sheet.max_row, column=col)
#         cell.border = border

#         if col >= title_end_column:
#             cell.number_format = "#,##0"

#     sheet.append([
#         None, None, None, None, None, None, None,
#         None, None, None, None
#     ])
    
#     sheet.merge_cells(start_row=sheet.max_row, start_column=totals_start_column,
#                 end_row=sheet.max_row, end_column=title_end_column)

#     for col in range(totals_start_column, totals_end_column + 1):
#         cell = sheet.cell(row=sheet.max_row, column=col)
#         cell.border = border

#         if col >= title_end_column:
#             cell.number_format = "#,##0"


#     sheet.append([
#         None, None, None, None, None, None,
#         'Subtotal', None, None, f'=+J{last_row + 9}', 0, f'=+L{last_row + 9}', None
#     ])
    
#     sheet.merge_cells(
#         start_row=sheet.max_row, start_column=totals_start_column,
#         end_row=sheet.max_row, end_column=title_end_column
#     )
    
#     for col in range(totals_start_column, totals_end_column + 1):
#         cell = sheet.cell(row=sheet.max_row, column=col)
#         cell.border = border

#         if col >= title_end_column:
#             cell.number_format = "#,##0"


#     sheet.append([
#         None, None, None, None, None, None,
#         'Total', None, None, None, None, f'=+J{last_row + 11}+L{last_row + 11}', None
#     ])
    
#     sheet.merge_cells(
#         start_row=sheet.max_row, start_column=totals_start_column,
#         end_row=sheet.max_row, end_column=title_end_column
#     )
#     for col in range(totals_start_column, totals_end_column + 1):
#         cell = sheet.cell(row=sheet.max_row, column=col)
#         cell.border = border
#         cell.font = Font(bold=True)

#         if col >= title_end_column:
#             cell.number_format = "#,##0"

#     sheet.append([
#         None, None, None, None, None, None, None,
#         None, None, 'IVA 10%', None, f'=+L{last_row + 12}/11', None
#     ])
    
#     sheet.merge_cells(start_row=sheet.max_row, start_column=totals_start_column,
#                 end_row=sheet.max_row, end_column=title_end_column)

#     for col in range(totals_start_column, totals_end_column + 1):
#         cell = sheet.cell(row=sheet.max_row, column=col)
#         cell.border = border
#         cell.font = Font(bold=True)

#         if col >= title_end_column:
#             cell.number_format = "#,##0"
    

