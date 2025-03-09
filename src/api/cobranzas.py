# def crear_cobranza_liquidacion(cobranza):
#     print(f'Cobranza: {cobranza}')
#     fecha_viaje = parser.isoparse(re.sub(r'\s+', ' ', str(cobranza['fechaViaje']).strip())).date()
#     chofer = re.sub(r'\s+', ' ', str(cobranza['chofer'])).strip()
#     chapa = re.sub(r'\s+', ' ', str(cobranza['chapa'])).strip()
#     producto = re.sub(r'\s+', ' ', str(cobranza['producto'])).strip()
#     origen = re.sub(r'\s+', ' ', str(cobranza['origen'])).strip()
#     destino = re.sub(r'\s+', ' ', str(cobranza['destino'])).strip()
#     tiquet = string_to_int(re.sub(r'\s+', ' ', str(cobranza['tiquet'])).strip())
#     kilos_origen = string_to_int(re.sub(r'\s+', ' ', str(cobranza['kgOrigen'])).strip())
#     kilos_destino = string_to_int(re.sub(r'\s+', ' ', str(cobranza['kgDestino'])).strip())
#     precio = re.sub(r'\s+', ' ', str(cobranza['precio'])).strip()
#     precio_liquidacion = re.sub(r'\s+', ' ', str(cobranza['precioLiquidacion'])).strip()
#     fecha_creacion = parser.isoparse(re.sub(r'\s+', ' ', str(cobranza['fechaCreacion'])).strip()).date()

#     try:
#         id_cobranza = agregar_cobranza(fecha_viaje, chofer, chapa, producto, origen, destino,
#                         tiquet, kilos_origen, kilos_destino, precio, fecha_creacion)
#     except IntegrityError as e:
#         error_message = f"Entrada duplicada {str(e)}"
#         logger.warning(error_message)
#         return jsonify({"error": error_message}), 500
#     except Exception as e:
#         error_message = f"Error al agregar entrada a la tabla Cobranzas {str(e)}"
#         logger.warning(error_message)
#         return jsonify({"error": error_message}), 500

#     try:
#         fecha_liquidacion = agregar_liquidacion(chofer)
#     except Exception as e:
#         error_message = f"Error al agregar nueva liquidacion {str(e)}"
#         logger.warning(error_message)
#         return jsonify({"error": error_message}), 500

#     try:
#         agregar_liquidacion_viaje(id_cobranza, precio_liquidacion, fecha_liquidacion, chofer)
#     except Exception as e:
#         error_message = f"Error al agregar a liquidacion del chofer {str(e)}"
#         logger.warning(error_message)
#         return jsonify({"error": error_message}), 500

#     return jsonify({"success": "Entrada agregada exitosamente a la tabla Cobranzas"}), 200
