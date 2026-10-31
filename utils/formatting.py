"""Форматирование карточки рецепта для Telegram (HTML)."""

import html
from textwrap import shorten

from services.recipes_api import Recipe

MAX_INSTRUCTIONS = 900  # символов — Telegram ограничивает caption 1024


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

    if recipe.instructions:
        trimmed = shorten(recipe.instructions, width=MAX_INSTRUCTIONS, placeholder=" …")
        lines.append(f"\n<b>Как готовить:</b>\n{html.escape(trimmed)}")

    if recipe.youtube_url:
        lines.append(f'\n▶️ <a href="{html.escape(recipe.youtube_url, quote=True)}">Видео-рецепт</a>')

    return "\n".join(lines)
