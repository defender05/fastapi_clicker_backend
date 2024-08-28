import uuid
from typing_extensions import Annotated, Optional
from pydantic import BaseModel, Field, StringConstraints

from src.settings import get_settings

cfg = get_settings()


def gen_user_id():
    return str(uuid.uuid4())


# Генерация уникального реферального кода из первых 6 символов UUID
def gen_referral_code():
    return str(uuid.uuid4().hex)[:6]


class Tap(BaseModel):
    tg_id: str


class UserBase(BaseModel):
    username: str
    first_name: str
    last_name: str
    tg_id: str
    tg_url: str
    tg_chat_id: str
    is_bot: bool
    country_id: Optional[int] = Field(None)
    region_id: Optional[int] = Field(None)
    total_capacity: Optional[int] = Field(0)
    user_rating_position: Optional[int] = Field(0)
    energy: Optional[int] = Field(cfg.energy_limit)
    enterprises_slots: Optional[int] = Field(cfg.enterprises_min_slots)
    game_balance: Optional[int] = Field(0)
    referrer_id: Optional[uuid.UUID] = None
    # donate_balance: int = Field(0)
    # token_balance: float = Field(0.0)
    # is_superuser: bool


class UserCreate(BaseModel):
    username: str
    first_name: str
    last_name: str
    tg_id: str
    tg_url: str
    tg_chat_id: str
    is_bot: bool
    country_id: Optional[int] = Field(None)
    region_id: Optional[int] = Field(None)
    referrer_id: Optional[str] = None
    # is_superuser: bool = Field(False)


# class UserAutoUpdate(BaseModel):
#     username: Optional[str] = Field(None)
#     first_name: Optional[str] = Field(None)
#     last_name: Optional[str] = Field(None)
#     tg_url: Optional[str] = Field(None)


class UserUpdate(BaseModel):
    # username: Optional[str] = Field(None)
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)
    tg_url: Optional[str] = Field(None)
    country_id: Optional[int] = Field(None)
    region_id: Optional[int] = Field(None)


class UserBalanceUpdate(BaseModel):
    tg_id: str
    current_tap_count: int = Field(ge=0, le=500),

# class UserUsernameUpdate(BaseModel):
#     username: Optional[str] = Field(None)
#
#
# class UserFirstNameUpdate(BaseModel):
#     first_name: Optional[str] = Field(None)
#
#
# class UserLastNameUpdate(BaseModel):
#     last_name: Optional[str] = Field(None)
#
#
# class UserEnterprisesSlotsUpdate(BaseModel):
#     enterprises_slots: Optional[int] = Field(None)


class User(UserBase):
    id: uuid.UUID

    class Config:
        from_attributes = True


# Рейтинг по юзерам
class UserRatingBase(BaseModel):
    user_id: uuid.UUID
    username: Optional[str] = Field(None)
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)
    tg_id: Optional[str] = Field(None)
    country_image_url: Optional[str] = Field(None)
    total: int


class UserRating(UserRatingBase):
    id: int

    class Config:
        from_attributes = True
