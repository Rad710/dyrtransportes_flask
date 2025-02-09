from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass

from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Numeric
from sqlalchemy import Date
from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import validates
from sqlalchemy.sql import functions


from .base import Base


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
    * payroll_price (float): price paid to drivers for the trip on this route.
    * dispatch_code (str): Code associated with the shipment dispatch ticket.
    * receipt_code (str): Code associated with the shipment receipt ticket.
    * origin_weight (int): Weight of the shipment at its origin.
    * destination_weight (int): Weight of the shipment at its destination.
    * shipment_payroll_code (int): Code linking the shipment to its payroll record.
    * driver_payroll_code (int): Code linking the driver shipment to its payroll record.
    * deleted (bool): Indicates whether the shipment record has been deleted.
    * modification_user (str): The user who created this payroll record.
    * modification_timestamp (TIMESTAMP): The last modification time.
    """
    __tablename__ = "shipment"

    shipment_code: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True)
    shipment_date: Mapped[date] = mapped_column(Date)
    driver_name: Mapped[str] = mapped_column(String(100))
    truck_plate: Mapped[str] = mapped_column(String(100))
    driver_code: Mapped[int] = mapped_column(ForeignKey('driver.driver_code'))
    product_code: Mapped[int] = mapped_column(
        ForeignKey('product.product_code'))
    route_code: Mapped[int] = mapped_column(ForeignKey('route.route_code'))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), server_default='0')
    payroll_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), server_default='0')
    dispatch_code: Mapped[str] = mapped_column(String(100))
    receipt_code: Mapped[str] = mapped_column(String(100))
    origin_weight: Mapped[Decimal] = mapped_column(Numeric(10, 0))
    destination_weight: Mapped[Decimal] = mapped_column(Numeric(10, 0))
    shipment_payroll_code: Mapped[int] = mapped_column(
        ForeignKey('shipment_payroll.payroll_code'))
    driver_payroll_code: Mapped[int] = mapped_column(
        ForeignKey('driver_payroll.payroll_code'))
    deleted: Mapped[bool] = mapped_column(server_default='0')
    modification_user: Mapped[str] = mapped_column(String(100))
    modification_timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=functions.current_timestamp(), onupdate=functions.current_timestamp())

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

    @validates('shipment_date')
    def validate_shipment_date(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("shipment_date must not be null")

        try:
            value = datetime.strptime(value, "%a, %d %b %Y %H:%M:%S %Z").date()
        except ValueError as e:
            raise ValueError(
                f"Invalid shipment_date: {value}. Expected format: 'Day, DD Mon YYYY HH:MM:SS GMT'") from e

        return value

    @validates('price')
    def validate_price(self, key, value):
        if isinstance(value, str):
            try:
                value = Decimal(value)
            except InvalidOperation as e:
                raise ValueError(f"Invalid price value: {value}") from e

        if not isinstance(value, Decimal):
            raise TypeError(
                "price must be a Decimal or convertible to Decimal")

        if value < 0:
            raise ValueError("price must be non-negative")

        return value

    @validates('payroll_price')
    def validate_payroll_price(self, key, value):
        if isinstance(value, str):
            try:
                value = Decimal(value)
            except InvalidOperation as e:
                raise ValueError(
                    f"Invalid payroll_price value: {value}") from e

        if not isinstance(value, Decimal):
            raise TypeError(
                "payroll_price must be a Decimal or convertible to Decimal")

        if value < 0:
            raise ValueError("payroll_price must be non-negative")

        return value

    @validates('origin_weight')
    def validate_origin_weight(self, key, value):
        if isinstance(value, str):
            try:
                value = Decimal(value)
            except InvalidOperation as e:
                raise ValueError(
                    f"Invalid origin_weight value: {value}") from e

        if not isinstance(value, Decimal):
            raise TypeError(
                "origin_weight must be a Decimal or convertible to Decimal")

        if value < 0:
            raise ValueError("origin_weight must be non-negative")

        return value
            


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
    * payroll_price (float): price paid to drivers for the trip on this route.
    * dispatch_code (str): Code associated with the shipment dispatch ticket.
    * receipt_code (str): Code associated with the shipment receipt ticket.
    * origin_weight (int): Weight of the shipment at its origin.
    * destination_weight (int): Weight of the shipment at its destination.
    * shipment_payroll_code (int): Code linking the shipment to its payroll record.
    * driver_payroll_code (int): Code linking the driver shipment to its payroll record.
    * deleted (bool): Indicates whether the payment associated with the shipment has been deleted.
    * modification_user (str): The user who created this payroll record.
    * modification_timestamp (TIMESTAMP): The last modification time.
    """
    __tablename__ = "shipment_audit"

    audit_code: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    shipment_code: Mapped[int] = mapped_column(
        Integer, ForeignKey('shipment.shipment_code'))
    shipment_date: Mapped[date] = mapped_column(Date)
    driver_code: Mapped[int] = mapped_column(ForeignKey('driver.driver_code'))
    truck_plate: Mapped[str] = mapped_column(String(100))
    product_code: Mapped[int] = mapped_column(
        ForeignKey('product.product_code'))
    route_code: Mapped[int] = mapped_column(ForeignKey('route.route_code'))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    payroll_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    dispatch_code: Mapped[str] = mapped_column(String(100))
    receipt_code: Mapped[str] = mapped_column(String(100))
    origin_weight: Mapped[Decimal] = mapped_column(Numeric(10, 0))
    destination_weight: Mapped[Decimal] = mapped_column(Numeric(10, 0))
    shipment_payroll_code: Mapped[int] = mapped_column(
        ForeignKey('shipment_payroll.payroll_code'))
    driver_payroll_code: Mapped[int] = mapped_column(
        ForeignKey('driver_payroll.payroll_code'))
    deleted: Mapped[bool] = mapped_column()
    modification_user: Mapped[str] = mapped_column(String(100))
    modification_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP)

    # Mapped["Shipment"]
    audit_shipment = relationship("Shipment", back_populates="shipment_audits")
