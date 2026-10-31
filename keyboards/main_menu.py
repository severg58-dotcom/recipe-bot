"""Клавиатуры общего меню."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.types.reply_keyboard_remove import ReplyKeyboardRemove

BTN_SEARCH = KeyboardButton(text="🔎 Поиск рецептов")
BTN_FAVORITES = KeyboardButton(text="⭐️ Мои рецепты")


def main_menu() -> ReplyKeyboardMarkup:
    """Главное меню: два основных действия."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [BTN_SEARCH],
            [BTN_FAVORITES],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие…",
    )


def remove_menu() -> ReplyKeyboardRemove:
    """Скрыть меню (например, во время ввода запроса)."""
    return ReplyKeyboardRemove()
