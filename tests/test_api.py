import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database import connection
from database.models import Base, Department, User, Ticket
from main import app


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tempdir.name) / "api-test.db"
        self.orig_engine = connection.engine
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )
        connection.engine = self.engine
        Base.metadata.create_all(bind=self.engine)

        db = Session(self.engine)
        fallback = Department(name="未分类", is_fallback=True)
        dept = Department(name="技术部")
        user = User(name="张三", department=dept)
        db.add_all([fallback, dept, user])
        db.commit()
        self.fallback_id = fallback.id
        self.dept_id = dept.id
        self.user_id = user.id
        db.close()

        self.client = TestClient(app)

    def tearDown(self):
        connection.engine = self.orig_engine
        self.engine.dispose()
        self.tempdir.cleanup()

    def test_create_ticket_requires_department_id(self):
        resp = self.client.post("/api/tickets", json={
            "title": "测试", "description": "", "creator_id": 1,
        })
        self.assertEqual(resp.status_code, 422)
        data = resp.json()
        self.assertIn("department_id", str(data))

    def test_create_ticket_rejects_fallback_department(self):
        resp = self.client.post("/api/tickets", json={
            "title": "测试", "description": "",
            "creator_id": 1, "department_id": self.fallback_id,
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("fallback", resp.json()["detail"])

    def test_create_ticket_success(self):
        resp = self.client.post("/api/tickets", json={
            "title": "新工单", "description": "描述",
            "creator_id": 1, "department_id": self.dept_id,
            "priority": "high",
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["title"], "新工单")
        self.assertEqual(data["department_id"], self.dept_id)

    def test_update_ticket_success(self):
        db = Session(self.engine)
        ticket = Ticket(title="原标题", description="原描述",
                        creator_id=1, department_id=self.dept_id)
        db.add(ticket)
        db.commit()
        ticket_id = ticket.id
        db.close()

        resp = self.client.put(f"/api/tickets/{ticket_id}", json={
            "title": "新标题", "description": "新描述",
            "priority": "high", "department_id": self.dept_id,
            "operator_id": 1, "comment": "修改了标题",
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["title"], "新标题")

    def test_update_ticket_rejects_fallback(self):
        db = Session(self.engine)
        ticket = Ticket(title="标题", description="",
                        creator_id=1, department_id=self.dept_id)
        db.add(ticket)
        db.commit()
        ticket_id = ticket.id
        db.close()

        resp = self.client.put(f"/api/tickets/{ticket_id}", json={
            "title": "标题", "description": "",
            "priority": "medium", "department_id": self.fallback_id,
            "operator_id": 1, "comment": "",
        })
        self.assertEqual(resp.status_code, 400)

    def test_departments_default_excludes_fallback(self):
        resp = self.client.get("/api/departments")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        ids = [d["id"] for d in data]
        self.assertNotIn(self.fallback_id, ids)
        self.assertIn(self.dept_id, ids)

    def test_departments_include_fallback(self):
        resp = self.client.get("/api/departments?include_fallback=true")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        ids = [d["id"] for d in data]
        self.assertIn(self.fallback_id, ids)
        self.assertIn(self.dept_id, ids)

    def test_update_ticket_rejects_wrong_operator(self):
        db = Session(self.engine)
        ticket = Ticket(title="标题", description="",
                        creator_id=1, department_id=self.dept_id)
        db.add(ticket)
        db.commit()
        ticket_id = ticket.id
        db.close()

        resp = self.client.put(f"/api/tickets/{ticket_id}", json={
            "title": "新标题", "description": "",
            "priority": "medium", "department_id": self.dept_id,
            "operator_id": 999, "comment": "",
        })
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
