from src.core.models import (UserModel, ReferralModel, StarsPaymentModel,
                             CountryModel, RegionModel, EnterpriseModel,
                             EnterpriseTypeModel, UserEnterpriseModel,
                             BoostModel, UserBoostModel, CaseModel, GdpUserRatingModel, CapacityUserRatingModel,
                             RefreshSessionModel,
                             )
from src.game_api.schemas.auth_schemas import RefreshSessionCreate, RefreshSessionUpdate
from src.game_api.schemas.user_schemas import UserCreate, UserUpdate
from src.game_api.schemas.user_referral_schemas import UserReferralCreate, UserReferralUpdate
from src.game_api.schemas.stars_payment_schemas import StarsPayment, StarsPaymentCreate
from src.game_api.schemas.country_schemas import CountryCreate, CountryUpdate, RegionCreate, RegionUpdate
from src.game_api.schemas.enterprise_schemas import EnterpriseCreate, EnterpriseUpdate
from src.game_api.schemas.enterprise_schemas import EnterpriseTypeCreate, EnterpriseTypeUpdate
from src.game_api.schemas.enterprise_schemas import UserEnterpriseCreate, UserEnterpriseUpdate
from src.game_api.schemas.boost_schemas import BoostCreate, BoostUpdate, UserBoostCreate, UserBoostUpdate

from src.core.base_dao import BaseDAO


class RefreshSessionDAO(BaseDAO[RefreshSessionModel, RefreshSessionCreate, RefreshSessionUpdate]):
    model = RefreshSessionModel


class UserDAO(BaseDAO[UserModel, UserCreate, UserUpdate]):
    model = UserModel


class UserReferralDAO(BaseDAO[ReferralModel, UserReferralCreate, UserReferralUpdate]):
    model = ReferralModel


class GdpUserRatingDAO(BaseDAO[GdpUserRatingModel, None, None]):
    model = GdpUserRatingModel


class CapacityUserRatingDAO(BaseDAO[CapacityUserRatingModel, None, None]):
    model = CapacityUserRatingModel


class EnterpriseDAO(BaseDAO[EnterpriseModel, EnterpriseCreate, EnterpriseUpdate]):
    model = EnterpriseModel


class EnterpriseTypeDAO(BaseDAO[EnterpriseTypeModel, EnterpriseTypeCreate, EnterpriseTypeUpdate]):
    model = EnterpriseTypeModel


class UserEnterpriseDAO(BaseDAO[UserEnterpriseModel, UserEnterpriseCreate, UserEnterpriseUpdate]):
    model = UserEnterpriseModel

#
# class OrderDAO(BaseDAO[OrderModel, OrderCreate, None]):
#     model = OrderModel


class StarsPaymentDAO(BaseDAO[StarsPaymentModel, StarsPaymentCreate, None]):
    model = StarsPaymentModel


class CountryDAO(BaseDAO[CountryModel, CountryCreate, CountryUpdate]):
    model = CountryModel


class RegionDAO(BaseDAO[RegionModel, RegionCreate, RegionUpdate]):
    model = RegionModel


class BoostDAO(BaseDAO[BoostModel, BoostCreate, BoostUpdate]):
    model = BoostModel


class UserBoostDAO(BaseDAO[UserBoostModel, UserBoostCreate, UserBoostUpdate]):
    model = UserBoostModel


class CaseDAO(BaseDAO[CaseModel, None, None]):
    model = CaseModel
