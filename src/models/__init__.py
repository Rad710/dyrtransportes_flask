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

from sqlalchemy import Column, ForeignKey, UniqueConstraint, Integer, String, Numeric, Boolean, Date, BigInteger, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import validates
from sqlalchemy.sql import functions
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from dataclasses import dataclass


class Base(DeclarativeBase):
    pass


@dataclass
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

    route_code: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True)
    origin: Mapped[str] = mapped_column(String(100))
    destination: Mapped[str] = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    payroll_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    # cannot delete since it's a foreign key
    deleted: Mapped[bool] = mapped_column(default=False)
    company_id: Mapped[str] = mapped_column(String(100))
    modification_user: Mapped[str] = mapped_column(String(100))

    # Mapped[List["Shipment"]] will be serialized if added
    route_shipments = relationship("Shipment", back_populates="shipment_route")

    # Mapped[List["RouteAudit"]]
    route_audits = relationship("RouteAudit", back_populates="audit_route")

    # __table_args__ = (
    #     UniqueConstraint(origin, destination, creation_user,
    #                      outdated.filter(deleted == False),
    #                      name="unique_origin_destination_user"),
    # )

    @validates('origin')
    def validate_origin(self, key, value):
        if not value or len(value) == 0:
            raise ValueError("Origen no puede estar vacío")
        return value

    @validates('destination')
    def validate_destination(self, key, value):
        if not value or len(value) == 0:
            raise ValueError("Destino no puede estar vacío")
        return value

    @validates('price')
    def validate_price(self, key, value):
        if not isinstance(value, Decimal):
            value = Decimal(value)

        if value < Decimal("0.00"):
            raise ValueError("Precio no puede ser negativo")

        return value

    @validates('payroll_price')
    def validate_payroll_price(self, key, value):
        if not isinstance(value, Decimal):
            value = Decimal(value)

        if value < Decimal("0.00"):
            raise ValueError("Precio Liquidación no puede ser negativo")

        return value


@dataclass
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

    audit_code: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True)
    route_code: Mapped[int] = mapped_column(ForeignKey('route.route_code'))
    origin: Mapped[str] = mapped_column(String(100))
    destination: Mapped[str] = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    payroll_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    deleted: Mapped[bool] = mapped_column(default=False)
    company_id: Mapped[str] = mapped_column(String(100))
    modification_user: Mapped[str] = mapped_column(String(100))

    audit_timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=functions.now())

    # Mapped["Route"]
    audit_route = relationship("Route", back_populates="route_audits")


@dataclass
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

    product_code: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(String(100))
    deleted: Mapped[bool] = mapped_column(default=False)
    company_id: Mapped[str] = mapped_column(String(100))
    modification_user: Mapped[str] = mapped_column(String(100))

    # Mapped[List["Shipment"]]
    product_shipments = relationship(
        "Shipment", back_populates="shipment_product")

    # Mapped[List["ProductAudit"]]
    product_audits = relationship(
        "ProductAudit", back_populates="audit_product")

    @validates('product_name')
    def validate_product_name(self, key, value):
        if not value:
            raise ValueError("Nombre del Producto no puede estar vacío")
        return value


@dataclass
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

    audit_code: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True)
    product_code: Mapped[int] = mapped_column(
        ForeignKey('product.product_code'))
    product_name: Mapped[str] = mapped_column(String(100))
    deleted: Mapped[bool] = mapped_column(default=False)
    company_id: Mapped[str] = mapped_column(String(100))
    modification_user: Mapped[str] = mapped_column(String(100))

    audit_timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=functions.now())

    # Mapped["Product"]
    audit_product = relationship("Product", back_populates="product_audits")


