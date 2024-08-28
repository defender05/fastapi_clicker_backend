from requests import JSONDecodeError
from typing_extensions import Any, Annotated


from fastapi import FastAPI, Request, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from contextlib import asynccontextmanager

from fastapi_utilities import add_timer_middleware
# from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.game_api.routes.user_routes import user_router
from src.game_api.routes.enterprise_routes import ent_router
from src.game_api.routes.stars_payment_routes import stars_payment_router
from src.game_api.routes.country_routes import country_router
from src.game_api.routes.boost_routes import boost_router
from src.game_api.routes.case_routes import case_router

from src.redis_queue import queue
from src.settings import get_settings
from loguru import logger as log

cfg = get_settings()
redis = queue.get_redis()
# scheduler = AsyncIOScheduler()

if cfg.run_type != 'dev':
    from src.telegram.bot import bot, dp, start_telegram, end_telegram
    from aiogram.types import Update


@asynccontextmanager
async def lifespan(application: FastAPI):
    log.info("🚀 Starting FastAPI application")
    log.info(f"Run type: {cfg.run_type}")
    await queue.get_broker().start()
    if cfg.run_type != 'dev':
        log.info("🚀 Telegram bot starting")
        await start_telegram()

    yield

    await queue.get_broker().close()
    if cfg.run_type != 'dev':
        log.info("⛔ Telegram bot stopping")
        await end_telegram()

    log.info("⛔ Stopping FastAPI application")


app = FastAPI(
    title="CountryBalls API",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    root_path="/api/v1",
    # docs_url="/docs",
    # redoc_url="/redoc",
    # openapi_url="/openapi.json"
)
add_timer_middleware(app, show_avg=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://frontend:3000",
    ],
    allow_credentials=True,
    allow_methods=[
        "GET", "POST", "OPTIONS", "DELETE", "PATCH", "PUT"
    ],
    allow_headers=[
        "Content-Type",
        "Set-Cookie",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Origin",
        "Authorization"
    ],
)
# app.mount("/static", StaticFiles(directory="./web/static"), name="static")
# templates = Jinja2Templates(directory="./web/templates")
app.include_router(user_router)
app.include_router(stars_payment_router)
app.include_router(ent_router)
app.include_router(country_router)
app.include_router(boost_router)
app.include_router(case_router)


@app.get("/")
def root():
    return 'Hello World!'


@app.post(cfg.webhook_path)
async def bot_webhook(
        request: Request,
        x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None
) -> dict:
    """ Register webhook endpoint for telegram bot"""
    try:
        payload = await request.body()
        if not payload:
            raise HTTPException(status_code=400, detail="Empty payload")

        if x_telegram_bot_api_secret_token != cfg.tg_secret_token:
            if cfg.debug:
                log.error(f"Wrong secret token ! : {x_telegram_bot_api_secret_token}")
            return {"status": "error", "message": "Wrong secret token!"}

        update = Update.model_validate(await request.json(), context={"bot": bot})
        await dp.feed_update(bot, update)
        return {'status': 'ok'}
    except JSONDecodeError:
        return {'status': 'error', 'message': 'Invalid JSON'}
    except HTTPException as e:
        if cfg.debug:
            log.error(f"Ошибка вебхука: {e.detail}")
        return {'status': 'error', 'message': e.detail}



if __name__ == "__main__":
    # только для локального тестирования
    import uvicorn
    uvicorn.run('main:app')
