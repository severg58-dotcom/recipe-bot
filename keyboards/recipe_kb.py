"""Клавиатура карточки рецепта."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Префиксы callback-data для inline-кнопок
CALLBACK_ADD_FAVORITE_PREFIX = "recipe:add:"
CALLBACK_NEXT_RANDOM = "recipe:next"


def recipe_card(recipe_id: str, is_favorite: bool = False) -> InlineKeyboardMarkup:
    """Кнопки под сообщением рецепта.

    :param recipe_id: id рецепта из API (нужен для сохранения в избранное).
    :param is_favorite: рецепт уже в избранном -> кнопка сохранения меняется.
    """
    text = "✅ В избранном" if is_favorite else "⭐️ Сохранить"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=f"{CALLBACK_ADD_FAVORITE_PREFIX}{recipe_id}")],
            [InlineKeyboardButton(text="➡️ Другой рецепт", callback_data=CALLBACK_NEXT_RANDOM)],
        ]
    )