@dataclass
class Driver(Base):
    """
    (Nomina) This class represents a Driver in the database.

    It stores information about the driver's code, name, truck plate,
    trailer plate, and outdated flag. Additionally, it keeps track of
    the user who created the driver record and the creation timestamp.

    Attributes:
    * driver_code (int): The unique identifier for the driver (primary key, auto-incrementing).
    * driver_id (str): The id of the Driver.
    * driver_name (str): The name of the driver (not nullable, up to 100 characters).
    * driver_surname (str): The surname of the driver (not nullable, up to 100 characters).
    * truck_plate (str): The license plate number of the driver's truck (not nullable, up to 100 characters).
    * trailer_plate (str): The license plate number of the driver's trailer (not nullable, up to 100 characters).
    * deleted (bool): A flag indicating if the driver is deleted or not.
    * company_id (str): The company id who created the driver record (not nullable, up to 100 characters).
    * modification_user (str): The user who last modified the driver record (not nullable, up to 100 characters).
    """
    __tablename__ = "driver"

    driver_code: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True)
    driver_id: Mapped[str] = mapped_column(String(100))
    driver_name: Mapped[str] = mapped_column(String(100))
    driver_surname: Mapped[Optional[str]] = mapped_column(String(100))
    truck_plate: Mapped[str] = mapped_column(String(100))
    trailer_plate: Mapped[Optional[str]] = mapped_column(String(100))
    # used to deactivate account
    deleted: Mapped[bool] = mapped_column(default=False)
    company_id: Mapped[str] = mapped_column(String(100))
    modification_user: Mapped[str] = mapped_column(String(100))

    # Mapped[List["DriverPayroll"]]
    driver_payrolls = relationship(
        "DriverPayroll", back_populates="payroll_driver")

    # Mapped[List["Shipment"]]
    driver_shipments = relationship(
        "Shipment", back_populates="shipment_driver")

    # Mapped[List["DriverAudit"]]
    driver_audits = relationship("DriverAudit", back_populates="audit_driver")

    __table_args__ = (
        UniqueConstraint("driver_id", "company_id"),
    )

    @validates('driver_id')
    def validate_driver_id(self, key, value):
        if not value or len(value) == 0:
            raise ValueError("C.I. no puede estar vacío")
        return value

    @validates('driver_name')
    def validate_driver_name(self, key, value):
        if not value or len(value) == 0:
            raise ValueError("Nombre no puede estar vacío")
        return value

    @validates('driver_surname')
    def validate_driver_surname(self, key, value):
        if not value or len(value) == 0:
            raise ValueError("Apellido no puede estar vacío")
        return value

    @validates('truck_plate')
    def validate_truck_plate(self, key, value):
        if not value or len(value) == 0:
            raise ValueError("Chapa de Camión no puede estar vacío")
        return value

    @validates('trailer_plate')
    def validate_trailer_plate(self, key, value):
        if not value or len(value) == 0:
            raise ValueError("Chapa de Carreta no puede estar vacío")
        return value


@dataclass
class DriverAudit(Base):
    """
    (Nomina Audit) Driver Audit Table.

    Attributes:
    * audit_code (int): Unique identifier for the audit.
    * driver_code (int): The unique identifier for the driver (primary key, auto-incrementing).
    * driver_id (str): The id of the Driver.
    * driver_name (str): The name of the driver (not nullable, up to 100 characters).
    * driver_surname (str): The surname of the driver (not nullable, up to 100 characters).
    * truck_plate (str): The license plate number of the driver's truck (not nullable, up to 100 characters).
    * trailer_plate (str): The license plate number of the driver's trailer (not nullable, up to 100 characters).
    * deleted (bool): A flag indicating if the driver is deleted or not.
    * creation_user (str): The username of the user who created the driver record (not nullable, up to 100 characters).
    * audit_timestamp (datetime): The time at which this route record was modified.
    """
    __tablename__ = "driver_audit"

    audit_code: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True)
    driver_code: Mapped[int] = mapped_column(ForeignKey('driver.driver_code'))
    driver_id: Mapped[str] = mapped_column(String(100))
    driver_name: Mapped[str] = mapped_column(String(100))
    driver_surname: Mapped[Optional[str]] = mapped_column(String(100))
    truck_plate: Mapped[str] = mapped_column(String(100))
    trailer_plate: Mapped[Optional[str]] = mapped_column(String(100))
    deleted: Mapped[bool] = mapped_column(default=False)
    company_id: Mapped[str] = mapped_column(String(100))
    modification_user: Mapped[str] = mapped_column(String(100))
    audit_timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=functions.now())

    # Mapped["Driver"]
    audit_driver = relationship("Driver", back_populates="driver_audits")

    @validates('driver_id')
    def validate_driver_id(self, key, value):
        if not value:
            raise ValueError("Nombre del Producto no puede estar vacío")
        return value

    @validates('driver_name')
    def validate_driver_name(self, key, value):
        if not value:
            raise ValueError("Nombre del Producto no puede estar vacío")
        return value

    @validates('driver_surname')
    def validate_driver_surname(self, key, value):
        if not value:
            raise ValueError("Nombre del Producto no puede estar vacío")
        return value

    @validates('truck_plate')
    def validate_truck_plate(self, key, value):
        if not value:
            raise ValueError("Nombre del Producto no puede estar vacío")
        return value

    @validates('trailer_plate')
    def validate_trailer_plate(self, key, value):
        if not value:
            raise ValueError("Nombre del Producto no puede estar vacío")
        return value


