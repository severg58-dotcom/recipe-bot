"""Работа с избранными рецептами: SQLite, файл favorites.db в корне проекта."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "favorites.db"

_schema = """
CREATE TABLE IF NOT EXISTS favorites (
    user_id   INTEGER NOT NULL,
    recipe_id TEXT    NOT NULL,
    title     TEXT    NOT NULL,
    rating    INTEGER NOT NULL DEFAULT 0,
    added_at  TEXT    DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, recipe_id)
)
"""


def init_db() -> None:
    """Создать таблицы при запуске бота (и добавить колонку rating в старые БД)."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(_schema)
        try:
            conn.execute(
                "ALTER TABLE favorites ADD COLUMN rating INTEGER NOT NULL DEFAULT 0"
            )
        except sqlite3.OperationalError:
            pass  # колонка уже есть — это нормально


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


def set_rating(user_id: int, recipe_id: str, rating: int) -> None:
    """Поставить или изменить рейтинг рецепта (1..5 звёзд)."""
    rating = max(1, min(5, int(rating)))
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE favorites SET rating = ? WHERE user_id = ? AND recipe_id = ?",
            (rating, user_id, recipe_id),
        )
        conn.commit()


def get_rating(user_id: int, recipe_id: str) -> int:
    """Текущий рейтинг рецепта у пользователя (0 — пока не оценён)."""
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT rating FROM favorites WHERE user_id = ? AND recipe_id = ?",
            (user_id, recipe_id),
        ).fetchone()
    return int(row[0]) if row else 0


def get_favorites(user_id: int) -> list[tuple[str, str, int]]:
    """Список избранных: [(recipe_id, title, rating), ...], сверху — лучший рейтинг."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT recipe_id, title, rating FROM favorites WHERE user_id = ? "
            "ORDER BY rating DESC, added_at DESC",
            (user_id,),
        ).fetchall()
    return [(recipe_id, title, rating) for recipe_id, title, rating in rows]
