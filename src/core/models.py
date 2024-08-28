import uuid
import decimal
from datetime import datetime

from sqlalchemy import ForeignKey, TIMESTAMP, UUID, func, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import CheckConstraint
from typing_extensions import List, Any

from src.core.database import Base
from src.settings import get_settings

cfg = get_settings()


class UserModel(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, index=True, default=uuid.uuid4)

    username: Mapped[str] = mapped_column(String(100), nullable=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str] = mapped_column(String(50), nullable=True)
    tg_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    tg_url: Mapped[str] = mapped_column(String(100), nullable=True)
    tg_chat_id: Mapped[str] = mapped_column(String(50), nullable=True)
    is_bot: Mapped[bool] = mapped_column(default=False)

    country_id: Mapped[int] = mapped_column(
        ForeignKey('countries.id', onupdate='CASCADE', ondelete='SET DEFAULT'),
        nullable=True, default=None,
    )
    # server_default='1'
    country: Mapped["CountryModel"] = relationship(
        back_populates="users",
        uselist=False,
    )

    region_id: Mapped[int] = mapped_column(
        ForeignKey('regions.id', onupdate='CASCADE', ondelete='SET DEFAULT'),
        nullable=True, default=None,
    )
    # server_default='1'
    region: Mapped["RegionModel"] = relationship(
        back_populates="users",
        uselist=False,
    )

    total_capacity: Mapped[int] = mapped_column(default=0)
    total_boost_value: Mapped[int] = mapped_column(default=0, server_default='0')

    users_rating_position: Mapped[int] = mapped_column(nullable=True)
    capacity_rating_position: Mapped[int] = mapped_column(nullable=True)

    energy: Mapped[int] = mapped_column(default=cfg.energy_limit)
    boosts: Mapped[List["UserBoostModel"]] = relationship(
        back_populates="user",
        uselist=True
    )
    can_open_case: Mapped[bool] = mapped_column(default=False, nullable=True)

    enterprises_slots: Mapped[int] = mapped_column(
        default=cfg.enterprises_min_slots
    )
    enterprises: Mapped[List["UserEnterpriseModel"]] = relationship(
        back_populates="user",
        uselist=True,
    )

    game_balance: Mapped[int] = mapped_column(default=0)  # это ВВП
    donate_balance: Mapped[int] = mapped_column(default=0)
    token_balance: Mapped[decimal.Decimal] = mapped_column(default=0.0)

    stars_payments: Mapped["StarsPaymentModel"] = relationship(
        back_populates="user",
        uselist=True,
    )
    stars_refunds: Mapped["StarsRefundModel"] = relationship(
        back_populates="user",
        uselist=True,
    )

    referrer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('users.id', onupdate='CASCADE', ondelete='SET NULL'),
        nullable=True
    )
    referrals = relationship(
        'ReferralModel',
        back_populates='owner',
        foreign_keys="ReferralModel.owner_id"
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        onupdate=func.now(),
        server_default=func.now()
    )

    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    __table_args__ = (
        CheckConstraint(
            f'enterprises_slots <= {cfg.enterprises_max_slots}',
            name='check_enterprises_slots_max_value'
        ),
    )


class RefreshSessionModel(Base):
    __tablename__ = 'refresh_session'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    refresh_token: Mapped[uuid.UUID] = mapped_column(UUID, index=True)
    expires_in: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                 server_default=func.now())
    user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey(
        "users.id", ondelete="CASCADE"))



class StarsPaymentModel(Base):
    __tablename__ = 'stars_payments'

    # Unique identifier of the transaction: telegram_payment_charge_id
    id: Mapped[str] = mapped_column(primary_key=True, unique=True)

    # 'XTR' for payments in Telegram Stars
    currency: Mapped[str] = mapped_column(nullable=False)

    # Total price in the *smallest units* of the currency
    total_amount: Mapped[int] = mapped_column(nullable=False)

    provider_payment_charge_id: Mapped[str] = mapped_column(nullable=True)
    shipping_option_id: Mapped[str] = mapped_column(nullable=True)
    invoice_payload = mapped_column(JSONB, nullable=True)
    order_info = mapped_column(JSONB, nullable=True)

    tg_id: Mapped[str] = mapped_column(
        ForeignKey('users.tg_id', onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    user: Mapped["UserModel"] = relationship(
        back_populates="stars_payments",
        uselist=False,
        foreign_keys=[tg_id]
    )


class StarsRefundModel(Base):
    __tablename__ = 'stars_refunds'

    # Unique identifier of the transaction: telegram_payment_charge_id
    id: Mapped[str] = mapped_column(primary_key=True, unique=True)

    # 'XTR' for payments in Telegram Stars
    currency: Mapped[str] = mapped_column(nullable=False)

    # Total price in the *smallest units* of the currency
    total_amount: Mapped[int] = mapped_column(nullable=False)

    shipping_option_id: Mapped[str] = mapped_column(nullable=True)
    order_info = mapped_column(JSONB, nullable=True)

    tg_id: Mapped[str] = mapped_column(
        ForeignKey('users.tg_id', onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    user: Mapped["UserModel"] = relationship(
        back_populates="stars_refunds",
        uselist=False,
        foreign_keys=[tg_id]
    )


# class StarsTransactionModel(Base):
#     __tablename__ = 'stars_transactions'
#
#     # Unique identifier of the transaction.
#     id: Mapped[str] = mapped_column(primary_key=True, unique=True)
#
#     # Number of Telegram Stars transferred by the transaction
#     amount: Mapped[int] = mapped_column(nullable=False)
#
#     # Date the transaction was created in Unix time
#     date: Mapped[datetime] = mapped_column(nullable=False)
#
#     """
#     Источник входящей транзакции (например, пользователь покупает товары или услуги,
#     Fragment возвращает деньги за неудачный вывод средств). Только для входящих транзакций
#     """
#     source = mapped_column(JSONB, nullable=True)
#
#     """
#     Получатель исходящей транзакции (например, пользователь для возврата средств за покупку,
#     Fragment для вывода средств). Только для исходящих транзакций
#     """
#     receiver = mapped_column(JSONB, nullable=True)
#
#     tg_id: Mapped[str] = mapped_column(
#         ForeignKey('users.tg_id', onupdate="CASCADE", ondelete="CASCADE"),
#         nullable=False
#     )
#
#     created_at: Mapped[datetime] = mapped_column(
#         TIMESTAMP(timezone=True),
#         server_default=func.now()
#     )
#
#     user: Mapped["UserModel"] = relationship(
#         back_populates="stars_transactions",
#         uselist=False,
#         foreign_keys=[tg_id]
#     )


class ReferralLevelModel(Base):
    __tablename__ = 'referral_levels'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    level: Mapped[int] = mapped_column(nullable=False, default=1)
    commision_rate: Mapped[float] = mapped_column()


class ReferralModel(Base):
    __tablename__ = 'user_referrals'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('users.id', onupdate="CASCADE", ondelete="CASCADE")
    )
    referral_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('users.id', onupdate="CASCADE", ondelete="CASCADE")
    )

    level_id: Mapped[int] = mapped_column(
        ForeignKey('referral_levels.id', onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False, default=1
    )
    level = relationship(
        'ReferralLevelModel',
        foreign_keys=[level_id]
    )

    owner = relationship(
        'UserModel',
        back_populates='referrals',
        foreign_keys=[owner_id]
    )