@dataclass
class ShipmentPayroll(Base):
    """
    (Planillas) Represents a payroll record for a shipment.
    Attributes:
    * payroll_code (int): Auto-generated unique identifier for the payroll record.
    * payroll_timestamp (datetime): The time at which this route record was created.
    * collected (bool): Indicates whether the payment associated with the shipment has been collected.
    * deleted (bool): Indicates whether the payment associated with the shipment has been deleted.
    * company_id (str): The company id who created this payroll record.
    * modification_user (str): The user who created this payroll record.
    """
    __tablename__ = "shipment_payroll"

    payroll_code: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True)
    payroll_timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=functions.now())
    collected: Mapped[bool] = mapped_column(default=False)
    collection_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)
    deleted: Mapped[bool] = mapped_column(default=False)
    company_id: Mapped[str] = mapped_column(String(100))
    modification_user: Mapped[str] = mapped_column(String(100))

    # Mapped[List["Shipment"]]
    payroll_shipments = relationship(
        "Shipment", back_populates="shipment_payroll")

    # Mapped[List["ShipmentPayrollAudit"]]
    shipment_payroll_audits = relationship(
        "ShipmentPayrollAudit", back_populates="audit_shipment_payroll")

    @validates('payroll_timestamp')
    def validate_payroll_timestamp(self, key, value):
        if not value:
            raise ValueError("Fecha de la planilla no puede estar vacía")

        if not isinstance(value, datetime):
            value = datetime.strptime(value, "%a, %d %b %Y %H:%M:%S %Z")

        return value

    @validates('collection_timestamp')
    def validate_collection_timestamp(self, key, value):
        if value is not None and not isinstance(value, DateTime):
            value = datetime.strptime(value, "%a, %d %b %Y %H:%M:%S %Z")

        return value


@dataclass
class ShipmentPayrollAudit(Base):
    """
    (Planillas) Represents a payroll record for a shipment. Audit Table
    Attributes:
    * audit_code (int): Unique identifier for the audit.
    * payroll_code (int): Auto-generated unique identifier for the payroll record.
    * payroll_timestamp (datetime): The time at which this route record was created.
    * collected (bool): Indicates whether the payment associated with the shipment has been collected.
    * deleted (bool): Indicates whether the payment associated with the shipment has been deleted.
    * company_id (str): The company id who created this payroll record.
    * modification_user (str): The user who created this payroll record.
    * audit_timestamp (datetime): The time at which this route record was modified.
    """
    __tablename__ = "shipment_payroll_audit"

    audit_code: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True)
    payroll_code: Mapped[int] = mapped_column(
        ForeignKey('shipment_payroll.payroll_code'))
    payroll_timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=functions.now())
    collected: Mapped[bool] = mapped_column(default=False)
    collection_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)
    deleted: Mapped[bool] = mapped_column(default=False)
    company_id: Mapped[str] = mapped_column(String(100))
    modification_user: Mapped[str] = mapped_column(String(100))
    audit_timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=functions.now())

    # Mapped["ShipmentPayroll"]
    audit_shipment_payroll = relationship(
        "ShipmentPayroll", back_populates="shipment_payroll_audits")


@dataclass
class DriverPayroll(Base):
    """
    (Liquidaciones) Represents a payroll record for a driver.
    Attributes:
    * payroll_code (int): Auto-generated unique identifier for the payroll record.
    * payroll_timestamp (datetime): The time at which this route record was created.
    * driver_code (int): foreign key to driver information.
    * paid (bool): Indicates whether the payment associated with the shipment has been collected.
    * paid_timestamp (bool): Indicates when the payment associated with the shipment has been collected.
    * deleted (bool): Indicates whether the payment associated with the shipment has been deleted.
    * company_id (str): The company id who created this payroll record.
    * modification_user (str): The user who created this payroll record.
    """
    __tablename__ = "driver_payroll"

    payroll_code: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True)
    payroll_timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=functions.now())
    driver_code: Mapped[int] = mapped_column(ForeignKey('driver.driver_code'))
    paid: Mapped[bool] = mapped_column(default=False)
    paid_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)
    deleted: Mapped[bool] = mapped_column(default=False)
    company_id: Mapped[str] = mapped_column(String(100))
    modification_user: Mapped[str] = mapped_column(String(100))

    # Mapped["Driver"]
    payroll_driver = relationship("Driver", back_populates="driver_payrolls")

    # Mapped[List["Shipment"]]
    driver_shipments = relationship(
        "Shipment", back_populates="shipment_driver_payroll")

    # Mapped[List["ShipmentExpense"]]
    driver_payroll_shipment_expenses = relationship(
        "ShipmentExpense", back_populates="shipment_expense_driver_payroll")

    # Mapped[List["DriverPayrollAudit"]]
    driver_payroll_audits = relationship(
        "DriverPayrollAudit", back_populates="audit_driver_payroll")


