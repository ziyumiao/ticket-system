import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine

from database import connection
from database.models import Base, Ticket, TicketLog, User, Department
from mcp_server import server as mcp_tools
from services import ticket_service as ts


class McpServerTest(unittest.TestCase):
    def setUp(self):
        self.original_engine = connection.engine
        self.tempdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tempdir.name) / "mcp-test.db"
        connection.engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=connection.engine)

        with connection.session_scope() as db:
            fallback = Department(name="未分类", is_fallback=True)
            dept = Department(name="技术部")
            user = User(name="张三", department=dept)
            db.add_all([fallback, dept, user])
            db.flush()
            self.fallback_id = fallback.id
            self.dept_id = dept.id
            self.user_id = user.id

    def tearDown(self):
        connection.engine.dispose()
        connection.engine = self.original_engine
        self.tempdir.cleanup()

    def test_create_ticket_requires_creator_and_department(self):
        result = mcp_tools.create_ticket(
            title="无参数",
            description="",
            priority="medium",
            creator_id=0,
            department_id=0,
        )
        self.assertIn("必填", result)

    def test_create_ticket_success_with_real_department(self):
        result = mcp_tools.create_ticket(
            title="MCP 创建工单",
            description="验证 MCP 创建",
            priority="high",
            creator_id=1,
            department_id=self.dept_id,
        )
        self.assertIn("工单创建成功", result)
        with connection.session_scope() as db:
            ticket = db.query(Ticket).filter(Ticket.title == "MCP 创建工单").one()
            self.assertEqual(ticket.creator_id, 1)
            self.assertEqual(ticket.department_id, self.dept_id)
            self.assertEqual(len(ticket.logs), 1)
            self.assertEqual(ticket.logs[0].action, "create")

    def test_create_ticket_rejects_fallback_department(self):
        result = mcp_tools.create_ticket(
            title="使用 fallback",
            description="",
            priority="medium",
            creator_id=1,
            department_id=self.fallback_id,
        )
        self.assertIn("错误", result)
        self.assertIn("fallback", result)

    def test_create_ticket_rejects_nonexistent_department(self):
        result = mcp_tools.create_ticket(
            title="不存在",
            description="",
            priority="medium",
            creator_id=1,
            department_id=999,
        )
        self.assertIn("错误", result)

    def test_create_ticket_rejects_nonexistent_user(self):
        result = mcp_tools.create_ticket(
            title="不存在用户",
            description="",
            priority="medium",
            creator_id=999,
            department_id=self.dept_id,
        )
        self.assertIn("错误", result)

    def test_update_ticket_status_persists_in_new_session(self):
        with connection.session_scope() as db:
            ticket = ts.create_ticket(
                db,
                title="MCP 状态流转",
                description="验证 MCP 流转会提交",
                creator_id=1,
                department_id=self.dept_id,
            )
            ticket_id = ticket.id

        result = mcp_tools.update_ticket_status(
            ticket_id=ticket_id,
            action="assign",
            operator_id=1,
            comment="开始处理",
        )

        self.assertIn("操作成功", result)
        with connection.session_scope() as db:
            ticket = db.query(Ticket).filter(Ticket.id == ticket_id).one()
            self.assertEqual(ticket.status, ts.STATUS_IN_PROGRESS)
            self.assertEqual(ticket.assignee_id, 1)
            actions = [log.action for log in ticket.logs]
            self.assertEqual(actions, ["create", "assign"])

    def test_invalid_mcp_transition_does_not_add_log(self):
        with connection.session_scope() as db:
            ticket = ts.create_ticket(
                db,
                title="MCP 非法流转",
                description="验证异常不会写入日志",
                creator_id=1,
                department_id=self.dept_id,
            )
            ticket_id = ticket.id

        result = mcp_tools.update_ticket_status(
            ticket_id=ticket_id,
            action="approve",
            operator_id=1,
        )

        self.assertIn("操作失败", result)
        with connection.session_scope() as db:
            ticket = db.query(Ticket).filter(Ticket.id == ticket_id).one()
            self.assertEqual(ticket.status, ts.STATUS_PENDING)
            logs = db.query(TicketLog).filter(TicketLog.ticket_id == ticket_id).all()
            self.assertEqual([log.action for log in logs], ["create"])


if __name__ == "__main__":
    unittest.main()
