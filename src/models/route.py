from datetime import datetime
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass

from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Numeric
from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import validates
from sqlalchemy.sql import functions


from .base import Base


@dataclass
class Route(Base):
    """(Precios) Represents a transportation route within a system.

    Attributes:
    * route_code (int): Unique identifier for the route.
    * origin (str): City or location where the route begins.
    * destination (str): City or location where the route ends.
    * price (float): Standard price for traveling this route.
    * payroll_price (float): price paid to drivers for the trip on this route.
    * deleted (bool): Indicates whether the route information is no longer valid.
    * modification_user (str): The user who last modified this route record.
    * modification_timestamp (TIMESTAMP): The last modification time.
    """

    __tablename__ = "route"

    route_code: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    origin: Mapped[str] = mapped_column(String(100))
    destination: Mapped[str] = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    payroll_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    # cannot delete since it's a foreign key
    deleted: Mapped[bool] = mapped_column(server_default="0")
    modification_user: Mapped[str] = mapped_column(String(100))
    modification_timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=functions.current_timestamp(),
        onupdate=functions.current_timestamp(),
    )

    # Mapped[List["Shipment"]] will be serialized if added
    route_shipments = relationship("Shipment", back_populates="shipment_route")

    # Mapped[List["RouteAudit"]]
    route_audits = relationship("RouteAudit", back_populates="audit_route")

    @validates("origin")
    def validate_origin(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("origin must be a non-empty string")
        return value

    @validates("destination")
    def validate_destination(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("destination must be a non-empty string")
        return value

    @validates("price")
    def validate_price(self, key, value):
        if isinstance(value, str):
            try:
                value = Decimal(value)
            except InvalidOperation as e:
                raise ValueError(f"Invalid price value: {value}") from e

        if not isinstance(value, Decimal):
            raise TypeError("price must be a Decimal or convertible to Decimal")

        if value < 0:
            raise ValueError("price must be non-negative")

        return value

    @validates("payroll_price")
    def validate_payroll_price(self, key, value):
        if isinstance(value, str):
            try:
                value = Decimal(value)
            except InvalidOperation as e:
                raise ValueError(f"Invalid payroll_price value: {value}") from e

        if not isinstance(value, Decimal):
            raise TypeError("payroll_price must be a Decimal or convertible to Decimal")

        if value < 0:
            raise ValueError("payroll_price must be non-negative")

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
    * payroll_price (float): price paid to drivers for the trip on this route.
    * deleted (bool): Indicates whether the route information is no longer valid.
    * modification_user (str): The user who last modified this route record.
    * modification_timestamp (TIMESTAMP): The time at which this route record was modified.
    """

    __tablename__ = "route_audit"

    audit_code: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    route_code: Mapped[int] = mapped_column(ForeignKey("route.route_code"))
    origin: Mapped[str] = mapped_column(String(100))
    destination: Mapped[str] = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    payroll_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    deleted: Mapped[bool] = mapped_column()
    modification_user: Mapped[str] = mapped_column(String(100))
    modification_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP)

    # Mapped["Route"]
    audit_route = relationship("Route", back_populates="route_audits")
