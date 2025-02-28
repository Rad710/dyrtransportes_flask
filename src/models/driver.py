from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import validates
from sqlalchemy.sql import functions

from .base import Base


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
    * modification_user (str): The user who last modified the driver record (not nullable, up to 100 characters).
    * modification_timestamp (TIMESTAMP): The last modification time.
    """

    __tablename__ = "driver"

    driver_code: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    driver_id: Mapped[str] = mapped_column(String(100))
    driver_name: Mapped[str] = mapped_column(String(100))
    driver_surname: Mapped[Optional[str]] = mapped_column(String(100))
    truck_plate: Mapped[str] = mapped_column(String(100))
    trailer_plate: Mapped[Optional[str]] = mapped_column(String(100))
    # used to deactivate account
    deleted: Mapped[bool] = mapped_column(server_default="0")
    modification_user: Mapped[str] = mapped_column(String(100))
    modification_timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=functions.current_timestamp(),
        onupdate=functions.current_timestamp(),
    )

    # Mapped[List["DriverPayroll"]]
    driver_payrolls = relationship("DriverPayroll", back_populates="payroll_driver")

    # Mapped[List["Shipment"]]
    driver_shipments = relationship("Shipment", back_populates="shipment_driver")

    # Mapped[List["DriverAudit"]]
    driver_audits = relationship("DriverAudit", back_populates="audit_driver")

    @validates("driver_id")
    def validate_driver_id(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("driver_id must be a non-empty string")
        return value

    @validates("driver_name")
    def validate_driver_name(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("driver_name must be a non-empty string")
        return value

    @validates("driver_surname")
    def validate_driver_surname(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("driver_surname must be a non-empty string")
        return value

    @validates("truck_plate")
    def validate_truck_plate(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("truck_plate must be a non-empty string")
        return value

    @validates("trailer_plate")
    def validate_trailer_plate(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("trailer_plate must be a non-empty string")
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
    * modification_user (str): The user who last modified the driver record (not nullable, up to 100 characters).
    * modification_timestamp (TIMESTAMP): The last modification time.
    """

    __tablename__ = "driver_audit"

    audit_code: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    driver_code: Mapped[int] = mapped_column(ForeignKey("driver.driver_code"))
    driver_id: Mapped[str] = mapped_column(String(100))
    driver_name: Mapped[str] = mapped_column(String(100))
    driver_surname: Mapped[Optional[str]] = mapped_column(String(100))
    truck_plate: Mapped[str] = mapped_column(String(100))
    trailer_plate: Mapped[Optional[str]] = mapped_column(String(100))
    deleted: Mapped[bool] = mapped_column()
    modification_user: Mapped[str] = mapped_column(String(100))
    modification_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP)

    # Mapped["Driver"]
    audit_driver = relationship("Driver", back_populates="driver_audits")