@dataclass
class DriverPayrollAudit(Base):
    """
    (Liquidaciones) Represents a payroll record for a driver. Audit Table
    Attributes:
    * audit_code (int): Unique identifier for the audit.
    * payroll_code (int): Auto-generated unique identifier for the payroll record.
    * payroll_timestamp (datetime): The time at which this route record was created.
    * driver_code (int): foreign key to driver information.
    * paid (bool): Indicates whether the payment associated with the shipment has been collected.
    * paid_timestamp (bool): Indicates when the payment associated with the shipment has been collected.
    * deleted (bool): Indicates whether the payment associated with the shipment has been deleted.
    * company_id (str): The company id who created this payroll record.
    * modification_user (str): The user who created this payroll record.
    * audit_timestamp (datetime): The time at which this route record was modified.
    """
    __tablename__ = "driver_payroll_audit"

    audit_code: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True)
    payroll_code: Mapped[int] = mapped_column(
        ForeignKey('driver_payroll.payroll_code'))
    payroll_timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=functions.now())
    driver_code: Mapped[int] = mapped_column(ForeignKey('driver.driver_code'))
    paid: Mapped[bool] = mapped_column(default=False)
    paid_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)
    deleted: Mapped[bool] = mapped_column(default=False)
    company_id: Mapped[str] = mapped_column(String(100))
    modification_user: Mapped[str] = mapped_column(String(100))

    audit_timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=functions.now())

    # Mapped["DriverPayroll"]
    audit_driver_payroll = relationship(
        "DriverPayroll", back_populates="driver_payroll_audits")


@dataclass
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

    shipment_code: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True)
    shipment_date: Mapped[date] = mapped_column(Date)
    driver_code: Mapped[int] = mapped_column(ForeignKey('driver.driver_code'))
    product_code: Mapped[int] = mapped_column(
        ForeignKey('product.product_code'))
    route_code: Mapped[int] = mapped_column(ForeignKey('route.route_code'))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    payroll_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    ticket_code: Mapped[str] = mapped_column(String(100))
    origin_weight: Mapped[Decimal] = mapped_column(Numeric(10, 0))
    destination_weight: Mapped[Decimal] = mapped_column(Numeric(10, 0))
    shipment_payroll_code: Mapped[int] = mapped_column(
        ForeignKey('shipment_payroll.payroll_code'))
    driver_payroll_code: Mapped[int] = mapped_column(
        ForeignKey('driver_payroll.payroll_code'))
    deleted: Mapped[bool] = mapped_column(default=False)
    company_id: Mapped[str] = mapped_column(String(100))
    modification_user: Mapped[str] = mapped_column(String(100))

    # Mapped["Route"]
    shipment_route = relationship("Route", back_populates="route_shipments")

    # Mapped["Product"]
    shipment_product = relationship(
        "Product", back_populates="product_shipments")

    # Mapped["Driver"]
    shipment_driver = relationship("Driver", back_populates="driver_shipments")

    # Mapped["ShipmentPayroll"]
    shipment_payroll = relationship(
        "ShipmentPayroll", back_populates="payroll_shipments")

    # Mapped["DriverPayroll"]
    shipment_driver_payroll = relationship(
        "DriverPayroll", back_populates="driver_shipments")

    # Mapped[List["ShipmentAudit"]]
    shipment_audits = relationship(
        "ShipmentAudit", back_populates="audit_shipment")

    # __table_args__ = (
    #     UniqueConstraint('driver_code', 'ticket_number', 'shipment_date',
    #                      name='unique_driver_ticket_date'),
    # )


