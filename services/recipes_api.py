"""Клиент API рецептов.

API: TheMealDB (бесплатный, тестовый ключ "1", включён в API_BASE по умолчанию).
Документация: https://www.themealdb.com/api.php
База англоязычная, поэтому для русских запросов есть перевод через MyMemory.
"""

import logging
import re
from dataclasses import dataclass, field
from urllib.parse import urlencode

import httpx

from config import API_BASE

log = logging.getLogger(__name__)

REQUEST_TIMEOUT = 10.0  # секунд

_CYRILLIC = re.compile(r"[\u0400-\u04FF]")
_TRANSLATE_URL = "https://api.mymemory.translated.net/get"


@dataclass
class Recipe:
    """Модель рецепта, получаемая из API."""

    id: str
    title: str
    image_url: str
    category: str
    instructions: str
    area: str = ""
    youtube_url: str = ""
    ingredients: list[tuple[str, str]] = field(default_factory=list)  # (ингредиент, мера)


async def _request(path: str, **params: str) -> dict | None:
    """GET-запрос к API. Возвращает None при ошибке сети или пустом ответе."""
    url = f"{API_BASE}/{path}"
    if params:
        url += "?" + urlencode(params)
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError) as e:
        log.warning("Запрос к recipes API не удался: %s | %s", url, e)
        return None
    if not data or not data.get("meals"):
        return None
    return data


def _parse_meal(meal: dict) -> Recipe:
    """Собрать модель Recipe из словаря ответа API."""
    ingredients: list[tuple[str, str]] = []
    for i in range(1, 21):  # в полях API занумерованы strIngredient1..20
        name = (meal.get(f"strIngredient{i}") or "").strip()
        measure = (meal.get(f"strMeasure{i}") or "").strip()
        if name:
            ingredients.append((name, measure))

    return Recipe(
        id=meal.get("idMeal", ""),
        title=meal.get("strMeal", "").strip(),
        image_url=meal.get("strMealThumb", "") or "",
        category=meal.get("strCategory", "") or "",
        instructions=(meal.get("strInstructions", "") or "").replace("\r\n", "\n"),
        area=meal.get("strArea", "") or "",
        youtube_url=meal.get("strYouTube", "") or "",
        ingredients=ingredients,
    )


async def search_by_name(query: str) -> list[Recipe]:
    """Поиск рецептов по названию блюда."""
    query = query.strip()
    if not query:
        return []
    data = await _request("search.php", s=query)
    if data is None:
        return []
    return [_parse_meal(m) for m in data["meals"]]


def is_cyrillic(text: str) -> bool:
    """Есть ли в тексте кириллица (значит, запрос на русском)."""
    return bool(_CYRILLIC.search(text))


async def translate_to_english(text: str) -> str | None:
    """Перевести запрос ru -> en бесплатным сервисом MyMemory.

    Возвращает None, если перевод не удался — тогда стоит искать как есть.
    """
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(
                _TRANSLATE_URL, params={"q": text, "langpair": "ru|en"}
            )
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError) as e:
        log.warning("Перевод не удался: %s", e)
        return None
    translated = (data.get("responseData") or {}).get("translatedText", "").strip()
    # MyMemory иногда отдаёт перевод с пометками/исходником — берём осмысленное
    if not translated or translated.upper() == text.upper():
        return None
    return translated


async def search_recipes(query: str) -> tuple[list[Recipe], str]:
    """Умный поиск: русский запрос переводится на английский.

    Если перевод целой фразы не дал результатов — ищем по отдельным словам.
    Возвращает (список рецептов, пояснение о переводе).
    """
    query = query.strip()
    if not query:
        return [], ""

    if not is_cyrillic(query):
        return await search_by_name(query), ""

    # 1) переводим цельную фразу
    translated = await translate_to_english(query)
    if translated:
        recipes = await search_by_name(translated)
        if recipes:
            return recipes, f"🔁 Перевод: <i>{translated}</i>"

    # 2) фраза не нашлась — пробуем по одному слову (берём первое с результатом)
    for word in query.split()[:4]:
        if not is_cyrillic(word):
            continue
        word_en = await translate_to_english(word)
        if not word_en:
            continue
        recipes = await search_by_name(word_en)
        if recipes:
            return recipes, (
                f"🔁 Перевод: <i>{word_en}</i> (по слову «{word}»)"
            )

    # 3) последний шанс — искать как есть
    return await search_by_name(query), ""


async def get_random() -> Recipe | None:
    """Случайный рецепт (для кнопки «Другой рецепт»)."""
    data = await _request("random.php", k="1")
    if data is None:
        return None
    return _parse_meal(data["meals"][0])


async def get_by_id(recipe_id: str) -> Recipe | None:
    """Рецепт по id (пригодится для избранного)."""
    data = await _request("lookup.php", i=recipe_id)
    if data is None:
        return None
    return _parse_meal(data["meals"][0])
