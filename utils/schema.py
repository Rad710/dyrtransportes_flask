from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import UniqueConstraint

db = SQLAlchemy()

#tablas de la base de datos
class Cobranzas(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    liquidacion_viajes = relationship("LiquidacionViajes", backref="liquidacion_viajes", cascade="all, delete-orphan")
    fecha_viaje = db.Column(db.Date, nullable=False)
    chofer = db.Column(db.String(100), nullable=False)
    chapa = db.Column(db.String(100))
    producto = db.Column(db.String(100))
    origen = db.Column(db.String(100))
    destino = db.Column(db.String(100))
    tiquet = db.Column(db.Integer, nullable=False)
    kilos_origen = db.Column(db.Integer, nullable=False)
    kilos_destino = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Numeric, nullable=False)
    fecha_creacion = db.Column(db.Date, nullable=True)

     # diferencia = kilos_destino - kilos_origen
    # tolerancia = redondear(Decimal(kilos_origen) * Decimal(0.002))
    # diferencia_de_tolerancia = diferencia + tolerancia
    # total = redondear(Decimal(precio) * Decimal(kilos_destino))

class Planillas(db.Model):
    fecha = db.Column(db.Date, nullable=False, primary_key=True)

tipo_clave = {'chofer/chapa', 'producto', 'origen', 'destino'} #tipos de palabras clave (a usar en tabla PalabraClave)
class Palabras(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    palabra = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(100), nullable=False)

    __table_args__ = (
        UniqueConstraint('palabra', 'tipo', name='uq_palabra_tipo'),
    )


class Precios(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    origen = db.Column(db.String(100), nullable=False)
    destino = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    precio_liquidacion = db.Column(db.Float, nullable=False)

    __table_args__ = (
        UniqueConstraint('origen', 'destino', name='uq_origen_destino'),
    )


class LiquidacionViajes(db.Model):
    id = db.Column(db.Integer,ForeignKey('cobranzas.id', ondelete='CASCADE'), primary_key=True)
    precio_liquidacion = db.Column(db.Numeric, nullable=False)
    fecha_liquidacion = db.Column(db.Date, nullable=False)


class LiquidacionGastos(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    chofer = db.Column(db.String(100), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    boleta = db.Column(db.String(100), nullable=True)
    importe = db.Column(db.BigInteger, nullable=False)
    fecha_liquidacion = db.Column(db.Date, nullable=False)
    razon = db.Column(db.String(100), nullable=True)


class Liquidaciones(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    chofer = db.Column(db.String(100), nullable=False)
    fecha_liquidacion = db.Column(db.Date, nullable=False)
    pagado = db.Column(db.Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint('chofer', 'fecha_liquidacion', name='uq_chofer_fecha'),
    )