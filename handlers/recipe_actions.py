"""Кнопки на карточке рецепта: сохранить в избранное / показать другой."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from handlers.states import SearchStates
from keyboards.recipe_kb import (
    CALLBACK_ADD_FAVORITE_PREFIX,
    CALLBACK_NEXT_RANDOM,
    recipe_card,
)
from services import database
from services.recipes_api import Recipe, get_by_id, get_random
from utils.formatting import recipe_text

router = Router(name="recipe_actions")
log = logging.getLogger(__name__)


@router.callback_query(F.data.startswith(CALLBACK_ADD_FAVORITE_PREFIX))
async def add_favorite(callback: CallbackQuery) -> None:
    """Сохранить рецепт в избранное и заменить кнопку на «✅ В избранном»."""
    recipe_id = callback.data.removeprefix(CALLBACK_ADD_FAVORITE_PREFIX)
    user_id = callback.from_user.id

    if database.is_favorite(user_id, recipe_id):
        await callback.answer("Этот рецепт уже в избранном 😉", show_alert=False)
        return

    recipe: Recipe | None = await get_by_id(recipe_id)
    if recipe is None:
        await callback.answer("Не удалось сохранить: API не отвечает 😔", show_alert=True)
        return

    database.save_favorite(user_id, recipe_id, recipe.title)
    await callback.answer("Сохранено ⭐️", show_alert=False)

    if isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(
            reply_markup=recipe_card(recipe_id, is_favorite=True)
        )


@router.callback_query(F.data == CALLBACK_NEXT_RANDOM)
async def next_recipe(callback: CallbackQuery, state: FSMContext) -> None:
    """Показать следующий рецепт из результатов поиска (или случайный, если поиск уже закончился)."""
    await callback.answer("Загружаю другой рецепт…", show_alert=False)

    recipe: Recipe | None = None

    # Идём по результатам текущего поиска, пока они не кончатся
    if await state.get_state() == SearchStates.showing_results.state:
        data = await state.get_data()
        ids: list[str] = data.get("ids", [])
        pos: int = data.get("pos", -1) + 1
        if pos < len(ids):
            await state.update_data(pos=pos)
            recipe = await get_by_id(ids[pos])
        else:
            await callback.answer(
                "Это все рецепты по вашему запросу 😉 Начните новый поиск",
                show_alert=False,
            )
            return

    if recipe is None:
        # Поиск неактивен (например, карточка открыта из избранного) — случайный рецепт
        recipe = await get_random()
    if recipe is None:
        await callback.answer("API не отвечает, попробуйте позже 😔", show_alert=True)
        return

    try:
        await callback.message.delete()
    except Exception:  # noqa: BLE001 — не критично, если старое сообщение не удалилось
        log.warning("Не удалось удалить карточку рецепта")

    try:
        await callback.message.answer_photo(
            photo=recipe.image_url,
            caption=recipe_text(recipe),
            reply_markup=recipe_card(recipe.id),
        )
    except Exception:  # noqa: BLE001 — картинка могла не загрузиться
        log.warning("Не удалось отправить фото рецепта %s, отправляю текстом", recipe.id)
        await callback.message.answer(
            recipe_text(recipe), reply_markup=recipe_card(recipe.id)
        )
