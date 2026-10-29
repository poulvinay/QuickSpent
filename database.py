"""SQLite persistence for transactions and their categories."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


DEFAULT_CATEGORIES = (
    ("Salary", "In"),
    ("Loaned", "In"),
    ("Food", "Out"),
    ("Transport", "Out"),
    ("Shopping", "Out"),
    ("Bills", "Out"),
    ("Health", "Out"),
    ("Other", "Out"),
)


class ExpenseDatabase:
    """Manage local transaction and category data."""

    def __init__(self, db_path):
        self.db_path = str(db_path)
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.create_tables()

    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def _connection(self):
        """Commit successful operations, roll back failures, and close cleanly."""
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _now():
        return datetime.now().astimezone().isoformat(timespec="seconds")

    def create_tables(self):
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL COLLATE NOCASE UNIQUE
                        CHECK (length(trim(name)) > 0),
                    flow TEXT NOT NULL DEFAULT 'Out' CHECK (flow IN ('In', 'Out')),
                    is_archived INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount_minor INTEGER NOT NULL CHECK (amount_minor > 0),
                    currency_code TEXT NOT NULL DEFAULT 'INR',
                    category_id INTEGER NOT NULL REFERENCES categories(id),
                    note TEXT NOT NULL DEFAULT '',
                    spent_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS expenses_spent_at_idx
                    ON expenses(spent_at);
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )

            category_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(categories)")
            }
            if "flow" not in category_columns:
                connection.execute(
                    "ALTER TABLE categories ADD COLUMN flow TEXT NOT NULL DEFAULT 'Out'"
                )

            now = self._now()
            connection.executemany(
                "INSERT OR IGNORE INTO categories(name, flow, created_at) VALUES (?, ?, ?)",
                ((name, flow, now) for name, flow in DEFAULT_CATEGORIES),
            )

    def get_categories(self, include_archived=False):
        query = "SELECT id, name, flow, is_archived FROM categories"
        if not include_archived:
            query += " WHERE is_archived = 0"
        query += " ORDER BY name COLLATE NOCASE, id"
        with self._connection() as connection:
            return connection.execute(query).fetchall()

    def add_category(self, name, flow="Out"):
        name = name.strip()
        if not name:
            raise ValueError("Category name is required.")
        flow = flow.title()
        if flow not in ("In", "Out"):
            raise ValueError("Category type must be In or Out.")

        with self._connection() as connection:
            cursor = connection.execute(
                "INSERT INTO categories(name, flow, created_at) VALUES (?, ?, ?)",
                (name, flow, self._now()),
            )
            return cursor.lastrowid

    def update_category_flow(self, category_id, flow):
        flow = flow.title()
        if flow not in ("In", "Out"):
            raise ValueError("Category type must be In or Out.")
        with self._connection() as connection:
            connection.execute(
                "UPDATE categories SET flow = ? WHERE id = ?", (flow, category_id)
            )

    def rename_category(self, category_id, name):
        name = name.strip()
        if not name:
            raise ValueError("Category name is required.")
        with self._connection() as connection:
            connection.execute(
                "UPDATE categories SET name = ? WHERE id = ?", (name, category_id)
            )

    def archive_category(self, category_id):
        with self._connection() as connection:
            connection.execute(
                "UPDATE categories SET is_archived = 1 WHERE id = ?", (category_id,)
            )

    def add_expense(
        self, amount_minor, category_id, note="", currency_code="INR", spent_at=None
    ):
        if not isinstance(amount_minor, int) or amount_minor <= 0:
            raise ValueError("Amount must be a positive number of minor currency units.")

        now = self._now()
        with self._connection() as connection:
            cursor = connection.execute(
                """INSERT INTO expenses
                   (amount_minor, currency_code, category_id, note, spent_at,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    amount_minor,
                    currency_code.upper(),
                    category_id,
                    note.strip(),
                    spent_at or now,
                    now,
                    now,
                ),
            )
            return cursor.lastrowid

    def update_expense(self, expense_id, amount_minor, category_id, note="", spent_at=None):
        if not isinstance(amount_minor, int) or amount_minor <= 0:
            raise ValueError("Amount must be positive.")

        now = self._now()
        with self._connection() as connection:
            connection.execute(
                """UPDATE expenses
                   SET amount_minor = ?, category_id = ?, note = ?,
                       spent_at = ?, updated_at = ?
                   WHERE id = ?""",
                (amount_minor, category_id, note.strip(), spent_at or now, now, expense_id),
            )

    def delete_expense(self, expense_id):
        with self._connection() as connection:
            connection.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))

    def get_expenses(self, limit=100, month=None, day=None):
        filters = []
        parameters = []
        if month:
            filters.append("substr(e.spent_at, 1, 7) = ?")
            parameters.append(month)
        if day:
            filters.append("substr(e.spent_at, 9, 2) = ?")
            parameters.append(f"{int(day):02d}")

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        parameters.append(limit)
        with self._connection() as connection:
            return connection.execute(
                f"""SELECT e.id, e.amount_minor, e.currency_code, e.category_id,
                          c.name, c.flow, e.note, e.spent_at
                   FROM expenses AS e
                   JOIN categories AS c ON c.id = e.category_id
                   {where_clause}
                   ORDER BY e.spent_at DESC, e.id DESC
                   LIMIT ?""",
                parameters,
            ).fetchall()

    def get_expense_months(self):
        with self._connection() as connection:
            return [
                row[0]
                for row in connection.execute(
                    """SELECT DISTINCT substr(spent_at, 1, 7)
                       FROM expenses
                       WHERE spent_at IS NOT NULL AND length(spent_at) >= 7
                       ORDER BY 1 DESC"""
                ).fetchall()
            ]

    def get_expense(self, expense_id):
        with self._connection() as connection:
            return connection.execute(
                """SELECT e.id, e.amount_minor, e.currency_code, e.category_id,
                          c.flow, e.note, e.spent_at
                   FROM expenses AS e
                   JOIN categories AS c ON c.id = e.category_id
                   WHERE e.id = ?""",
                (expense_id,),
            ).fetchone()

    def get_total_since(self, since):
        with self._connection() as connection:
            result = connection.execute(
                """SELECT COALESCE(
                       SUM(CASE c.flow WHEN 'In' THEN e.amount_minor
                           ELSE -e.amount_minor END), 0)
                   FROM expenses AS e
                   JOIN categories AS c ON c.id = e.category_id
                   WHERE e.spent_at >= ?""",
                (since,),
            ).fetchone()
            return result[0]

    def get_cashflow_since(self, since):
        with self._connection() as connection:
            return connection.execute(
                """SELECT
                       COALESCE(SUM(CASE WHEN c.flow = 'In'
                           THEN e.amount_minor ELSE 0 END), 0),
                       COALESCE(SUM(CASE WHEN c.flow = 'Out'
                           THEN e.amount_minor ELSE 0 END), 0)
                   FROM expenses AS e
                   JOIN categories AS c ON c.id = e.category_id
                   WHERE e.spent_at >= ?""",
                (since,),
            ).fetchone()

    def get_spending_limit(self):
        with self._connection() as connection:
            row = connection.execute(
                "SELECT value FROM app_settings WHERE key = 'monthly_spending_limit'"
            ).fetchone()
            return int(row[0]) if row else 0

    def set_spending_limit(self, amount_minor):
        if not isinstance(amount_minor, int) or amount_minor < 0:
            raise ValueError("Spending limit must be zero or a positive amount.")
        with self._connection() as connection:
            connection.execute(
                """INSERT INTO app_settings(key, value) VALUES ('monthly_spending_limit', ?)
                   ON CONFLICT(key) DO UPDATE SET value = excluded.value""",
                (str(amount_minor),),
            )

    def get_outgoing_since(self, since):
        with self._connection() as connection:
            result = connection.execute(
                """SELECT COALESCE(SUM(e.amount_minor), 0)
                   FROM expenses AS e
                   JOIN categories AS c ON c.id = e.category_id
                   WHERE c.flow = 'Out' AND e.spent_at >= ?""",
                (since,),
            ).fetchone()
            return result[0]
