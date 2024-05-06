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

from sqlalchemy import Column, ForeignKey, UniqueConstraint, Integer, String, Numeric, Boolean, DateTime, Date, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import functions
from decimal import Decimal

from models.database import Base

class Route(Base):
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

    __tablename__ = "route"


    route_code : Column[int] = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    origin : Column[str] = Column(String(100), nullable=False)
    destination : Column[str] = Column(String(100), nullable=False)
    price : Column[Decimal]  = Column(Numeric(10, 2), nullable=False)
    payroll_price : Column[Decimal] = Column(Numeric(10, 2), nullable=False)

    #cannot delete since it's a foreign key
    deleted : Column[bool] = Column(Boolean, default=False, nullable=False)
    company_id : Column[str] = Column(String(100), nullable=False)
    modification_user : Column[str] = Column(String(100), nullable=False)
    
    shipment_route_code = relationship("Shipment", backref="shipment_route_code", cascade="all, delete-orphan")

    # __table_args__ = (
    #     UniqueConstraint(origin, destination, creation_user,
    #                      outdated.filter(deleted == False),
    #                      name="unique_origin_destination_user"),
    # )


class RouteAudit(Base):
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
    __tablename__ = "route_audit"


    audit_code = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    route_code = Column(Integer, ForeignKey('route.route_code'), nullable=False)
    origin = Column(String(100), nullable=False)
    destination = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    payroll_price = Column(Numeric(10, 2), nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)
    company_id = Column(String(100), nullable=False)
    modification_user = Column(String(100), nullable=False)
    
    audit_timestamp = Column(DateTime, server_default=functions.now(), nullable=False)


class Product(Base):
    """(Palabras/Productos) Represents a product within a product management system.

    Attributes:
    * product_code (int): A unique identifier for the product.
    * product_name (str): The name of the product.
    * deleted (bool): Indicates whether the product is retired or discontinued.
    * company_id (str): The company who created this product record.
    * modification_user (str): The user who last modified this product record.
    """

    __tablename__ = "product"


    product_code = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    product_name = Column(String(100), nullable=False)

    #cannot delete since it's a foreign key
    deleted = Column(Boolean, default=False, nullable=False)
    company_id = Column(String(100), nullable=False)
    modification_user = Column(String(100), nullable=False)

    shipment_product_code = relationship("Shipment", backref="shipment_product_code", cascade="all, delete-orphan")

    # __table_args__ = (
    #     UniqueConstraint(product_name, company_id,
    #                      outdated.filter(outdated == False),
    #                      name="unique_product_user"),
    # )


class ProductAudit(Base):
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

    __tablename__ = "product_audit"

    audit_code = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    product_code = Column(Integer, ForeignKey('product.product_code'), nullable=False)
    product_name = Column(String(100), nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)
    company_id = Column(String(100), nullable=False)
    modification_user = Column(String(100), nullable=False)
    
    audit_timestamp = Column(DateTime, server_default=functions.now(), nullable=False)


class Driver(Base):
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

    __tablename__ = "driver"

    driver_code = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    driver_name = Column(String(100), nullable=False)
    truck_plate = Column(String(100), nullable=False)
    trailer_plate = Column(String(100), nullable=True)
    # used to deactivate account
    deleted = Column(Boolean, default=False, nullable=False)
    company_id = Column(String(100), nullable=False)
    modification_user = Column(String(100), nullable=False)

    driver_payroll_driver_code = relationship("DriverPayroll", backref="driver_payroll_driver_code", cascade="all, delete-orphan")
    shipment_driver_code = relationship("Shipment", backref="shipment_driver_code", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("driver_name", "company_id"),
    )


class DriverAudit(Base):
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

    __tablename__ = "driver_audit"

    
    audit_code = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    driver_code = Column(Integer, ForeignKey('driver.driver_code'), nullable=False)
    driver_name = Column(String(100), nullable=False)
    truck_plate = Column(String(100), nullable=False)
    trailer_plate = Column(String(100), nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)
    company_id = Column(String(100), nullable=False)
    modification_user = Column(String(100), nullable=False)
    audit_timestamp = Column(DateTime, server_default=functions.now(), nullable=False)


class ShipmentPayroll(Base):
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

    __tablename__ = "shipment_payroll"

    payroll_code = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    creation_timestamp = Column(DateTime, server_default=functions.now(), nullable=False)
    collected = Column(Boolean, default=False, nullable=False)
    collection_timestamp = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)
    company_id = Column(String(100), nullable=False)
    modification_user = Column(String(100), nullable=False)

    shipment_shipment_payroll_code = relationship("Shipment", backref="shipment_shipment_payroll_code", cascade="all, delete-orphan")



