from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from sqlalchemy.sql import functions

from .base import Base


@dataclass
class DriverPayroll(Base):
    """
    (Liquidaciones) Represents a payroll record for a driver.
    Attributes:
    * payroll_code (int): Auto-generated unique identifier for the payroll record.
    * payroll_timestamp (TIMESTAMP): The time at which this route record was created.
    * driver_code (int): foreign key to driver information.
    * paid (bool): Indicates whether the payment associated with the shipment has been collected.
    * paid_timestamp (bool): Indicates when the payment associated with the shipment has been collected.
    * deleted (bool): Indicates whether the payment associated with the shipment has been deleted.
    * modification_user (str): The user who created this payroll record.
    * modification_timestamp (TIMESTAMP): The last modification time.
    """

    __tablename__ = "driver_payroll"

    payroll_code: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    payroll_timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=functions.now()
    )
    driver_code: Mapped[int] = mapped_column(ForeignKey("driver.driver_code"))
    paid: Mapped[bool] = mapped_column(server_default="0")
    paid_timestamp: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    deleted: Mapped[bool] = mapped_column(server_default="0")
    modification_user: Mapped[str] = mapped_column(String(100))
    modification_timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=functions.current_timestamp(),
        onupdate=functions.current_timestamp(),
    )

    # Mapped["Driver"]
    payroll_driver = relationship("Driver", back_populates="driver_payrolls")

    # Mapped[List["Shipment"]]
    driver_shipments = relationship(
        "Shipment", back_populates="shipment_driver_payroll"
    )

    # Mapped[List["ShipmentExpense"]]
    driver_payroll_shipment_expenses = relationship(
        "ShipmentExpense", back_populates="shipment_expense_driver_payroll"
    )

    # Mapped[List["DriverPayrollAudit"]]
    driver_payroll_audits = relationship(
        "DriverPayrollAudit", back_populates="audit_driver_payroll"
    )


@dataclass
class DriverPayrollAudit(Base):
    """
    (Liquidaciones) Represents a payroll record for a driver. Audit Table
    Attributes:
    * audit_code (int): Unique identifier for the audit.
    * payroll_code (int): Auto-generated unique identifier for the payroll record.
    * payroll_timestamp (TIMESTAMP): The time at which this route record was created.
    * driver_code (int): foreign key to driver information.
    * paid (bool): Indicates whether the payment associated with the shipment has been collected.
    * paid_timestamp (bool): Indicates when the payment associated with the shipment has been collected.
    * deleted (bool): Indicates whether the payment associated with the shipment has been deleted.
    * modification_user (str): The user who created this payroll record.
    * modification_timestamp (TIMESTAMP): The last modification time.
    """

    __tablename__ = "driver_payroll_audit"

    audit_code: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    payroll_code: Mapped[int] = mapped_column(ForeignKey("driver_payroll.payroll_code"))
    payroll_timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=functions.now()
    )
    driver_code: Mapped[int] = mapped_column(ForeignKey("driver.driver_code"))
    paid: Mapped[bool] = mapped_column()
    paid_timestamp: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    deleted: Mapped[bool] = mapped_column()
    modification_user: Mapped[str] = mapped_column(String(100))
    modification_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP)

    audit_timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=functions.now()
    )

    # Mapped["DriverPayroll"]
    audit_driver_payroll = relationship(
        "DriverPayroll", back_populates="driver_payroll_audits"
    )
