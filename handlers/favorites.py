"""Список избранных рецептов и просмотр рецепта по кнопке."""

import html
import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from keyboards.favorites_kb import CALLBACK_VIEW_FAVORITE, favorites_list
from keyboards.main_menu import main_menu
from keyboards.recipe_kb import recipe_card
from services import database
from services.recipes_api import Recipe, get_by_id
from utils.formatting import recipe_text

router = Router(name="favorites")
log = logging.getLogger(__name__)


@router.message(F.text == "⭐️ Мои рецепты")
async def show_favorites(message: Message) -> None:
    """Показать избранные рецепты пользователя в виде онлайн-кнопок."""
    favorite = database.get_favorites(message.from_user.id)

    title = html.escape("⭐️ Мои рецепты")
    if not favorite:
        await message.answer(
            f"{title}\n\nПока пусто — найдите рецепт через «🔎 Поиск рецептов» и нажмите «⭐️ Сохранить».",
            reply_markup=main_menu(),
        )
        return

    await message.answer(
        f"{title}\nВыберите рецепт — покажу его целиком:",
        reply_markup=favorites_list(favorite),
    )
    await message.answer(
        f"Всего рецептов: {len(favorite)}",
        reply_markup=main_menu(),
    )


@router.callback_query(F.data.startswith(CALLBACK_VIEW_FAVORITE))
async def view_favorite(callback: CallbackQuery) -> None:
    """По нажатию кнопки показать полный текст рецепта (фото + описание)."""
    recipe_id = callback.data.removeprefix(CALLBACK_VIEW_FAVORITE)
    await callback.answer()

    recipe: Recipe | None = await get_by_id(recipe_id)
    if recipe is None:
        await callback.answer("API не отвечает, попробуйте позже 😔", show_alert=True)
        return

    user_id = callback.from_user.id
    try:
        await callback.message.answer_photo(
            photo=recipe.image_url,
            caption=recipe_text(recipe),
            reply_markup=recipe_card(recipe.id, is_favorite=database.is_favorite(user_id, recipe.id)),
        )
    except Exception:  # noqa: BLE001 — картинка могла не загрузиться
        log.warning("Не удалось отправить фото рецепта %s, отправляю текстом", recipe.id)
        await callback.message.answer(
            recipe_text(recipe),
            reply_markup=recipe_card(recipe.id, is_favorite=database.is_favorite(user_id, recipe.id)),
        )
