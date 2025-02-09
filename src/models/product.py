from datetime import datetime
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
class Product(Base):
    """(Palabras/Productos) Represents a product within a product management system.

    Attributes:
    * product_code (int): A unique identifier for the product.
    * product_name (str): The name of the product.
    * deleted (bool): Indicates whether the product is retired or discontinued.
    * modification_user (str): The user who last modified this product record.
    * modification_timestamp (TIMESTAMP): The last modification time.
    """
    __tablename__ = "product"

    product_code: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(String(100))
    deleted: Mapped[bool] = mapped_column(server_default='0')
    modification_user: Mapped[str] = mapped_column(String(100))
    modification_timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=functions.current_timestamp(), onupdate=functions.current_timestamp())

    # Mapped[List["Shipment"]]
    product_shipments = relationship(
        "Shipment", back_populates="shipment_product")

    # Mapped[List["ProductAudit"]]
    product_audits = relationship(
        "ProductAudit", back_populates="audit_product")

    @validates('product_name')
    def validate_product_name(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("product_name must be a non-empty string")
        return value


@dataclass
class ProductAudit(Base):
    """(Palabras/Productos) Represents a product within a product management system.

    Attributes:
    * audit_code (int): Unique identifier for the audit.
    * product_code (int): foreign key identifier for the product.
    * product_name (str): The name of the product.
    * deleted (bool): Indicates whether the product is retired or discontinued.
    * modification_user (str): The user who last modified this product record.
    * audit_timestamp (TIMESTAMP): The time at which this route record was modified.
    * modification_timestamp (TIMESTAMP): The last modification time.
    """
    __tablename__ = "product_audit"

    audit_code: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True)
    product_code: Mapped[int] = mapped_column(
        ForeignKey('product.product_code'))
    product_name: Mapped[str] = mapped_column(String(100))
    deleted: Mapped[bool] = mapped_column()
    modification_user: Mapped[str] = mapped_column(String(100))
    modification_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP)

    # Mapped["Product"]
    audit_product = relationship("Product", back_populates="product_audits")

