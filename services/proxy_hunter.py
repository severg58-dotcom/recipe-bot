"""Охота за живым прокси: автоподбор при смерти текущего.

Работа сбоит с бесплатными SOCKS5/HTTP — бот вызывает этого помощника,
когда текущий прокси перестал отвечать, и заменяет его на свежий.
"""

import asyncio
import logging
import random
import re
from pathlib import Path

import httpx

from config import ENV_PATH, PROXY_URL as CONFIG_PROXY_URL

log = logging.getLogger(__name__)

LISTS = [
    ("socks5://", "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt"),
    ("http://", "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"),
]
GET_ME = "https://api.telegram.org/bot1/getMe"


async def proxy_alive(proxy_url: str, timeout: float = 12.0) -> bool:
    """Достучался ли прокси до api.telegram.org (любой HTTP-ответ = да)."""
    try:
        async with httpx.AsyncClient(proxy={"all://": proxy_url}, timeout=timeout) as client:
            resp = await client.get(GET_ME)
            return resp.status_code == 404  # фиктивный токен "1" -> 404 = транспорт работает
    except Exception:  # noqa: BLE001
        return False


async def find_stable_proxy(max_packets: int = 8) -> str | None:
    """Найти живой прокси (двойная проверка). Возвращает 'socks5://ip:port' или None."""
    socks5: list[str] = []
    http: list[str] = []
    async with httpx.AsyncClient(timeout=20) as fetcher:
        for scheme, url in LISTS:
            try:
                lines = [
                    l.strip() for l in (await fetcher.get(url)).text.splitlines() if ":" in l
                ]
                (socks5 if scheme.startswith("socks") else http).extend(scheme + l for l in lines)
            except Exception as e:  # noqa: BLE001
                log.warning("Список прокси недоступен: %s", url)

    # Подсеть, которая чаще всего жива, — впереди
    subnet = [p for p in socks5 if "45.74.31." in p]
    random.shuffle(subnet)
    random.shuffle(socks5)
    random.shuffle(http)
    candidates = subnet[:40] + socks5[:40] + http[:30]

    for i in range(0, len(candidates), 15):
        batch = candidates[i : i + 15]
        results = await asyncio.gather(
            *(_check(proxy) for proxy in batch)
        )
        for proxy, alive in zip(batch, results):
            if alive and await _check(proxy):  # двойная проверка
                log.info("Найден рабочий прокси: %s", proxy)
                return proxy
        if i // 15 >= max_packets:
            break
    return None


async def _check(proxy: str) -> bool:
    try:
        async with asyncio.timeout(9):
            return await proxy_alive(proxy, timeout=8)
    except Exception:  # noqa: BLE001
        return False


def write_env_proxy(proxy_url: str) -> None:
    """Обновить PROXY_URL в .env, чтобы перезапуск бота стартовал с него же."""
    try:
        lines = [
            l
            for l in ENV_PATH.read_text(encoding="utf-8").splitlines()
            if not l.startswith("PROXY_URL=")
        ]
        lines.append(f"PROXY_URL={proxy_url}")
        ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError as e:
        log.warning("Не удалось обновить .env: %s", e)


async def hunt_new_proxy() -> str | None:
    """Найти свежий прокси и записать его в .env. Возвращает прокси или None."""
    proxy = await find_stable_proxy()
    if proxy:
        write_env_proxy(proxy)
    return proxy
