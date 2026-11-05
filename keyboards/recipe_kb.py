"""Клавиатура карточки рецепта."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Префиксы callback-data для inline-кнопок
CALLBACK_ADD_FAVORITE_PREFIX = "recipe:add:"
CALLBACK_NEXT_RANDOM = "recipe:next"
CALLBACK_RATE_PREFIX = "rate:"


def recipe_card(
    recipe_id: str, is_favorite: bool = False, rating: int = 0
) -> InlineKeyboardMarkup:
    """Кнопки под сообщением рецепта.

    :param recipe_id: id рецепта из API (нужен для сохранения в избранное).
    :param is_favorite: рецепт уже в избранном -> кнопка сохранения меняется.
    :param rating: текущий рейтинг 0..5 (0 — не оценён, звёзды без отметки).
    """
    text = "✅ В избранном" if is_favorite else "⭐️ Сохранить"

    # Ряд из 5 звёзд для оценки блюда (по нажатию рецепт сохранится, если ещё не был)
    stars = [
        InlineKeyboardButton(
            text=("✅ " if n == rating else "⭐ ") + str(n),
            callback_data=f"{CALLBACK_RATE_PREFIX}{recipe_id}:{n}",
        )
        for n in range(1, 6)
    ]

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=f"{CALLBACK_ADD_FAVORITE_PREFIX}{recipe_id}")],
            stars,
            [InlineKeyboardButton(text="➡️ Другой рецепт", callback_data=CALLBACK_NEXT_RANDOM)],
        ]
    )
