from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import UniqueConstraint

db = SQLAlchemy()

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
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_creacion = db.Column(db.Date, ForeignKey('planillas.fecha', ondelete='CASCADE'), nullable=True)

    __table_args__ = (
        UniqueConstraint('chofer', 'tiquet', 'fecha_viaje', name='uq_chofer_tiquet_fecha'),
    )

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
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    precio_liquidacion = db.Column(db.Numeric(10, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint('origen', 'destino', name='uq_origen_destino'),
    )


class LiquidacionViajes(db.Model):
    id = db.Column(db.Integer,ForeignKey('cobranzas.id', ondelete='CASCADE'), primary_key=True)
    precio_liquidacion = db.Column(db.Numeric(10, 2), nullable=False)

    id_liquidacion = db.Column(db.Integer,ForeignKey('liquidaciones.id', ondelete='CASCADE'), nullable=False)



class LiquidacionGastos(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    fecha = db.Column(db.Date, nullable=False)
    boleta = db.Column(db.String(100), nullable=True)
    importe = db.Column(db.BigInteger, nullable=False)
    razon = db.Column(db.String(100), nullable=True)

    id_liquidacion = db.Column(db.Integer,ForeignKey('liquidaciones.id', ondelete='CASCADE'), nullable=False)


class Liquidaciones(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    chofer = db.Column(db.String(100), nullable=False)
    fecha_liquidacion = db.Column(db.Date, nullable=False)
    pagado = db.Column(db.Boolean, default=False, nullable=False)

    liquidacion_viajes_id = relationship("LiquidacionViajes", backref="liquidacion_viajes_id", cascade="all, delete-orphan")
    liquidacion_gastos_id = relationship("LiquidacionGastos", backref="liquidacion_gastos_id", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('chofer', 'fecha_liquidacion', name='uq_chofer_fecha'),
    )
