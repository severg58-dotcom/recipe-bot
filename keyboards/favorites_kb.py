"""Клавиатура списка избранных рецептов."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Префикс callback-data кнопок просмотра избранного
CALLBACK_VIEW_FAVORITE = "fav:view:"


def favorites_list(
    favorites: list[tuple[str, str]], max_buttons: int = 50
) -> InlineKeyboardMarkup:
    """Кнопчатый список: по кнопке на каждый избранный рецепт.

    :param favorites: список кортежей (recipe_id, title) из БД.
    :param max_buttons: Telegram допускает до 100 кнопок, берём запас.
    """
    buttons = [
        [InlineKeyboardButton(text=title, callback_data=f"{CALLBACK_VIEW_FAVORITE}{recipe_id}")]
        for recipe_id, title in favorites[:max_buttons]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