class ShipmentPayrollAudit(Base):
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

    __tablename__ = "shipment_payroll_audit"

    audit_code = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    payroll_code = Column(Integer, ForeignKey('shipment_payroll.payroll_code'), nullable=False)
    creation_timestamp = Column(DateTime, server_default=functions.now(), nullable=False)
    collected = Column(Boolean, default=False, nullable=False)
    collection_timestamp = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)
    company_id = Column(String(100), nullable=False)
    modification_user = Column(String(100), nullable=False)

    audit_timestamp = Column(DateTime, server_default=functions.now(), nullable=False)



class DriverPayroll(Base):
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

    __tablename__ = "driver_payroll"

        
    payroll_code = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    creation_timestamp = Column(DateTime, server_default=functions.now(), nullable=False)
    driver_code = Column(Integer, ForeignKey('driver.driver_code'), nullable=False)
    paid = Column(Boolean, default=False, nullable=False)
    paid_timestamp = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)
    company_id = Column(String(100), nullable=False)
    modification_user = Column(String(100), nullable=False)

    shipment_driver_payroll_code = relationship("Shipment", backref="shipment_driver_payroll_code", cascade="all, delete-orphan")
    shipment_expense_code = relationship("ShipmentExpense", backref="shipment_expense_code", cascade="all, delete-orphan")


class DriverPayrollAudit(Base):
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
    
    __tablename__ = "driver_payroll_audit"


    audit_code = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    payroll_code = Column(Integer, ForeignKey('driver_payroll.payroll_code'), nullable=False)
    creation_timestamp = Column(DateTime, server_default=functions.now(), nullable=False)
    driver_code = Column(Integer, ForeignKey('driver.driver_code'), nullable=False)
    paid = Column(Boolean, default=False, nullable=False)
    paid_timestamp = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)
    company_id = Column(String(100), nullable=False)
    modification_user = Column(String(100), nullable=False)

    audit_timestamp = Column(DateTime, server_default=functions.now(), nullable=False)


class Shipment(Base):
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

    __tablename__ = "shipment"

    shipment_code = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    shipment_date = Column(Date, nullable=False)
    driver_code = Column(Integer, ForeignKey('driver.driver_code'), nullable=False)
    product_code = Column(Integer, ForeignKey('product.product_code'), nullable=False)
    route_code = Column(Integer, ForeignKey('route.route_code'), nullable=False)
    price = Column(Numeric(10, 2), default=0, nullable=False)
    payroll_price = Column(Numeric(10, 2), default=0, nullable=False)
    ticket_code = Column(String(100), nullable=False)
    origin_weight = Column(Integer, nullable=False)
    destination_weight = Column(Integer, nullable=False)
    shipment_payroll_code = Column(Integer, ForeignKey('shipment_payroll.payroll_code'), nullable=False)
    driver_payroll_code = Column(Integer, ForeignKey('driver_payroll.payroll_code'), nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)
    company_id = Column(String(100), nullable=False)
    modification_user = Column(String(100), nullable=False)

    # __table_args__ = (
    #     UniqueConstraint('driver_code', 'ticket_number', 'shipment_date', 
    #                      name='unique_driver_ticket_date'),
    # )


class ShipmentAudit(Base):
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

    __tablename__ = "shipment_audit"


    audit_code = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    shipment_code = Column(Integer, ForeignKey('shipment.shipment_code'), nullable=False)
    shipment_date = Column(Date, nullable=False)
    driver_code = Column(Integer, ForeignKey('driver.driver_code'), nullable=False)
    product_code = Column(Integer, ForeignKey('product.product_code'), nullable=False)
    route_code = Column(Integer, ForeignKey('route.route_code'), nullable=False)
    price = Column(Numeric(10, 2), default=0, nullable=False)
    payroll_price = Column(Numeric(10, 2), default=0, nullable=False)
    ticket_code = Column(String(100), nullable=False)
    origin_weight = Column(Integer, nullable=False)
    destination_weight = Column(Integer, nullable=False)
    shipment_payroll_code = Column(Integer, ForeignKey('shipment_payroll.payroll_code'), nullable=False)
    driver_payroll_code = Column(Integer, ForeignKey('driver_payroll.payroll_code'), nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)
    company_id = Column(String(100), nullable=False)
    modification_user = Column(String(100), nullable=False)

    audit_timestamp = Column(DateTime, server_default=functions.now(), nullable=False)


