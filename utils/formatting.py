"""Форматирование карточки рецепта для Telegram (HTML).

Telegram ограничивает подпись к фото 1024 символами — текст собирается
с динамическим бюджетом: инструкция подрезается так, чтобы caption влезал.
"""

import html
from textwrap import shorten

from services.recipes_api import Recipe

CAPTION_LIMIT = 1024  # жёсткий лимит Telegram на caption фото
_MIN_INSTRUCTIONS = 150  # минимум символов инструкции, ради которых готовим


def recipe_text(recipe: Recipe) -> str:
    """HTML-текст карточки: название, категория, ингредиенты, инструкция."""
    title = html.escape(recipe.title)
    meta = html.escape(" • ".join(filter(None, (recipe.category, recipe.area))))

    lines = [f"🍲 <b>{title}</b>"]
    if meta:
        lines.append(f"<i>{meta}</i>")

    if recipe.ingredients:
        lines.append("\n<b>Ингредиенты:</b>")
        for name, measure in recipe.ingredients[:15]:
            ing = html.escape(name)
            amount = html.escape(measure)
            lines.append(f"  • {ing}" + (f" — {amount}" if amount else ""))

    head = "\n".join(lines)

    video = ""
    if recipe.youtube_url:
        video = f'\n▶️ <a href="{html.escape(recipe.youtube_url, quote=True)}">Видео-рецепт</a>'

    label = "\n\n<b>Как готовить:</b>\n"

    # Бюджет под инструкцию: лимит минус всё остальное.
    # Ссылка на видео по заданию обязательна — не отбрасываем её,
    # при нехватке места сначала сильнее ужмётся инструкция (страховка ниже).
    width = CAPTION_LIMIT - len(head) - len(label) - len(video) - 20

    if recipe.instructions:
        instr = html.escape(
            shorten(recipe.instructions, width=max(_MIN_INSTRUCTIONS, width), placeholder=" …")
        )
    else:
        instr = ""

    text = head + label + instr + video

    # Страховка: html.escape мог немного раздуть текст — ужимаем инструкцию повторно
    if len(text) > CAPTION_LIMIT and recipe.instructions:
        excess = len(text) - CAPTION_LIMIT + 20
        instr = html.escape(
            shorten(
                recipe.instructions,
                width=max(60, width - excess),
                placeholder=" …",
            )
        )
        text = head + label + instr + video

    return text
