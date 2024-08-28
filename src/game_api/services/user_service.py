import string
import time
import random
import uuid

from typing import Optional, Union, List, Any

from fastapi import HTTPException, status
from sqlalchemy import select, update, func, asc, text, desc
from sqlalchemy.orm import selectinload, joinedload

from src.core.enums import SortType
from src.game_api.schemas.enterprise_schemas import UserEnterpriseCreate
from src.game_api.schemas.user_schemas import User, UserCreate, UserUpdate, UserRating
from src.game_api.schemas.user_referral_schemas import UserReferral, UserReferralCreate, UserReferralUpdate
from src.core.models import UserModel, ReferralModel, ReferralLevelModel, UserEnterpriseModel, EnterpriseModel, \
    GdpUserRatingModel, CapacityUserRatingModel
from src.game_api.dao import UserDAO, UserReferralDAO, UserEnterpriseDAO, EnterpriseDAO, CountryDAO, RegionDAO, \
    GdpUserRatingDAO, CapacityUserRatingDAO
from src.core.database import db_helper as db

from src.game_api.utils import exception_and_log, log
from src.settings import get_settings

cfg = get_settings()


class UserService:
    @classmethod
    async def check_user_by_telegram_id(cls, tg_id: str) -> User | str:
        async with db.session_factory() as session:
            user_exist = await UserDAO.find_one_or_none(session, tg_id=tg_id)
            if user_exist:
                return user_exist
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail='User not found')



    @classmethod
    async def create_user(cls, user: UserCreate) -> Optional[User]:
        async with db.session_factory() as ses:
            user_exist = await UserDAO.find_one_or_none(ses, tg_id=user.tg_id)
            owner = await UserDAO.find_one_or_none(ses, tg_id=user.referrer_id)
            if user_exist is None:
                if owner is None:
                    user.referrer_id = None
                else:
                    user.referrer_id = owner.id

                db_user = await UserDAO.add(ses, user)
                total_capacity = 0

                for i in range(1, 4):  # Добавляем 3 начальных предприятия юзеру
                    added_ents = await UserEnterpriseDAO.add(
                        ses,
                        UserEnterpriseCreate(
                            tg_id=user.tg_id,
                            enterprise_id=i,
                        )
                    )
                    current_ent = await EnterpriseDAO.find_one_or_none(ses, id=i)
                    total_capacity += current_ent.capacity
                    await ses.commit()

                db_user.total_capacity = total_capacity
                await ses.commit()

                if owner:
                    log.info(f'Owner:{owner}')
                    level = 1
                    current_referrer_id = owner.referrer_id

                    # Реализация многоуровневой реферальной системы
                    # Идем вверх по цепочке, пока не достигнем 10 уровня или юзера, которого никто не приглашал
                    while level <= 10:

                        # если такой юзер найден, добавляем одну запись и выходим из цикла
                        if current_referrer_id is None:
                            ref_obj = UserReferralCreate(
                                owner_id=owner.id,
                                referral_id=db_user.id,
                                level_id=1
                            )
                            log.success(f'Юзер найден. Добавляем одну запись:{ref_obj}')
                            new_ref = await UserReferralDAO.add(ses, obj_in=ref_obj)
                            await ses.commit()
                            break
                        else:   # если нет, добавляем записи (рефералов) для каждого юзера вверх по цепочке
                            log.warning(f'Юзер не найден. Идем вверх по цепочке')
                            next_owner = await UserDAO.find_one_or_none(ses, id=current_referrer_id)
                            if next_owner is None:
                                log.warning(f'Next owner не найден')
                                break

                            level += 1
                            ref_for_next_owner = UserReferralCreate(
                                owner_id=next_owner.id,
                                referral_id=db_user.id,
                                level_id=level
                            )
                            new_ref = await UserReferralDAO.add(ses, obj_in=ref_for_next_owner)
                            await ses.commit()
                            current_referrer_id = next_owner.referrer_id
                    else:
                        log.warning(f"Owner by uuid: {user.referrer_id} not found")


                return db_user
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with tg_id:{user.tg_id} already exists"
                )


    @classmethod
    async def get_users(
            cls,
            *filter,
            offset: int,
            limit: int,
            order_by: Optional[str],
            sort_type: str = SortType.ASC,
            **filter_by,
    ) -> list[User]:
        async with db.session_factory() as session:
            users = await UserDAO.find_all(
                session,
                *filter,
                offset=offset,
                limit=limit,
                order_by=order_by,
                sort_type=sort_type,
                **filter_by,
            )
            if users is None:
                exception_and_log(
                    cfg.debug,
                    status.HTTP_404_NOT_FOUND,
                    f"Users not found"
                )
            return [db_user for db_user in users]


    @classmethod
    async def get_user_by_id(cls, user_id: uuid.UUID) -> User:
        async with db.session_factory() as session:
            db_user = await UserDAO.find_one_or_none(session, id=user_id)
            if db_user is None:
                exception_and_log(
                    cfg.debug,
                    status.HTTP_404_NOT_FOUND,
                    f"User by user_id {user_id} not found"
                )
            return db_user

    @classmethod
    async def get_user_by_telegram_id(cls, tg_id: str) -> dict[str, Any]:
        async with db.session_factory() as ses:
            db_user = await UserDAO.find_one_or_none(ses, tg_id=tg_id)
            if db_user is None:
                exception_and_log(
                    cfg.debug,
                    status.HTTP_404_NOT_FOUND,
                    f"User by tg_id {tg_id} not found"
                )

            country = await CountryDAO.find_first(ses, id=db_user.country_id)
            region = await RegionDAO.find_first(ses, id=db_user.region_id)
            user_rating_gdp = await GdpUserRatingDAO.find_one_or_none(ses, user_id=db_user.id)
            user_rating_capacity = await CapacityUserRatingDAO.find_one_or_none(ses, user_id=db_user.id)

            rating_position = user_rating_gdp.id if user_rating_gdp else None
            capacity_rating_position = user_rating_capacity.id if user_rating_capacity else None

            output_dict: dict[str, Any] = {
                'id': str(db_user.id),
                'tg_id': db_user.tg_id,
                'username': db_user.username,
                'first_name': db_user.first_name,
                'last_name': db_user.last_name,
                'country': None,
                'region': None,
                'total_capacity': db_user.total_capacity,
                'total_boost_value': db_user.total_boost_value,
                'user_rating_position': rating_position,
                'capacity_rating_position': capacity_rating_position,
                'energy': db_user.energy,
                'game_balance': db_user.game_balance,
                'enterprises_slots': db_user.enterprises_slots,
                'can_open_case': db_user.can_open_case,
                'referrer_id': str(db_user.referrer_id),
            }

            if country:
                country_dict = dict(
                    id=country.id,
                    name=country.name,
                    description=country.description,
                    image_url=country.image_url,
                    total_gdp=country.total_gdp,
                )
                output_dict['country'] = country_dict

            if region:
                region_dict = dict(
                    id=region.id,
                    name=region.name,
                    country_id=region.country_id,
                )
                output_dict['region'] = region_dict

            return output_dict



    @classmethod
    async def update_user_by_telegram_id(
            cls,
            tg_id: str,
            user_update: UserUpdate,
    ) -> Any:
        async with db.session_factory() as ses:
            db_user = await UserDAO.find_one_or_none(ses, tg_id=tg_id)

            output_dict = {}

            if db_user is None:
                exception_and_log(
                    cfg.debug,
                    status.HTTP_404_NOT_FOUND,
                    f"User by tg_id {tg_id} not found"
                )
            else:
                # if user_update.username is not None:
                #     db_user.username = user_update.username
                #     output_dict['username'] = db_user.username
                if user_update.first_name is not None:
                    db_user.first_name = user_update.first_name
                    output_dict['first_name'] = db_user.first_name
                if user_update.last_name is not None:
                    db_user.last_name = user_update.last_name
                    output_dict['last_name'] = db_user.last_name
                if user_update.tg_url is not None:
                    db_user.tg_url = user_update.tg_url
                    output_dict['tg_url'] = db_user.tg_url
                if user_update.country_id is not None:
                    country = await CountryDAO.find_first(ses, id=user_update.country_id)
                    if country is None:
                        exception_and_log(
                            cfg.debug,
                            status.HTTP_404_NOT_FOUND,
                            f"Country_id {user_update.country_id} not found"
                        )

                    if user_update.country_id != db_user.country_id:
                        db_user.game_balance = int(db_user.game_balance / 2)

                    db_user.country_id = user_update.country_id
                    db_user.region_id = None

                    output_dict['country'] = dict(
                        id=country.id,
                        name=country.name,
                        description=country.description,
                        image_url=country.image_url,
                        total_gdp=country.total_gdp,
                    )

                if user_update.region_id is not None:
                    # region = await RegionDAO.find_first(ses, id=user_update.region_id)
                    if db_user.country_id is None:
                        exception_and_log(
                            cfg.debug,
                            status.HTTP_403_FORBIDDEN,
                            "You cannot update the region_id while the country_id is None"
                        )

                    region = await RegionDAO.find_first(
                        ses,
                        id=user_update.region_id,
                        country_id=db_user.country_id
                    )
                    if region is None:
                        exception_and_log(
                            cfg.debug,
                            status.HTTP_404_NOT_FOUND,
                            f"Region from country_id {user_update.country_id} not found"
                        )

                    if user_update.country_id is None and db_user.country_id == 1 and user_update.region_id != db_user.region_id:
                        db_user.game_balance = int(db_user.game_balance / 2)

                    db_user.region_id = user_update.region_id

                    output_dict['region'] = dict(
                        id=region.id,
                        name=region.name,
                        country_id=region.country_id,
                    )

                await ses.commit()
                return output_dict



    @classmethod
    async def update_game_balance(
            cls,
            tg_id: str,
            new_tap_count: int,
    ) -> dict:
        async with db.session_factory() as ses:
            db_user = await UserDAO.find_one_or_none(ses, tg_id=tg_id)
            if db_user is None:
                exception_and_log(
                    cfg.debug,
                    status.HTTP_404_NOT_FOUND,
                    f"User by tg_id {tg_id} not found"
                )
            else:

                if db_user.energy == 0:
                    return dict(
                        message="The energy is gone",
                        balance=db_user.game_balance
                    )

                current_tap_count = (cfg.energy_limit - db_user.energy)

                if new_tap_count < current_tap_count or new_tap_count < 0:
                    return dict(
                        message="""Вы не можете передать кол-во кликов меньше 0 или меньше,
                         чем уже сделали за сегодня""",
                        balance=db_user.game_balance
                    )

                if new_tap_count == 0:
                    return dict(
                        message="Make taps before update your balance",
                        balance=db_user.game_balance
                    )

                new_tap_count = new_tap_count - current_tap_count

                total_boost = db_user.total_boost_value if db_user.total_boost_value != 0 else 1
                composition = total_boost * db_user.total_capacity
                additional_value = composition / 100 if composition != 0 else 0

                if db_user.energy >= new_tap_count:
                    db_user.game_balance += ((db_user.total_capacity + additional_value) * 2) * new_tap_count
                    db_user.energy -= new_tap_count
                    await ses.commit()
                    return dict(
                        message="Balance successfully updated",
                        balance=db_user.game_balance
                    )
                else:
                    db_user.game_balance += ((db_user.total_capacity + additional_value) * 2) * db_user.energy
                    db_user.energy = 0
                    await ses.commit()
                    return dict(
                        message="Balance successfully updated",
                        balance=db_user.game_balance
                    )


    @classmethod
    async def buy_slot(
            cls,
            tg_id: str,
    ) -> dict[str, Any]:
        async with db.session_factory() as session:
            db_user = await UserDAO.find_one_or_none(session, tg_id=tg_id)
            if db_user is None:
                exception_and_log(
                    cfg.debug,
                    status.HTTP_404_NOT_FOUND,
                    f"User by tg_id {tg_id} not found"
                )
            else:
                if db_user.enterprises_slots < cfg.enterprises_max_slots:
                    db_user.enterprises_slots += 1
                    await session.commit()
                    if cfg.debug:
                        log.success("Слот успешно добавлен")
                    return dict(
                        message="Слот успешно добавлен",
                        number_of_slots=db_user.enterprises_slots
                    )
                else:
                    return dict(
                        message="Количество слотов уже достигло своего максимума",
                        number_of_slots=db_user.enterprises_slots
                    )

    @classmethod
    async def get_referral_stats(
            cls,
            tg_id: str,
    ) -> dict[str, Any]:
        async with db.session_factory() as ses:
            db_user = await UserDAO.find_one_or_none(ses, tg_id=tg_id)
            if db_user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User by tg_id {tg_id} not found"
                )

            stmt = (
                select(ReferralModel.level_id, func.count(ReferralModel.id))
                .filter(ReferralModel.owner_id == db_user.id)
                .group_by(ReferralModel.level_id)
            )
            res = await ses.execute(stmt)
            refferal_counts = res.all()
            if refferal_counts is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Referrals not found"
                )

            referral_stats = {item[0]: item[1] for item in refferal_counts}
            return dict(
                total_referrals=sum(referral_stats.values()),
                level_stats=referral_stats
            )


    @classmethod
    async def get_referrals(
            cls,
            offset: int,
            limit: int,
            order_by: Optional[str],
            sort_type: str = SortType.ASC,
    ) -> list[UserReferral]:
        async with db.session_factory() as session:
            referrals = await UserReferralDAO.find_all(
                session,
                offset=offset,
                limit=limit,
                order_by=order_by,
                sort_type=sort_type,
            )
            if referrals is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Referrals not found"
                )
            return [ref for ref in referrals]



    @classmethod
    async def create_or_update_user_by_telegram_id(cls, message, payload: Any):
        if message is None:
            return

        async with db.session_factory() as ses:
            try:
                tg_user_id = str(message.from_user.id)

                exist_user = await UserDAO.find_one_or_none(ses, tg_id=tg_user_id)
                owner_user = None

                if payload:
                    ref_id = str(payload)
                    # if ref_id == tg_user_id:
                    #     log.warning(f'Ошибка создания юзера: {tg_user_id} Нельзя пригласить самого себя')
                    #     return
                    owner_user = await UserDAO.find_one_or_none(ses, tg_id=ref_id)


                if exist_user is None:
                    if cfg.debug:
                        log.info(f'Пользователь {message.from_user.id} не найден. Создание...')

                    first_name = message.from_user.first_name
                    last_name = message.from_user.last_name

                    user_obj = UserCreate(
                        username=str(message.from_user.username),
                        first_name=str(first_name) if first_name else '',
                        last_name=str(last_name) if last_name else '',
                        tg_id=str(message.from_user.id),
                        tg_url=f'https://t.me/{message.from_user.username}',
                        tg_chat_id=str(message.chat.id),
                        is_bot=message.from_user.is_bot,
                        country_id=None,
                        region_id=None,
                        referrer_id=str(owner_user.id) if owner_user else None
                    )
                    new_user = await UserDAO.add(
                        ses,
                        user_obj
                    )

                    total_capacity = 0

                    for i in range(1, 4):  # Добавляем 3 начальных предприятия юзеру
                        added_ents = await UserEnterpriseDAO.add(
                            ses,
                            UserEnterpriseCreate(
                                tg_id=new_user.tg_id,
                                enterprise_id=i,
                            )
                        )
                        current_ent = await EnterpriseDAO.find_one_or_none(ses, id=i)
                        total_capacity += current_ent.capacity
                        await ses.commit()

                    new_user.total_capacity = total_capacity
                    await ses.commit()

                    if owner_user:
                        # log.info(f'Owner:{owner_user}')
                        level = 1
                        current_referrer_id = owner_user.referrer_id

                        # Реализация многоуровневой реферальной системы
                        # Идем вверх по цепочке, пока не достигнем 10 уровня или юзера, которого никто не приглашал
                        while level <= 10:

                            # если такой юзер найден, добавляем одну запись и выходим из цикла
                            if current_referrer_id is None:
                                ref_obj = UserReferralCreate(
                                    owner_id=owner_user.id,
                                    referral_id=new_user.id,
                                    level_id=1
                                )
                                log.success(f'Юзер найден. Добавляем одну запись:{ref_obj}')
                                new_ref = await UserReferralDAO.add(ses, obj_in=ref_obj)
                                await ses.commit()
                                break
                            else:  # если нет, добавляем записи (рефералов) для каждого юзера вверх по цепочке
                                log.warning(f'Юзер не найден. Идем вверх по цепочке')
                                next_owner = await UserDAO.find_one_or_none(ses, id=current_referrer_id)
                                if next_owner is None:
                                    log.warning(f'Next owner не найден')
                                    break

                                level += 1
                                ref_for_next_owner = UserReferralCreate(
                                    owner_id=next_owner.id,
                                    referral_id=new_user.id,
                                    level_id=level
                                )
                                new_ref = await UserReferralDAO.add(ses, obj_in=ref_for_next_owner)
                                await ses.commit()
                                current_referrer_id = next_owner.referrer_id
                        else:
                            log.warning(f"Owner by uuid: {owner_user.referrer_id} not found")


                    if new_user is not None:
                        await ses.commit()
                        if cfg.debug:
                            log.success(f'Новый пользователь успешно создан: {new_user}')
                    else:
                        if cfg.debug:
                            log.error(f'Ошибка создания пользователя:  {exist_user}')

                else:
                    log.info(f'Пользователь уже создан: \n{exist_user}\nОбновление данных пользователя...')
                    user_obj = UserUpdate(
                        # username=str(message.from_user.username),
                        first_name=str(message.from_user.first_name),
                        last_name=str(message.from_user.last_name),
                        tg_url=f'https://t.me/{message.from_user.username}' if message.from_user.username else None,
                    )
                    updated_user = await cls._auto_update_user(
                        session=ses,
                        current_user=exist_user,
                        user_update=user_obj,
                    )
                    cfg.debug and log.success(f'Пользователь успешно обновлен: {updated_user}')

            except Exception as e:
                if cfg.debug:
                    log.error(f'Ошибка при создании или обновлении пользователя: {e}')
                else:
                    log.error(f'Ошибка при создании или обновлении пользователя')

    @classmethod
    async def _auto_update_user(
            cls,
            session,
            current_user: User,
            user_update: UserUpdate
    ) -> UserUpdate:

        if user_update.username is not None:
            current_user.username = user_update.username
        if user_update.first_name is not None:
            current_user.first_name = user_update.first_name
        if user_update.last_name is not None:
            current_user.last_name = user_update.last_name
        if user_update.tg_url is not None:
            current_user.tg_url = user_update.tg_url

        await session.commit()
        return user_update


    @classmethod
    async def get_gdp_rating(
            cls,
            offset: int = 0,
            limit: int = 100,
    ) -> list[UserRating]:
        async with db.session_factory() as ses:
            stmt = (
                select(GdpUserRatingModel)
                .offset(offset)
                .limit(limit)
                .order_by(desc(text('total')))
            )

            result = await ses.execute(stmt)
            users = result.scalars().all()

            if users is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Users gdp rating not found"
                )
            return [user for user in users]

    @classmethod
    async def get_capacity_rating(
            cls,
            offset: int = 0,
            limit: int = 100,
    ) -> list[UserRating]:
        async with db.session_factory() as ses:
            stmt = (
                select(CapacityUserRatingModel)
                .offset(offset)
                .limit(limit)
                .order_by(desc(text('total')))
            )

            result = await ses.execute(stmt)
            users = result.scalars().all()

            if users is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Users capacity rating not found"
                )
            return [user for user in users]


    # @classmethod
    # async def delete_user(cls, user_id: uuid.UUID):
    #     async with db.session_factory() as session:
    #         db_user = await UserDAO.find_one_or_none(session, id=user_id)
    #         if db_user is None:
    #             raise HTTPException(
    #                 status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    #         await UserDAO.update(
    #             session,
    #             UserModel.id == user_id,
    #             {'is_active': False}
    #         )
    #         await session.commit()



    @classmethod
    async def update_user_from_superuser(cls, user_id: uuid.UUID, user: UserUpdate) -> User:
        async with db.session_factory() as session:
            db_user = await UserDAO.find_one_or_none(session, UserModel.id == user_id)
            if db_user is None:
                exception_and_log(
                    cfg.debug,
                    status.HTTP_404_NOT_FOUND,
                    f"User by user_id {user_id} not found"
                )

            user_update = await UserDAO.update(
                session,
                UserModel.id == user_id,
                obj_in=user)

            await session.commit()
            return user_update

    @classmethod
    async def delete_user_from_superuser(cls, user_id: uuid.UUID):
        async with db.session_factory() as session:
            db_user = await UserDAO.find_one_or_none(session, UserModel.id == user_id)
            if db_user is None:
                exception_and_log(
                    cfg.debug,
                    status.HTTP_404_NOT_FOUND,
                    f"User by user_id {user_id} not found"
                )
            else:
                try:
                    await UserDAO.delete(session, UserModel.id == user_id)
                    await session.commit()
                except Exception as e:
                    log.error(f"Error deleting user: {e}")










