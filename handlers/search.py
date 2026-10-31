"""Поиск рецептов (по кнопке «🔎 Поиск рецептов»)."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from keyboards.main_menu import main_menu
from keyboards.recipe_kb import recipe_card
from services.recipes_api import Recipe, search_recipes
from utils.formatting import recipe_text

router = Router(name="search")
log = logging.getLogger(__name__)


class SearchStates(StatesGroup):
    """Состояния FSM: ожидание текстового запроса от пользователя."""

    waiting_for_query = State()


@router.message(F.text == "🔎 Поиск рецептов")
async def start_search(message: Message, state: FSMContext) -> None:
    """Попросить пользователя ввести название блюда."""
    await state.set_state(SearchStates.waiting_for_query)
    await message.answer("Введите название блюда или его часть 🍝")


@router.message(SearchStates.waiting_for_query, F.text)
async def do_search(message: Message, state: FSMContext) -> None:
    """Найти рецепты по запросу (с переводом русских слов) и показать первый."""
    await state.clear()

    recipes, note = await search_recipes(message.text)
    if not recipes:
        await message.answer(
            "😕 Ничего не нашлось по запросу "
            f"<i>{message.text}</i>.\n"
            "Попробуйте другое слово — и снова «🔎 Поиск рецептов».",
            reply_markup=main_menu(),
        )
        return

    first: Recipe = recipes[0]
    try:
        await message.answer_photo(
            photo=first.image_url,
            caption=recipe_text(first),
            reply_markup=recipe_card(first.id),
        )
    except Exception:  # noqa: BLE001 — картинка могла не загрузиться
        log.warning("Не удалось отправить фото рецепта %s, отправляю текстом", first.id)
        await message.answer(recipe_text(first), reply_markup=recipe_card(first.id))

    if note:
        await message.answer(note)

    if len(recipes) > 1:
        await message.answer(
            f"Ещё найдено рецептов по запросу: {len(recipes) - 1}. Нажимайте «➡️ Другой рецепт» 😉"
        )
