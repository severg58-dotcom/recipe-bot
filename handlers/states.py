"""Состояния FSM бота (вынесены отдельно, чтобы модули не зависели друг от друга)."""

from aiogram.fsm.state import State, StatesGroup


class SearchStates(StatesGroup):
    """Состояния поиска: ждём запрос -> показываем результаты по запросу."""

    waiting_for_query = State()
    showing_results = State()