@dataclass
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

    audit_code: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    shipment_code: Mapped[int] = mapped_column(
        Integer, ForeignKey('shipment.shipment_code'))
    shipment_date: Mapped[date] = mapped_column(Date)
    driver_code: Mapped[int] = mapped_column(ForeignKey('driver.driver_code'))
    product_code: Mapped[int] = mapped_column(
        ForeignKey('product.product_code'))
    route_code: Mapped[int] = mapped_column(ForeignKey('route.route_code'))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    payroll_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    ticket_code: Mapped[str] = mapped_column(String(100))
    origin_weight: Mapped[Decimal] = mapped_column(Numeric(10, 0))
    destination_weight: Mapped[Decimal] = mapped_column(Numeric(10, 0))
    shipment_payroll_code: Mapped[int] = mapped_column(
        ForeignKey('shipment_payroll.payroll_code'))
    driver_payroll_code: Mapped[int] = mapped_column(
        ForeignKey('driver_payroll.payroll_code'))
    deleted: Mapped[bool] = mapped_column(default=False)
    company_id: Mapped[str] = mapped_column(String(100))
    modification_user: Mapped[str] = mapped_column(String(100))

    audit_timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=functions.now())

    # Mapped["Shipment"]
    audit_shipment = relationship("Shipment", back_populates="shipment_audits")


@dataclass
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

    expense_code: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True)
    expense_date: Mapped[date] = mapped_column(Date)
    receipt: Mapped[Optional[str]] = mapped_column(String(100))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 0))
    reason: Mapped[Optional[str]] = mapped_column(String(100))
    driver_payroll_code: Mapped[int] = mapped_column(
        ForeignKey('driver_payroll.payroll_code'))
    deleted: Mapped[bool] = mapped_column(default=False)
    company_id: Mapped[str] = mapped_column(String(100))
    modification_user: Mapped[str] = mapped_column(String(100))

    # Mapped["DriverPayroll"]
    shipment_expense_driver_payroll = relationship(
        "DriverPayroll", back_populates="driver_payroll_shipment_expenses")

    # Mapped[List["ShipmentExpenseAudit"]]
    shipment_expense_audits = relationship(
        "ShipmentExpenseAudit", back_populates="audit_shipment_expense")


@dataclass
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

    audit_code: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True)
    expense_code: Mapped[int] = mapped_column(
        ForeignKey('shipment_expense.expense_code'))
    expense_date: Mapped[date] = mapped_column(Date)
    receipt: Mapped[Optional[str]] = mapped_column(String(100))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 0))
    reason: Mapped[Optional[str]] = mapped_column(String(100))
    driver_payroll_code: Mapped[int] = mapped_column(
        ForeignKey('driver_payroll.payroll_code'))
    deleted: Mapped[bool] = mapped_column(default=False)
    company_id: Mapped[str] = mapped_column(String(100))
    modification_user: Mapped[str] = mapped_column(String(100))

    audit_timestamp: Mapped[datetime] = mapped_column(
        server_default=functions.now())

    # Mapped["Shipment"]
    audit_shipment_expense = relationship(
        "ShipmentExpense", back_populates="shipment_expense_audits")


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
    liquidacion_viajes = relationship(
        "LiquidacionViajes", backref="liquidacion_viajes", cascade="all, delete-orphan")
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
    fecha_creacion = Column(Date, ForeignKey(
        'planillas.fecha', ondelete='CASCADE'), nullable=True)

    __table_args__ = (
        UniqueConstraint('chofer', 'tiquet', 'fecha_viaje',
                         name='uq_chofer_tiquet_fecha'),
    )


# tipos de palabras clave (a usar en tabla PalabraClave)
tipo_clave = {'chofer/chapa', 'producto', 'origen', 'destino'}


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

    id = Column(Integer, ForeignKey('cobranzas.id',
                ondelete='CASCADE'), primary_key=True)
    precio_liquidacion = Column(Numeric(10, 2), nullable=False)

    id_liquidacion = Column(Integer, ForeignKey(
        'liquidaciones.id', ondelete='CASCADE'), nullable=False)


class LiquidacionGastos(Base):
    __tablename__ = "liquidacion_gastos"

    id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    fecha = Column(Date, nullable=False)
    boleta = Column(String(100), nullable=True)
    importe = Column(BigInteger, nullable=False)
    razon = Column(String(100), nullable=True)

    id_liquidacion = Column(Integer, ForeignKey(
        'liquidaciones.id', ondelete='CASCADE'), nullable=False)


class Liquidaciones(Base):
    __tablename__ = "liquidaciones"

    id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    chofer = Column(String(100), nullable=False)
    fecha_liquidacion = Column(Date, nullable=False)
    pagado = Column(Boolean, default=False, nullable=False)

    liquidacion_viajes_id = relationship(
        "LiquidacionViajes", backref="liquidacion_viajes_id", cascade="all, delete-orphan")
    liquidacion_gastos_id = relationship(
        "LiquidacionGastos", backref="liquidacion_gastos_id", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('chofer', 'fecha_liquidacion',
                         name='uq_chofer_fecha'),
    )
