"""
    Defines the Database Schema. Tables
    * Route, RouteAudit
    * Product, ProductAudit
    * Driver, DriverAudit,
    * ShipmentPayroll, ShipmentPayrollAudit
    * DriverPayroll, DriverPayrollAudit,
    * Shipment, ShipmentAudit,
    * ShipmentExpense, ShipmentExpenseAudit
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import UniqueConstraint
from sqlalchemy.sql import func


db = SQLAlchemy()

class Route(db.Model):
    """(Precios) Represents a transportation route within a system.

    Attributes:
    * route_code (int): Unique identifier for the route.
    * origin (str): City or location where the route begins.
    * destination (str): City or location where the route ends.
    * price (float): Standard price for traveling this route.
    * paid_price (float): price paid to drivers for the trip on this route.
    * deleted (bool): Indicates whether the route information is no longer valid.
    * company_id (str): The company who created this route record.
    * modification_user (str): The user who last modified this route record.
    """

    route_code = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    origin = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    payroll_price = db.Column(db.Numeric(10, 2), nullable=False)

    #cannot delete since it's a foreign key
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    company_id = db.Column(db.String(100), nullable=False)
    modification_user = db.Column(db.String(100), nullable=False)
    
    shipment_route_code = relationship("Shipment", backref="shipment_route_code", cascade="all, delete-orphan")

    # __table_args__ = (
    #     UniqueConstraint(origin, destination, creation_user,
    #                      outdated.filter(outdated == False),
    #                      name="unique_origin_destination_user"),
    # )


class RouteAudit(db.Model):
    """(Precios) Represents a transportation route within a system.

    Attributes:
    * audit_code (int): Unique identifier for the audit.
    * route_code (int): foreign key identifier for the route.
    * origin (str): City or location where the route begins.
    * destination (str): City or location where the route ends.
    * price (float): Standard price for traveling this route.
    * paid_price (float): price paid to drivers for the trip on this route.
    * deleted (bool): Indicates whether the route information is no longer valid.
    * company_id (str): The user who created this route record.
    * modification_user (str): The user who last modified this route record.
    * audit_timestamp (datetime): The time at which this route record was modified.
    """

    audit_code = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    route_code = db.Column(db.Integer, ForeignKey('route.route_code'), nullable=False)
    origin = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    payroll_price = db.Column(db.Numeric(10, 2), nullable=False)
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    company_id = db.Column(db.String(100), nullable=False)
    modification_user = db.Column(db.String(100), nullable=False)
    
    audit_timestamp = db.Column(db.DateTime, server_default=func.now(), nullable=False)


class Product(db.Model):
    """(Palabras/Productos) Represents a product within a product management system.

    Attributes:
    * product_code (int): A unique identifier for the product.
    * product_name (str): The name of the product.
    * deleted (bool): Indicates whether the product is retired or discontinued.
    * company_id (str): The company who created this product record.
    * modification_user (str): The user who last modified this product record.
    """

    product_code = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    product_name = db.Column(db.String(100), nullable=False)

    #cannot delete since it's a foreign key
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    company_id = db.Column(db.String(100), nullable=False)
    modification_user = db.Column(db.String(100), nullable=False)

    shipment_product_code = relationship("Shipment", backref="shipment_product_code", cascade="all, delete-orphan")

    # __table_args__ = (
    #     UniqueConstraint(product_name, company_id,
    #                      outdated.filter(outdated == False),
    #                      name="unique_product_user"),
    # )


class ProductAudit(db.Model):
    """(Palabras/Productos) Represents a product within a product management system.

    Attributes:
    * audit_code (int): Unique identifier for the audit.
    * product_code (int): foreign key identifier for the product.
    * product_name (str): The name of the product.
    * deleted (bool): Indicates whether the product is retired or discontinued.
    * company_id (str): The company who created this product record.
    * modification_user (str): The user who last modified this product record.
    * audit_timestamp (datetime): The time at which this route record was modified.
    """

    audit_code = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    product_code = db.Column(db.Integer, ForeignKey('product.product_code'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    company_id = db.Column(db.String(100), nullable=False)
    modification_user = db.Column(db.String(100), nullable=False)
    
    audit_timestamp = db.Column(db.DateTime, server_default=func.now(), nullable=False)


class Driver(db.Model):
    """
    (Nomina) This class represents a Driver in the database.

    It stores information about the driver's code, name, truck plate,
    trailer plate, and outdated flag. Additionally, it keeps track of
    the user who created the driver record and the creation timestamp.

    Attributes:
    * driver_code (int): The unique identifier for the driver (primary key, auto-incrementing).
    * driver_name (str): The name of the driver (not nullable, up to 100 characters).
    * truck_plate (str): The license plate number of the driver's truck (not nullable, up to 100 characters).
    * trailer_plate (str): The license plate number of the driver's trailer (not nullable, up to 100 characters).
    * deleted (bool): A flag indicating if the driver is deleted or not.
    * company_id (str): The company id who created the driver record (not nullable, up to 100 characters).
    * modification_user (str): The user who last modified the driver record (not nullable, up to 100 characters).
    """

    driver_code = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    driver_name = db.Column(db.String(100), nullable=False)
    truck_plate = db.Column(db.String(100), nullable=False)
    trailer_plate = db.Column(db.String(100), nullable=True)
    # used to deactivate account
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    company_id = db.Column(db.String(100), nullable=False)
    modification_user = db.Column(db.String(100), nullable=False)

    driver_payroll_driver_code = relationship("DriverPayroll", backref="driver_payroll_driver_code", cascade="all, delete-orphan")
    shipment_driver_code = relationship("Shipment", backref="shipment_driver_code", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("driver_name", "company_id"),
    )


class DriverAudit(db.Model):
    """
    (Nomina Audit) Driver Audit Table.

    Attributes:
    * audit_code (int): Unique identifier for the audit.
    * driver_code (int): The unique identifier for the driver (primary key, auto-incrementing).
    * driver_name (str): The name of the driver (not nullable, up to 100 characters).
    * truck_plate (str): The license plate number of the driver's truck (not nullable, up to 100 characters).
    * trailer_plate (str): The license plate number of the driver's trailer (not nullable, up to 100 characters).
    * deleted (bool): A flag indicating if the driver is deleted or not.
    * creation_user (str): The username of the user who created the driver record (not nullable, up to 100 characters).
    * audit_timestamp (datetime): The time at which this route record was modified.
    """
    
    audit_code = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    driver_code = db.Column(db.Integer, ForeignKey('driver.driver_code'), nullable=False)
    driver_name = db.Column(db.String(100), nullable=False)
    truck_plate = db.Column(db.String(100), nullable=False)
    trailer_plate = db.Column(db.String(100), nullable=False)
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    company_id = db.Column(db.String(100), nullable=False)
    modification_user = db.Column(db.String(100), nullable=False)
    audit_timestamp = db.Column(db.DateTime, server_default=func.now(), nullable=False)


class ShipmentPayroll(db.Model):
    """
    (Planillas) Represents a payroll record for a shipment.
    Attributes:
    * payroll_code (int): Auto-generated unique identifier for the payroll record.
    * creation_timestamp (datetime): The time at which this route record was created.
    * collected (bool): Indicates whether the payment associated with the shipment has been collected.
    * deleted (bool): Indicates whether the payment associated with the shipment has been deleted.
    * company_id (str): The company id who created this payroll record.
    * modification_user (str): The user who created this payroll record.
    """

    payroll_code = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    creation_timestamp = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    collected = db.Column(db.Boolean, default=False, nullable=False)
    collection_timestamp = db.Column(db.DateTime, nullable=True)
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    company_id = db.Column(db.String(100), nullable=False)
    modification_user = db.Column(db.String(100), nullable=False)

    shipment_shipment_payroll_code = relationship("Shipment", backref="shipment_shipment_payroll_code", cascade="all, delete-orphan")



class ShipmentPayrollAudit(db.Model):
    """
    (Planillas) Represents a payroll record for a shipment. Audit Table
    Attributes:
    * audit_code (int): Unique identifier for the audit.
    * payroll_code (int): Auto-generated unique identifier for the payroll record.
    * creation_timestamp (datetime): The time at which this route record was created.
    * collected (bool): Indicates whether the payment associated with the shipment has been collected.
    * deleted (bool): Indicates whether the payment associated with the shipment has been deleted.
    * company_id (str): The company id who created this payroll record.
    * modification_user (str): The user who created this payroll record.
    * audit_timestamp (datetime): The time at which this route record was modified.
    """

    audit_code = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    payroll_code = db.Column(db.Integer, ForeignKey('shipment_payroll.payroll_code'), nullable=False)
    creation_timestamp = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    collected = db.Column(db.Boolean, default=False, nullable=False)
    collection_timestamp = db.Column(db.DateTime, nullable=True)
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    company_id = db.Column(db.String(100), nullable=False)
    modification_user = db.Column(db.String(100), nullable=False)

    audit_timestamp = db.Column(db.DateTime, server_default=func.now(), nullable=False)



class DriverPayroll(db.Model):
    """
    (Liquidaciones) Represents a payroll record for a driver.
    Attributes:
    * payroll_code (int): Auto-generated unique identifier for the payroll record.
    * creation_timestamp (datetime): The time at which this route record was created.
    * driver_code (int): foreign key to driver information.
    * paid (bool): Indicates whether the payment associated with the shipment has been collected.
    * paid_timestamp (bool): Indicates when the payment associated with the shipment has been collected.
    * deleted (bool): Indicates whether the payment associated with the shipment has been deleted.
    * company_id (str): The company id who created this payroll record.
    * modification_user (str): The user who created this payroll record.
    """
        
    payroll_code = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    creation_timestamp = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    driver_code = db.Column(db.Integer, ForeignKey('driver.driver_code'), nullable=False)
    paid = db.Column(db.Boolean, default=False, nullable=False)
    paid_timestamp = db.Column(db.DateTime, nullable=True)
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    company_id = db.Column(db.String(100), nullable=False)
    modification_user = db.Column(db.String(100), nullable=False)

    shipment_driver_payroll_code = relationship("Shipment", backref="shipment_driver_payroll_code", cascade="all, delete-orphan")
    shipment_expense_code = relationship("ShipmentExpenses", backref="shipment_expense_code", cascade="all, delete-orphan")


class DriverPayrollAudit(db.Model):
    """
    (Liquidaciones) Represents a payroll record for a driver. Audit Table
    Attributes:
    * audit_code (int): Unique identifier for the audit.
    * payroll_code (int): Auto-generated unique identifier for the payroll record.
    * creation_timestamp (datetime): The time at which this route record was created.
    * driver_code (int): foreign key to driver information.
    * paid (bool): Indicates whether the payment associated with the shipment has been collected.
    * paid_timestamp (bool): Indicates when the payment associated with the shipment has been collected.
    * deleted (bool): Indicates whether the payment associated with the shipment has been deleted.
    * company_id (str): The company id who created this payroll record.
    * modification_user (str): The user who created this payroll record.
    * audit_timestamp (datetime): The time at which this route record was modified.
    """
    
    audit_code = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    payroll_code = db.Column(db.Integer, ForeignKey('driver_payroll.payroll_code'), nullable=False)
    creation_timestamp = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    driver_code = db.Column(db.Integer, ForeignKey('driver.driver_code'), nullable=False)
    paid = db.Column(db.Boolean, default=False, nullable=False)
    paid_timestamp = db.Column(db.DateTime, nullable=True)
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    company_id = db.Column(db.String(100), nullable=False)
    modification_user = db.Column(db.String(100), nullable=False)

    audit_timestamp = db.Column(db.DateTime, server_default=func.now(), nullable=False)


class Shipment(db.Model):
    """(Cobranzas) Represents a single product shipment within a transportation system. 

    Attributes:
    * shipment_code (int): Unique identifier for the shipment.
    * shipment_date (date): Date on which the shipment took place.
    * driver_code (int): Code identifying the driver responsible for the shipment.
    * product_code (int): Code identifying the product being shipped.
    * route_code (int): Code identifying the route taken for the shipment.
    * price (float): Standard price charged for the shipment.
    * paid_price (float): Actual price paid for the shipment.
    * ticket_code (str): Code associated with the shipment ticket or waybill.
    * origin_weight (int): Weight of the shipment at its origin.
    * destination_weight (int): Weight of the shipment at its destination.
    * shipment_payroll_code (int): Code linking the shipment to its payroll record.
    * driver_payroll_code (int): Code linking the driver shipment to its payroll record.
    * deleted (bool): Indicates whether the shipment record has been deleted.
    * company_id (str): The company id who created this payroll record.
    * modification_user (str): The user who created this payroll record.
    """

    shipment_code = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    shipment_date = db.Column(db.Date, nullable=False)
    driver_code = db.Column(db.Integer, ForeignKey('driver.driver_code'), nullable=False)
    product_code = db.Column(db.Integer, ForeignKey('product.product_code'), nullable=False)
    route_code = db.Column(db.Integer, ForeignKey('route.route_code'), nullable=False)
    price = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    payroll_price = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    ticket_code = db.Column(db.String(100), nullable=False)
    origin_weight = db.Column(db.Integer, nullable=False)
    destination_weight = db.Column(db.Integer, nullable=False)
    shipment_payroll_code = db.Column(db.Integer, ForeignKey('shipment_payroll.payroll_code'), nullable=False)
    driver_payroll_code = db.Column(db.Integer, ForeignKey('driver_payroll.payroll_code'), nullable=False)
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    company_id = db.Column(db.String(100), nullable=False)
    modification_user = db.Column(db.String(100), nullable=False)

    # __table_args__ = (
    #     UniqueConstraint('driver_code', 'ticket_number', 'shipment_date', 
    #                      name='unique_driver_ticket_date'),
    # )


class ShipmentAudit(db.Model):
    """(Cobranzas) Represents a single product shipment within a transportation system. 

    Attributes:
    * audit_code (int): Unique identifier for the audit.
    * shipment_code (int): Unique identifier for the shipment.
    * shipment_date (date): Date on which the shipment took place.
    * driver_code (int): Code identifying the driver responsible for the shipment.
    * product_code (int): Code identifying the product being shipped.
    * route_code (int): Code identifying the route taken for the shipment.
    * price (float): Standard price charged for the shipment.
    * paid_price (float): Actual price paid for the shipment.
    * ticket_code (str): Code associated with the shipment ticket or waybill.
    * origin_weight (int): Weight of the shipment at its origin.
    * destination_weight (int): Weight of the shipment at its destination.
    * shipment_payroll_code (int): Code linking the shipment to its payroll record.
    * driver_payroll_code (int): Code linking the driver shipment to its payroll record.
    * deleted (bool): Indicates whether the payment associated with the shipment has been deleted.
    * company_id (str): The company id who created this payroll record.
    * modification_user (str): The user who created this payroll record.
    * audit_timestamp (datetime): The time at which this route record was modified.
    """
    audit_code = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    shipment_code = db.Column(db.Integer, ForeignKey('shipment.shipment_code'), nullable=False)
    shipment_date = db.Column(db.Date, nullable=False)
    driver_code = db.Column(db.Integer, ForeignKey('driver.driver_code'), nullable=False)
    product_code = db.Column(db.Integer, ForeignKey('product.product_code'), nullable=False)
    route_code = db.Column(db.Integer, ForeignKey('route.route_code'), nullable=False)
    price = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    payroll_price = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    ticket_code = db.Column(db.String(100), nullable=False)
    origin_weight = db.Column(db.Integer, nullable=False)
    destination_weight = db.Column(db.Integer, nullable=False)
    shipment_payroll_code = db.Column(db.Integer, ForeignKey('shipment_payroll.payroll_code'), nullable=False)
    driver_payroll_code = db.Column(db.Integer, ForeignKey('driver_payroll.payroll_code'), nullable=False)
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    company_id = db.Column(db.String(100), nullable=False)
    modification_user = db.Column(db.String(100), nullable=False)

    audit_timestamp = db.Column(db.DateTime, server_default=func.now(), nullable=False)


class ShipmentExpense(db.Model):
    """(LiquidacionGastos) Represents a shipment expenses like gas, etc. 

    Attributes:
    * expense_code (int): Unique identifier for the expense.
    * expense_date (date): Date on which the expense took place.
    * receipt (str): Code of the expense receipt.
    * amount (bigint): Cost of the expense.
    * reason (str): reason of the expense
    * driver_payroll_code (int): Code linking the driver shipment to its payroll record.
    * deleted (bool): Indicates whether the payment associated with the shipment has been deleted.
    * company_id (str): The company id who created this payroll record.
    * modification_user (str): The user who created this payroll record.
    """
    
    expense_code = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    expense_date = db.Column(db.Date, nullable=False)
    receipt = db.Column(db.String(100), nullable=True)
    amount = db.Column(db.BigInteger, nullable=False)
    reason = db.Column(db.String(100), nullable=True)
    driver_payroll_code = db.Column(db.Integer, ForeignKey('driver_payroll.payroll_code'), nullable=False)
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    company_id = db.Column(db.String(100), nullable=False)
    modification_user = db.Column(db.String(100), nullable=False)


class ShipmentExpenseAudit(db.Model):
    """(LiquidacionGastos) Represents a shipment expenses like gas, etc. 

    Attributes:
    * expense_code (int): Unique identifier for the expense.
    * expense_date (date): Date on which the expense took place.
    * receipt (str): Code of the expense receipt.
    * amount (bigint): Cost of the expense.
    * reason (str): reason of the expense
    * driver_payroll_code (int): Code linking the driver shipment to its payroll record.
    * deleted (bool): Indicates whether the payment associated with the shipment has been deleted.
    * company_id (str): The company id who created this payroll record.
    * modification_user (str): The user who created this payroll record.
    * audit_timestamp (datetime): The time at which this route record was modified.
    """

    audit_code = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    expense_code = db.Column(db.Integer, ForeignKey('shipment_expense.expense_code'), nullable=False)
    expense_date = db.Column(db.Date, nullable=False)
    receipt = db.Column(db.String(100), nullable=True)
    amount = db.Column(db.BigInteger, nullable=False)
    reason = db.Column(db.String(100), nullable=True)
    driver_payroll_code = db.Column(db.Integer, ForeignKey('driver_payroll.payroll_code'), nullable=False)
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    company_id = db.Column(db.String(100), nullable=False)
    modification_user = db.Column(db.String(100), nullable=False)

    audit_timestamp = db.Column(db.DateTime, server_default=func.now(), nullable=False)


# Old
class Planillas(db.Model):
    fecha = db.Column(db.Date, nullable=False, primary_key=True)


class Precios(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    origen = db.Column(db.String(100), nullable=False)
    destino = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    precio_liquidacion = db.Column(db.Numeric(10, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint('origen', 'destino', name='uq_origen_destino'),
    )


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


tipo_clave = {'chofer/chapa', 'producto', 'origen', 'destino'} #tipos de palabras clave (a usar en tabla PalabraClave)
class Palabras(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    palabra = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(100), nullable=False)

    __table_args__ = (
        UniqueConstraint('palabra', 'tipo', name='uq_palabra_tipo'),
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
