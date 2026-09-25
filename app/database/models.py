from datetime import datetime

from sqlalchemy import BigInteger, DateTime, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Drug(Base):
    __tablename__ = "drugs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    unit: Mapped[str] = mapped_column(String(32), default="упак")
    price: Mapped[float] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SpekCounter(Base):
    __tablename__ = "spek_counter"

    id: Mapped[int] = mapped_column(primary_key=True)
    last_number: Mapped[int] = mapped_column(default=0)


class Spek(Base):
    __tablename__ = "speks"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column()
    user_id: Mapped[int] = mapped_column(BigInteger)
    user_name: Mapped[str] = mapped_column(String(255), default="")
    items_json: Mapped[str] = mapped_column(String, default="")
    total: Mapped[float] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    inn: Mapped[str] = mapped_column(String(32), index=True)
    firma: Mapped[str] = mapped_column(String(255))
    number: Mapped[str] = mapped_column(String(64))
    date: Mapped[str] = mapped_column(String(32))
    user_id: Mapped[int] = mapped_column(BigInteger)
    user_name: Mapped[str] = mapped_column(String(255), default="")
    pdf_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=True)
    pdf_name: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
