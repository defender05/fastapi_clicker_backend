from typing import Optional, Any

from fastapi import Request, APIRouter, Header, Depends
from pydantic import BaseModel, Field

from src.core.schemas import Pagination, StarsTransactionPagination
from src.game_api.schemas.stars_payment_schemas import StarsPayment, StarsPaymentCreate, \
    StarsInvoiceLinkCreate
from src.game_api.services.stars_payment_service import StarsPaymentService
from src.game_api.tg_payment import create_stars_payment_link, stars_transactions
from src.settings import get_settings

cfg = get_settings()

if cfg.run_type != 'dev':
    from src.telegram.bot import bot

stars_payment_router = APIRouter(prefix='/stars_payment', tags=["Stars payment"])


class Timeout(BaseModel):
    req_timeout: int = Field(default=100, ge=10)


@stars_payment_router.post("/getInvoiceLink")
async def get_invoice_link(
        link: StarsInvoiceLinkCreate = Depends(StarsInvoiceLinkCreate)
) -> str:
    """
    Возвращает ссылку для оплаты цифрового товара в telegram stars\n
    Источник: https://core.telegram.org/bots/api#createinvoicelink\n

    В payload нужно передать строку, полученную из словаря,  \n
    user_id - telegram id пользователя\n
    product_type - тип товара (boost, enterprise, case или slot)\n
    product_id - идентификатор товара (буста или предприятия)\n

    P.S: В случае покупки слотов, product_id нужно передать как пустую строку
    """
    pay_link = await create_stars_payment_link(bot, link)
    return pay_link


@stars_payment_router.post("/makeRefund")
async def make_refund(
        user_id: int,
        transaction_id: str
) -> Any:
    """
    Делаем рефанд потраченных старс обратно на счет пользователю\n
    !!!ВРЕМЕННАЯ РУЧКА ДЛЯ ТЕСТОВ!!!
    """
    refund = await bot.refund_star_payment(
        user_id=user_id,
        telegram_payment_charge_id=transaction_id,
        request_timeout=1000
    )
    return refund

# @star_order_router.post("/saveTransaction/{transaction_id}")
# async def save_stars_transaction(
#         order: StarsOrderCreate = Depends(StarsOrderCreate)
# ) -> StarsOrder:
#     """
#     Сохраняет транзакцию telegram stars в базу
#     """
#     trans = await StarsOrderService.create_order()
#     return trans


@stars_payment_router.get("/listStarsTransactions")
async def get_stars_transactions(
        pag: StarsTransactionPagination = Depends(StarsTransactionPagination),
        tr: Timeout = Depends(Timeout)
):
    """
    Получение списка транзакций пользователя в telegram stars\n
    req_timeout - время ожидания ответа в секундах
    """
    transactions = await stars_transactions(
        bot=bot,
        offset=pag.offset,
        limit=pag.limit,
        request_timeout=tr.req_timeout,
    )
    return transactions
