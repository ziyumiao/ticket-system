import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine

from database import connection
from database.models import Base, Department


class SessionScopeTest(unittest.TestCase):
    def setUp(self):
        self.original_engine = connection.engine
        self.tempdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tempdir.name) / "test.db"
        connection.engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=connection.engine)

    def tearDown(self):
        connection.engine.dispose()
        connection.engine = self.original_engine
        self.tempdir.cleanup()

    def test_session_scope_commits_on_success(self):
        with connection.session_scope() as db:
            db.add(Department(name="技术部"))

        with connection.session_scope() as db:
            names = [dept.name for dept in db.query(Department).all()]

        self.assertEqual(names, ["技术部"])

    def test_session_scope_rolls_back_on_error(self):
        with self.assertRaises(RuntimeError):
            with connection.session_scope() as db:
                db.add(Department(name="运维部"))
                raise RuntimeError("boom")

        with connection.session_scope() as db:
            count = db.query(Department).count()

        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
