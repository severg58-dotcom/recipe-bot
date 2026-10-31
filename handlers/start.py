"""/start — приветствие и главное меню."""

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards.main_menu import main_menu

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Показать главное меню: поиск рецептов / мои рецепты."""
    await message.answer(
        "Привет! 👋\n"
        "Я помогу найти вкусные рецепты и сохранить их в избранное.\n\n"
        "Выбери действие в меню ниже 👇",
        reply_markup=main_menu(),
    )
