"""Точка входа: запуск бота локально и на хостинге.

Локально (Windows): если задан PROXY_URL — цикл «поллинг + наблюдатель» сам
лечит умирающие бесплатные прокси. На хостинге (Render) PROXY_URL пуст,
бот работает напрямую, а на $PORT поднимается мини-HTTP-сервер здоровья —
Render требует открытый порт, а UptimeRobot пингует его, чтобы сервис не спал.
"""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode

from config import BOT_TOKEN, PROXY_URL
from handlers import favorites, recipe_actions, search, start
from services import database, proxy_hunter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("bot")

PROXY_CHECK_INTERVAL = 45  # секунд между проверками прокси


def build_bot(proxy: str | None) -> Bot:
    """Собрать бота (новая сессия = новый прокси)."""
    session = AiohttpSession(proxy=proxy) if proxy else None
    return Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def build_dispatcher() -> Dispatcher:
    """Диспетчер с роутерами. Создаётся один раз — роутеры нельзя переприкреплять."""
    dp = Dispatcher()
    dp.include_routers(
        recipe_actions.router,
        search.router,
        favorites.router,
        start.router,
    )
    return dp


async def watchdog(proxy: str | None) -> None:
    """Раз в PROXY_CHECK_INTERVAL секунд проверяет живость прокси.

    Завершение корутины = сигнал, что прокси мёртв (или связь потеряна).
    """
    while True:
        await asyncio.sleep(PROXY_CHECK_INTERVAL)
        alive = await proxy_hunter.proxy_alive(proxy) if proxy else True
        if not alive:
            log.warning("Прокси мёртв: %s — запускаю поиск нового", proxy)
            return
        log.debug("Прокси жив: %s", proxy)


async def polling_cycle(proxy: str | None, dp: Dispatcher) -> None:
    """Один цикл поллинга: работает, пока прокси жив и нет фатальной ошибки."""
    bot = build_bot(proxy)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:  # noqa: BLE001 — не смертельно, поллинг и так сбросит
        log.warning("delete_webhook: %s", e)

    poll_task = asyncio.create_task(dp.start_polling(bot), name="polling")
    watch_task = asyncio.create_task(watchdog(proxy), name="watchdog")

    try:
        done, _pending = await asyncio.wait(
            {poll_task, watch_task}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in done:
            exc = task.exception() if not task.cancelled() else None
            if exc:
                raise exc
            log.warning("Задача %s завершилась — переподключаюсь", task.get_name())
    finally:
        for task in (poll_task, watch_task):
            if not task.done():
                task.cancel()
        await asyncio.gather(poll_task, watch_task, return_exceptions=True)
        await bot.session.close()


async def start_health_server() -> None:
    """Мини HTTP-сервер для хостинга: Render шлёт проверки на $PORT.

    Локально (PORT не задан) не поднимается. Работает в фоне того же event loop.
    """
    port = int(os.getenv("PORT", "0"))
    if not port:
        log.info("PORT не задан — сервер здоровья не нужен (локальный запуск)")
        return

    from aiohttp import web

    async def ok(_request: web.Request) -> web.Response:
        return web.Response(text="Recipe bot is running")

    app = web.Application()
    app.router.add_get("/", ok)
    app.router.add_get("/healthz", ok)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", port).start()
    log.info("Сервер здоровья слушает порт %s", port)


async def main() -> None:
    database.init_db()
    await start_health_server()
    log.info("Бот стартует…")

    proxy: str | None = PROXY_URL or None
    dp = build_dispatcher()

    while True:
        try:
            # Свежий прокси или текущий — проверяем заранее, чтобы не ждать таймаутов
            if proxy and not await proxy_hunter.proxy_alive(proxy):
                log.warning("Текущий прокси недоступен, ищу новый…")
                proxy = await proxy_hunter.hunt_new_proxy() or proxy
            elif not proxy:
                log.info("PROXY_URL пуст — работаю напрямую (хостинг/прямой доступ)")

            await polling_cycle(proxy, dp)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:  # noqa: BLE001 — всё чиним и идём дальше
            log.error("Цикл поллинга упал: %s: %s", type(e).__name__, e)

        # Охота за прокси имеет смысл только там, где он нужен (блокированная сеть)
        if proxy:
            fresh = await proxy_hunter.hunt_new_proxy()
            proxy = fresh or proxy
        await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Остановлено пользователем")
