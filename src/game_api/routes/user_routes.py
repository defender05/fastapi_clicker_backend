import uuid
from typing import Optional, List, Any

from fastapi import Request, APIRouter, Header, Depends, HTTPException, status
from fastapi.responses import ORJSONResponse
from pydantic import Field

from src.core.enums import SortType, RatingType
from src.core.schemas import Pagination
from src.game_api.schemas.user_referral_schemas import UserReferralCreate, UserReferral
from src.game_api.schemas.user_schemas import (Tap, User, UserCreate,
                                               UserUpdate, UserBalanceUpdate)
from src.game_api.services.user_service import UserService

from src.redis_queue import queue
from src.settings import get_settings

cfg = get_settings()
broker = queue.get_broker()
redis = queue.get_redis()


user_router = APIRouter(tags=["Users"], prefix="/user")

if cfg.run_type != 'dev':
    from src.telegram.bot import bot
    from aiogram.utils.deep_linking import create_start_link
    from aiogram.types import Message



@user_router.get("/check/{tg_id}")
async def check_user_by_telegram_id(tg_id: str) -> User | str:
    """
    Проверка существования юзера по telegram id.\n
    """
    user = await UserService.check_user_by_telegram_id(tg_id)
    return user


# @user_router.post("/create")
# async def create_user(user: UserCreate = Depends(UserCreate)) -> Optional[User]:
#     """
#     Создание нового пользователя с проверкой его наличия
#     """
#     new_user = await UserService.create_user(user)
#     return new_user


# @user_router.get("/list")
# async def get_users(
#         pag: Pagination = Depends(Pagination),
#         sort_type: str = SortType.ASC,
# ) -> list[User]:
#     """
#     Получение списка всех пользователей с пагинацией\n
#     sort_type - тип сортировки: ASC или DESC
#     """
#     users = await UserService.get_users(
#         offset=pag.offset, limit=pag.limit, order_by='id', sort_type=sort_type)
#     return users


@user_router.get("/me")
async def get_user_by_telegram_id(tg_id: str) -> Any:
    """
    Получение пользователя по telegram id
    """
    user = await UserService.get_user_by_telegram_id(tg_id)
    return ORJSONResponse(content=user)


@user_router.get("/getReflink")
async def get_referral_link(tg_id: str) -> str:
    """
    Получение реферальной ссылки пользователя по telegram id
    """
    # user = await UserService.get_reflink_by_telegram_id(tg_id)
    # link = f"https://t.me/{cfg.bot_username}/{cfg.webapp_username}/start={tg_id}"
    reflink = await create_start_link(
        bot=bot,
        payload=tg_id,
        encode=False
    )
    return reflink


@user_router.patch("/update")
async def update_user_by_telegram_id(
        tg_id: str,
        user: UserUpdate = Depends(UserUpdate)
) -> Any:
    """
    Обновление данных пользователя по telegram id
    """
    updated_user = await UserService.update_user_by_telegram_id(
        tg_id=tg_id,
        user_update=user,
    )
    return ORJSONResponse(content=updated_user)


@user_router.post("/updateGameBalance")
async def update_game_balance(
        balance: UserBalanceUpdate = Depends(UserBalanceUpdate)
) -> dict:
    """
    Обновление баланса игровой валюты юзера.\n\n

    Входные параметры:\n
    current_tap_count - текущее значение счетчика тапов, которое сделал юзер \n\n

    Как вызывать этот метод?
    Нужно на фронте создать таймер, который будет отсчитывать 60 сек после тапа\n
    и вызывать этот метод. Если 60 сек не прошло, а юзер снова тапнул, то таймер сбрасывается \n
    и начинает отсчет снова.
    """
    # tap_count = await redis.get(tg_id)
    res = await UserService.update_game_balance(
        tg_id=balance.tg_id, new_tap_count=balance.current_tap_count)
    return res


@user_router.get("/getReferralStats")
async def get_referrals_stats_by_telegram_id(
        tg_id: str,
) -> Any:
    """
    Получение статистики по рефералам юзера\n
    """
    stat = await UserService.get_referral_stats(
        tg_id=tg_id,
    )
    return ORJSONResponse(content=stat)


@user_router.get("/rating")
async def get_rating(rating_type: RatingType, pag: Pagination = Depends(Pagination)):
    """
    Получение рейтинга по юзерам для gdp и производительности\n
    rating_type: str = "gdp or capacity"
    """
    res = []
    if rating_type == "gdp":
        res = await UserService.get_gdp_rating(offset=pag.offset, limit=pag.limit)
    else:
        res = await UserService.get_capacity_rating(offset=pag.offset, limit=pag.limit)
    return res
