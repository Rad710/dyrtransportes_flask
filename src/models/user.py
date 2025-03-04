from datetime import datetime

import uuid

from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import TIMESTAMP
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from sqlalchemy.sql import functions


from .base import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "user"

    user_id: Mapped[str] = mapped_column(
        String(36),  # UUID strings are 36 characters
        primary_key=True,
        default=generate_uuid,
    )

    email: Mapped[str] = mapped_column(String(100), unique=True)

    name: Mapped[str] = mapped_column(String(100))

    password_hash: Mapped[str] = mapped_column(Text)

    modification_user: Mapped[str] = mapped_column(String(100))

    modification_timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=functions.current_timestamp(),
        onupdate=functions.current_timestamp(),
    )

    __table_args__ = (
        UniqueConstraint(
            "email",
            name="unique_email_user",
        ),
    )


# TODO ADD USER AUDIT TABLE
