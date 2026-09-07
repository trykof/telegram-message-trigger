from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from telegram_message_trigger.db.base import Base


class Owner(Base):
    __tablename__ = "owners"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    business_connection_id: Mapped[str | None] = mapped_column(default=None)
    is_connected: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    rules: Mapped[list["Rule"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id"), index=True)
    case_sensitive: Mapped[bool] = mapped_column(default=False)
    whole_word: Mapped[bool] = mapped_column(default=False)
    reply_text: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(default=True)
    target_telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, default=None)
    target_label: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    owner: Mapped["Owner"] = relationship(back_populates="rules")
    triggers: Mapped[list["Trigger"]] = relationship(
        back_populates="rule", cascade="all, delete-orphan"
    )


class Trigger(Base):
    __tablename__ = "triggers"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("rules.id"), index=True)
    text: Mapped[str]

    rule: Mapped["Rule"] = relationship(back_populates="triggers")
