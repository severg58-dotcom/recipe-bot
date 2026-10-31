"""Работа с избранными рецептами: SQLite, файл favorites.db в корне проекта."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "favorites.db"

_schema = """
CREATE TABLE IF NOT EXISTS favorites (
    user_id   INTEGER NOT NULL,
    recipe_id TEXT    NOT NULL,
    title     TEXT    NOT NULL,
    added_at  TEXT    DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, recipe_id)
)
"""


def init_db() -> None:
    """Создать таблицы при запуске бота."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(_schema)


def is_favorite(user_id: int, recipe_id: str) -> bool:
    """Проверить, сохранён ли рецепт у пользователя."""
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND recipe_id = ?",
            (user_id, recipe_id),
        ).fetchone()
    return row is not None


def save_favorite(user_id: int, recipe_id: str, title: str) -> None:
    """Сохранить рецепт в избранное пользователя.

    Повторное сохранение того же рецепта не дублирует запись.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO favorites (user_id, recipe_id, title) VALUES (?, ?, ?)",
            (user_id, recipe_id, title),
        )
        conn.commit()


def remove_favorite(user_id: int, recipe_id: str) -> bool:
    """Удалить рецепт из избранного. Возвращает True, если удаление было."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "DELETE FROM favorites WHERE user_id = ? AND recipe_id = ?",
            (user_id, recipe_id),
        )
        conn.commit()
    return cursor.rowcount > 0


def get_favorites(user_id: int) -> list[tuple[str, str]]:
    """Список избранных рецептов пользователя: [(recipe_id, title), ...]."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT recipe_id, title FROM favorites WHERE user_id = ? "
            "ORDER BY added_at DESC",
            (user_id,),
        ).fetchall()
    return [(recipe_id, title) for recipe_id, title in rows]
