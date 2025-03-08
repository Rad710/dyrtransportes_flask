from datetime import datetime
from datetime import date
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
class ShipmentPayroll(Base):
    """
    (Planillas) Represents a payroll record for a shipment.
    Attributes:
    * payroll_code (int): Auto-generated unique identifier for the payroll record.
    * payroll_timestamp (TIMESTAMP): The time at which this route record was created.
    * collected (bool): Indicates whether the payment associated with the shipment has been collected.
    * deleted (bool): Indicates whether the payment associated with the shipment has been deleted.
    * modification_user (str): The user who created this payroll record.
    * modification_timestamp (TIMESTAMP): The last modification time.
    """

    __tablename__ = "shipment_payroll"

    payroll_code: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    payroll_timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=functions.now()
    )
    collected: Mapped[bool] = mapped_column(server_default="0")
    collection_timestamp: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    deleted: Mapped[bool] = mapped_column(server_default="0")
    modification_user: Mapped[str] = mapped_column(String(100))
    modification_timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=functions.current_timestamp(),
        onupdate=functions.current_timestamp(),
    )

    # Mapped[List["Shipment"]]
    payroll_shipments = relationship("Shipment", back_populates="shipment_payroll")

    # Mapped[List["ShipmentPayrollAudit"]]
    shipment_payroll_audits = relationship(
        "ShipmentPayrollAudit", back_populates="audit_shipment_payroll"
    )

    @validates("payroll_timestamp")
    def validate_payroll_timestamp(self, key, value):
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, "%a, %d %b %Y %H:%M:%S %Z")
            except ValueError as e:
                raise ValueError(
                    f"Invalid payroll_timestamp: {value}. Expected format: 'Day, DD Mon YYYY HH:MM:SS GMT'"
                ) from e

        if not isinstance(value, datetime) or value is None:
            raise ValueError("payroll_timestamp must be of type datetime")

        return value

    @validates("collection_timestamp")
    def validate_collection_timestamp(self, key, value):
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, "%a, %d %b %Y %H:%M:%S %Z")
            except ValueError as e:
                raise ValueError(
                    f"Invalid collection_timestamp: {value}. Expected format: 'Day, DD Mon YYYY HH:MM:SS GMT'"
                ) from e

        if value is not None and not isinstance(value, datetime):
            raise ValueError("collection_timestamp must be of type datetime")

        return value


@dataclass
class ShipmentPayrollAudit(Base):
    """
    (Planillas) Represents a payroll record for a shipment. Audit Table
    Attributes:
    * audit_code (int): Unique identifier for the audit.
    * payroll_code (int): Auto-generated unique identifier for the payroll record.
    * payroll_timestamp (TIMESTAMP): The time at which this route record was created.
    * collected (bool): Indicates whether the payment associated with the shipment has been collected.
    * deleted (bool): Indicates whether the payment associated with the shipment has been deleted.
    * modification_user (str): The user who created this payroll record.
    * audit_timestamp (TIMESTAMP): The time at which this route record was modified.
    * modification_timestamp (TIMESTAMP): The last modification time.
    """

    __tablename__ = "shipment_payroll_audit"

    audit_code: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    payroll_code: Mapped[int] = mapped_column(
        ForeignKey("shipment_payroll.payroll_code")
    )
    payroll_timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=functions.now()
    )
    collected: Mapped[bool] = mapped_column()
    collection_timestamp: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    deleted: Mapped[bool] = mapped_column()
    modification_user: Mapped[str] = mapped_column(String(100))
    modification_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP)

    # Mapped["ShipmentPayroll"]
    audit_shipment_payroll = relationship(
        "ShipmentPayroll", back_populates="shipment_payroll_audits"
    )
