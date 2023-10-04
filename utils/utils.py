from flask import jsonify
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_

from decimal import localcontext, Decimal, ROUND_HALF_UP
from datetime import datetime

from app_database import app
from utils.schema import db, Cobranzas, LiquidacionViajes, Precios, Palabras, tipo_clave, Liquidaciones


def redondear(numero):
    with localcontext() as ctx:
        ctx.rounding = ROUND_HALF_UP
        n = Decimal(numero)
        return int(n.to_integral_value())


def agregar_cobranza(fecha_viaje, chofer, chapa, producto, origen, destino, 
                  tiquet, kilos_origen, kilos_destino, precio, fecha_creacion):
    
    agregar_keywords(chofer, chapa, producto, origen, destino)
    agregar_precio(origen, destino, precio, 0)

    new_cobranza = Cobranzas(
        fecha_viaje=fecha_viaje,
        chofer=chofer,
        chapa=chapa,
        producto=producto,
        origen=origen,
        destino=destino,
        tiquet=tiquet,
        kilos_origen=kilos_origen,
        kilos_destino=kilos_destino,
        precio=precio,
        fecha_creacion=fecha_creacion
    )

    try:
        db.session.add(new_cobranza)
        db.session.commit()
        app.logger.warning('Cobranza agregada exitosamente')
        return new_cobranza.id

    except IntegrityError as e:
        db.session.rollback()
        app.logger.warning('Error al agregar cobranza')
        raise e



def agregar_liquidacion_viaje(id_cobranza, precio_liquidacion, fecha_liquidacion):
    liq = LiquidacionViajes(id=id_cobranza, precio_liquidacion=precio_liquidacion, fecha_liquidacion=fecha_liquidacion)

    try:
        db.session.add(liq)
        db.session.commit()
        app.logger.warning("Nueva entrada en lista de liquidaciones agregada")
    except IntegrityError as e:
        db.session.rollback()
        app.logger.warning("No se pudo cargar nueva entrada en lista de liquidaciones")
        raise e



def agregar_precio(origen, destino, precio, precio_liquidacion):
    existing_entry = Precios.query.filter_by(origen=origen, destino=destino).first()
    if existing_entry is None:
        # nueva entrada
        new_precio = Precios(origen=origen, destino=destino, precio=precio, precio_liquidacion=precio_liquidacion)

        try:
            db.session.add(new_precio)
            db.session.commit()
            app.logger.warning("Nuevo precio en lista de precios")
            return jsonify({"message": "Entrada agregada exitosamente a la tabla Precios"}), 200
        
        except IntegrityError:
            db.session.rollback()
            app.logger.warning("No se pudo cargar nuevo precio el lista de precios")
            return jsonify({"error": "Error al agregar a tabla Precios"}), 500
        
    return jsonify({"error": "Entrada ya existe en la tabla Precios"}), 500


def agregar_keywords(chofer, chapa, producto, origen, destino):
    palabras_clave = {'chofer/chapa': f'{chofer}/{chapa}',
                      'producto': producto, 'origen': origen, 'destino': destino}
    for tipo in tipo_clave:
        # revisar si entrada en la table de palabras claves ya existe
        existing_entry = Palabras.query.filter_by(
            palabra=palabras_clave[tipo], tipo=tipo).first()
        if existing_entry is None:
            # nueva entrada
            new_clave = Palabras(palabra=palabras_clave[tipo], tipo=tipo)

            try:
                db.session.add(new_clave)
                db.session.commit()
                app.logger.warning(f'Nueva entrada en palabras clave de tipo: {tipo}')
            except IntegrityError:
                db.session.rollback()
                app.logger.warning( f'No se pudo cargar nueva palabras clave de tipo: {tipo}')


def agregar_liquidacion(chofer):
    existing_entries = Liquidaciones.query.filter(
        and_(
            Liquidaciones.chofer == chofer,
            Liquidaciones.pagado != True  # Exclude entries where pagado is True
        )
    ).all()
    if not existing_entries:
        # nueva entrada
        new_liquidacion = Liquidaciones(
            chofer=chofer, fecha_liquidacion=datetime.now())
        try:
            db.session.add(new_liquidacion)
            db.session.commit()
            app.logger.warning("Nueva fecha de liquidacion agregada")

            return new_liquidacion.fecha_liquidacion

        except IntegrityError as e:
            db.session.rollback()
            app.logger.warning("No se pudo cargar nueva fecha de liquidacion")
            raise e
    else:
        app.logger.warning('Entrada ya exite en tabla Liquidaciones')
        liquidaciones_ordenadas = sorted(
            existing_entries, key=lambda liq: liq.fecha_liquidacion, reverse=True)
        return liquidaciones_ordenadas[0].fecha_liquidacion