class ShipmentExpense(Base):
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

    __tablename__ = "shipment_expense"

    
    expense_code = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    expense_date = Column(Date, nullable=False)
    receipt = Column(String(100), nullable=True)
    amount = Column(BigInteger, nullable=False)
    reason = Column(String(100), nullable=True)
    driver_payroll_code = Column(Integer, ForeignKey('driver_payroll.payroll_code'), nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)
    company_id = Column(String(100), nullable=False)
    modification_user = Column(String(100), nullable=False)


class ShipmentExpenseAudit(Base):
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

    __tablename__ = "shipment_expense_audit"

    audit_code = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    expense_code = Column(Integer, ForeignKey('shipment_expense.expense_code'), nullable=False)
    expense_date = Column(Date, nullable=False)
    receipt = Column(String(100), nullable=True)
    amount = Column(BigInteger, nullable=False)
    reason = Column(String(100), nullable=True)
    driver_payroll_code = Column(Integer, ForeignKey('driver_payroll.payroll_code'), nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)
    company_id = Column(String(100), nullable=False)
    modification_user = Column(String(100), nullable=False)

    audit_timestamp = Column(DateTime, server_default=functions.now(), nullable=False)


# Old
class Planillas(Base):
    __tablename__ = "planillas"


    fecha = Column(Date, nullable=False, primary_key=True)


class Precios(Base):
    __tablename__ = "precios"


    id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    origen = Column(String(100), nullable=False)
    destino = Column(String(100), nullable=False)
    precio = Column(Numeric(10, 2), nullable=False)
    precio_liquidacion = Column(Numeric(10, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint('origen', 'destino', name='uq_origen_destino'),
    )


class Cobranzas(Base):
    __tablename__ = "cobranzas"


    id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    liquidacion_viajes = relationship("LiquidacionViajes", backref="liquidacion_viajes", cascade="all, delete-orphan")
    fecha_viaje = Column(Date, nullable=False)
    chofer = Column(String(100), nullable=False)
    chapa = Column(String(100))
    producto = Column(String(100))
    origen = Column(String(100))
    destino = Column(String(100))
    tiquet = Column(Integer, nullable=False)
    kilos_origen = Column(Integer, nullable=False)
    kilos_destino = Column(Integer, nullable=False)
    precio = Column(Numeric(10, 2), nullable=False)
    fecha_creacion = Column(Date, ForeignKey('planillas.fecha', ondelete='CASCADE'), nullable=True)

    __table_args__ = (
        UniqueConstraint('chofer', 'tiquet', 'fecha_viaje', name='uq_chofer_tiquet_fecha'),
    )


tipo_clave = {'chofer/chapa', 'producto', 'origen', 'destino'} #tipos de palabras clave (a usar en tabla PalabraClave)
class Palabras(Base):
    __tablename__ = "palabras"

    id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    palabra = Column(String(100), nullable=False)
    tipo = Column(String(100), nullable=False)

    __table_args__ = (
        UniqueConstraint('palabra', 'tipo', name='uq_palabra_tipo'),
    )


class LiquidacionViajes(Base):
    __tablename__ = "liquidacion_viajes"

    id = Column(Integer,ForeignKey('cobranzas.id', ondelete='CASCADE'), primary_key=True)
    precio_liquidacion = Column(Numeric(10, 2), nullable=False)

    id_liquidacion = Column(Integer,ForeignKey('liquidaciones.id', ondelete='CASCADE'), nullable=False)



class LiquidacionGastos(Base):
    __tablename__ = "liquidacion_gastos"

    id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    fecha = Column(Date, nullable=False)
    boleta = Column(String(100), nullable=True)
    importe = Column(BigInteger, nullable=False)
    razon = Column(String(100), nullable=True)

    id_liquidacion = Column(Integer,ForeignKey('liquidaciones.id', ondelete='CASCADE'), nullable=False)


class Liquidaciones(Base):
    __tablename__ = "liquidaciones"

    id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    chofer = Column(String(100), nullable=False)
    fecha_liquidacion = Column(Date, nullable=False)
    pagado = Column(Boolean, default=False, nullable=False)

    liquidacion_viajes_id = relationship("LiquidacionViajes", backref="liquidacion_viajes_id", cascade="all, delete-orphan")
    liquidacion_gastos_id = relationship("LiquidacionGastos", backref="liquidacion_gastos_id", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('chofer', 'fecha_liquidacion', name='uq_chofer_fecha'),
    )
