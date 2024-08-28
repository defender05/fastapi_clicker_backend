import random
from typing import Optional, Union, List, Any

from fastapi import HTTPException, status
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload, joinedload

from src.core.enums import SortType
from src.game_api.schemas.user_schemas import User
from src.core.models import UserModel
from src.game_api.dao import UserDAO, EnterpriseDAO
from src.core.database import db_helper as db

from src.game_api.utils import exception_and_log, log
from src.settings import get_settings

cfg = get_settings()


# class RepeatTasksService:
#     @classmethod
#     async def restore_energy(cls):
#         async with db.session_factory() as ses:
#             users = await UserDAO.find_all(ses)
#             if users is None:
#                 raise HTTPException(
#                     status_code=status.HTTP_404_NOT_FOUND,
#                     detail='Users not found'
#                 )
#
#         users = db.query(User).all()
#         now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
#
#         for user in users:
#             user_tz = pytz.timezone(user.timezone)
#             user_now = now_utc.astimezone(user_tz)
#
#             if user.last_energy_update is None or (user_now - user.last_energy_update).total_seconds() >= 24 * 3600:
#                 user.energy = 500
#                 user.last_energy_update = user_now
#
#         db.commit()