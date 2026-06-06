import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, inspect, text

from alembic.config import Config
from alembic import command


class MigrationTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "test.db"
        self.db_url = f"sqlite:///{self.db_path}"
        self.engine = create_engine(
            self.db_url,
            connect_args={"check_same_thread": False},
        )

    def tearDown(self):
        self.engine.dispose()
        self.tempdir.cleanup()

    def _make_alembic_config(self):
        alembic_cfg = Config()
        alembic_cfg.set_main_option("script_location", str(PROJECT_ROOT / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", self.db_url)
        return alembic_cfg

    def test_migration_adds_is_fallback_column(self):
        self._create_old_schema()
        alembic_cfg = self._make_alembic_config()
        command.upgrade(alembic_cfg, "head")
        inspector = inspect(self.engine)
        columns = {c["name"]: c for c in inspector.get_columns("departments")}
        self.assertIn("is_fallback", columns)
        self.assertFalse(columns["is_fallback"]["nullable"])

    def test_migration_makes_department_id_not_null(self):
        self._create_old_schema()
        alembic_cfg = self._make_alembic_config()
        command.upgrade(alembic_cfg, "head")
        inspector = inspect(self.engine)
        columns = {c["name"]: c for c in inspector.get_columns("tickets")}
        self.assertIn("department_id", columns)
        self.assertFalse(columns["department_id"]["nullable"])

    def _create_old_schema(self):
        """Create tables with old schema (no is_fallback, nullable department_id)."""
        with self.engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE departments (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(50) NOT NULL,
                    parent_id INTEGER,
                    dingtalk_dept_id INTEGER
                )
            """))
            conn.execute(text("""
                CREATE TABLE tickets (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
                    creator_id INTEGER NOT NULL,
                    assignee_id INTEGER,
                    department_id INTEGER,
                    closed_at DATETIME,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
            """))
            conn.execute(text("""
                CREATE TABLE users (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(50) NOT NULL,
                    department_id INTEGER,
                    role VARCHAR(20) NOT NULL DEFAULT 'user'
                )
            """))
            conn.execute(text("""
                CREATE TABLE ticket_logs (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER NOT NULL,
                    action VARCHAR(50) NOT NULL,
                    operator_id INTEGER NOT NULL,
                    comment TEXT,
                    created_at DATETIME NOT NULL
                )
            """))

    def test_migration_migrates_null_department_to_fallback(self):
        self._create_old_schema()

        with self.engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO departments (id, name) VALUES (1, '未分类')"
            ))
            conn.execute(text(
                "INSERT INTO departments (id, name) VALUES (2, '技术部')"
            ))
            conn.execute(text(
                "INSERT INTO users (id, name, department_id) VALUES (1, '张三', 2)"
            ))
            conn.execute(text(
                "INSERT INTO tickets (id, title, description, status, priority, "
                "creator_id, department_id, created_at, updated_at) "
                "VALUES (1, '历史工单', '描述', 'pending', 'medium', 1, NULL, "
                "datetime('now'), datetime('now'))"
            ))

        alembic_cfg = self._make_alembic_config()
        command.upgrade(alembic_cfg, "head")

        with self.engine.connect() as conn:
            fallback_id = conn.execute(
                text("SELECT id FROM departments WHERE is_fallback = 1 LIMIT 1")
            ).scalar()
            self.assertIsNotNone(fallback_id)

            ticket_dept = conn.execute(
                text("SELECT department_id FROM tickets WHERE id = 1")
            ).scalar()
            self.assertEqual(ticket_dept, fallback_id)

            inspector = inspect(self.engine)
            columns = {c["name"]: c for c in inspector.get_columns("tickets")}
            self.assertFalse(columns["department_id"]["nullable"])


if __name__ == "__main__":
    unittest.main()
