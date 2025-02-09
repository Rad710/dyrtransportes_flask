from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Optional
from dataclasses import dataclass

from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Numeric
from sqlalchemy import Date
from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from sqlalchemy.sql import functions


from .base import Base


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
    * modification_user (str): The user who created this payroll record.
    * modification_timestamp (TIMESTAMP): The last modification time.
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
    deleted: Mapped[bool] = mapped_column(server_default='0')
    modification_user: Mapped[str] = mapped_column(String(100))
    modification_timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=functions.current_timestamp(), onupdate=functions.current_timestamp())

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
    * modification_user (str): The user who created this payroll record.
    * modification_timestamp (TIMESTAMP): The last modification time.
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
    deleted: Mapped[bool] = mapped_column()
    modification_user: Mapped[str] = mapped_column(String(100))
    modification_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP)

    # Mapped["Shipment"]
    audit_shipment_expense = relationship(
        "ShipmentExpense", back_populates="shipment_expense_audits")
