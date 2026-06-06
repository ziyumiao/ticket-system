import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database.models import Base, Department, TicketLog, User, Ticket
from services import ticket_service as ts


class TicketServiceTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.db = Session(self.engine)

        self.fallback = Department(name="未分类", is_fallback=True)
        self.department = Department(name="技术部")
        self.creator = User(name="张三", department=self.department)
        self.assignee = User(name="李四", department=self.department)
        self.db.add_all([self.fallback, self.department, self.creator, self.assignee])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    # --- create_ticket ---

    def test_create_ticket_adds_pending_ticket_and_log(self):
        ticket = ts.create_ticket(
            self.db,
            title="服务器磁盘空间不足",
            description="需要清理日志",
            creator_id=self.creator.id,
            department_id=self.department.id,
            priority="high",
        )

        self.assertEqual(ticket.status, ts.STATUS_PENDING)
        self.assertEqual(ticket.creator_id, self.creator.id)
        self.assertEqual(ticket.department_id, self.department.id)
        self.assertEqual(ticket.priority, "high")

        logs = self.db.query(TicketLog).filter(TicketLog.ticket_id == ticket.id).all()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action, "create")
        self.assertEqual(logs[0].operator_id, self.creator.id)

    def test_create_ticket_requires_department_id(self):
        with self.assertRaises(TypeError):
            ts.create_ticket(
                self.db,
                title="缺失部门",
                description="",
                creator_id=self.creator.id,
                # department_id omitted
                priority="medium",
            )

    def test_create_ticket_rejects_none_department(self):
        with self.assertRaises(ValueError):
            ts.create_ticket(
                self.db,
                title="无效部门",
                description="",
                creator_id=self.creator.id,
                department_id=None,  # type: ignore
                priority="medium",
            )

    def test_create_ticket_rejects_fallback_department(self):
        with self.assertRaises(ValueError) as ctx:
            ts.create_ticket(
                self.db,
                title="使用 fallback",
                description="",
                creator_id=self.creator.id,
                department_id=self.fallback.id,
                priority="medium",
            )
        self.assertIn("fallback", str(ctx.exception))

    def test_create_ticket_rejects_nonexistent_department(self):
        with self.assertRaises(ValueError):
            ts.create_ticket(
                self.db,
                title="不存在的部门",
                description="",
                creator_id=self.creator.id,
                department_id=999,
                priority="medium",
            )

    def test_create_ticket_validates_creator(self):
        with self.assertRaises(ValueError):
            ts.create_ticket(
                self.db,
                title="无效创建人",
                description="",
                creator_id=999,
                department_id=self.department.id,
            )

    # --- update_ticket ---

    def test_update_ticket_changes_fields_and_writes_log(self):
        ticket = ts.create_ticket(
            self.db, title="原标题", description="原描述",
            creator_id=self.creator.id, department_id=self.department.id,
        )
        ticket_id = ticket.id

        updated = ts.update_ticket(
            self.db,
            ticket_id=ticket_id,
            operator_id=self.creator.id,
            title="新标题",
            description="新描述",
            priority="high",
            department_id=self.department.id,
        )

        self.assertEqual(updated.title, "新标题")
        self.assertEqual(updated.description, "新描述")
        self.assertEqual(updated.priority, "high")

        logs = self.db.query(TicketLog).filter(
            TicketLog.ticket_id == ticket_id, TicketLog.action == "update"
        ).all()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].operator_id, self.creator.id)

    def test_update_ticket_no_changes_no_log(self):
        ticket = ts.create_ticket(
            self.db, title="标题", description="描述",
            creator_id=self.creator.id, department_id=self.department.id,
            priority="medium",
        )
        ticket_id = ticket.id
        log_count_before = self.db.query(TicketLog).filter(
            TicketLog.ticket_id == ticket_id
        ).count()

        updated = ts.update_ticket(
            self.db,
            ticket_id=ticket_id,
            operator_id=self.creator.id,
            title="标题",
            description="描述",
            priority="medium",
            department_id=self.department.id,
        )

        log_count_after = self.db.query(TicketLog).filter(
            TicketLog.ticket_id == ticket_id
        ).count()
        self.assertEqual(updated.title, "标题")
        self.assertEqual(log_count_after, log_count_before)

    def test_update_ticket_rejects_non_creator(self):
        ticket = ts.create_ticket(
            self.db, title="标题", description="",
            creator_id=self.creator.id, department_id=self.department.id,
        )
        with self.assertRaises(ValueError):
            ts.update_ticket(
                self.db,
                ticket_id=ticket.id,
                operator_id=999,
                title="新标题", description="", priority="medium",
                department_id=self.department.id,
            )

    def test_update_ticket_rejects_fallback_department(self):
        ticket = ts.create_ticket(
            self.db, title="标题", description="",
            creator_id=self.creator.id, department_id=self.department.id,
        )
        with self.assertRaises(ValueError) as ctx:
            ts.update_ticket(
                self.db,
                ticket_id=ticket.id,
                operator_id=self.creator.id,
                title="标题", description="", priority="medium",
                department_id=self.fallback.id,
            )
        self.assertIn("fallback", str(ctx.exception))

    def test_update_ticket_rejects_done_status(self):
        ticket = ts.create_ticket(
            self.db, title="标题", description="",
            creator_id=self.creator.id, department_id=self.department.id,
        )
        ts.transition_ticket(self.db, ticket.id, "assign", self.creator.id)
        ts.transition_ticket(self.db, ticket.id, "submit_review", self.creator.id)
        ts.transition_ticket(self.db, ticket.id, "approve", self.creator.id)

        with self.assertRaises(ValueError) as ctx:
            ts.update_ticket(
                self.db,
                ticket_id=ticket.id,
                operator_id=self.creator.id,
                title="新标题", description="", priority="medium",
                department_id=self.department.id,
            )
        self.assertIn("不允许编辑", str(ctx.exception))

    def test_update_ticket_comment_is_optional(self):
        ticket = ts.create_ticket(
            self.db, title="标题", description="",
            creator_id=self.creator.id, department_id=self.department.id,
        )
        updated = ts.update_ticket(
            self.db,
            ticket_id=ticket.id,
            operator_id=self.creator.id,
            title="新标题", description="", priority="medium",
            department_id=self.department.id,
        )
        self.assertEqual(updated.title, "新标题")

    # --- existing tests (adapted) ---

    def test_ticket_can_follow_happy_path_to_done(self):
        ticket = ts.create_ticket(
            self.db,
            title="新员工入职",
            description="配置开发环境",
            creator_id=self.creator.id,
            department_id=self.department.id,
        )

        ticket = ts.transition_ticket(
            self.db,
            ticket.id,
            "assign",
            operator_id=self.creator.id,
            assignee_id=self.assignee.id,
        )
        self.assertEqual(ticket.status, ts.STATUS_IN_PROGRESS)
        self.assertEqual(ticket.assignee_id, self.assignee.id)

        ticket = ts.transition_ticket(
            self.db,
            ticket.id,
            "submit_review",
            operator_id=self.assignee.id,
            comment="已完成",
        )
        self.assertEqual(ticket.status, ts.STATUS_REVIEWING)

        ticket = ts.transition_ticket(
            self.db,
            ticket.id,
            "approve",
            operator_id=self.creator.id,
        )
        self.assertEqual(ticket.status, ts.STATUS_DONE)
        self.assertIsNotNone(ticket.closed_at)

        actions = [
            log.action
            for log in self.db.query(TicketLog)
            .filter(TicketLog.ticket_id == ticket.id)
            .order_by(TicketLog.id)
        ]
        self.assertEqual(actions, ["create", "assign", "submit_review", "approve"])

    def test_decline_returns_reviewing_ticket_to_in_progress(self):
        ticket = ts.create_ticket(
            self.db,
            title="数据库查询慢",
            description="查询响应超过 5 秒",
            creator_id=self.creator.id,
            department_id=self.department.id,
        )
        ts.transition_ticket(self.db, ticket.id, "assign", operator_id=self.creator.id)
        ts.transition_ticket(self.db, ticket.id, "submit_review", operator_id=self.creator.id)

        ticket = ts.transition_ticket(
            self.db,
            ticket.id,
            "decline",
            operator_id=self.creator.id,
            comment="还需要补充说明",
        )

        self.assertEqual(ticket.status, ts.STATUS_IN_PROGRESS)
        self.assertIsNone(ticket.closed_at)

    def test_invalid_transition_raises_value_error_without_log(self):
        ticket = ts.create_ticket(
            self.db,
            title="权限申请",
            description="申请代码仓库权限",
            creator_id=self.creator.id,
            department_id=self.department.id,
        )
        log_count = self.db.query(TicketLog).filter(TicketLog.ticket_id == ticket.id).count()

        with self.assertRaises(ValueError):
            ts.transition_ticket(
                self.db,
                ticket.id,
                "approve",
                operator_id=self.creator.id,
            )

        self.db.refresh(ticket)
        self.assertEqual(ticket.status, ts.STATUS_PENDING)
        self.assertEqual(
            self.db.query(TicketLog).filter(TicketLog.ticket_id == ticket.id).count(),
            log_count,
        )

    def test_create_ticket_validates_foreign_keys(self):
        with self.assertRaises(ValueError):
            ts.create_ticket(
                self.db, title="无效创建人", description="",
                creator_id=999, department_id=self.department.id,
            )

        with self.assertRaises(ValueError):
            ts.create_ticket(
                self.db, title="无效部门", description="",
                creator_id=self.creator.id, department_id=999,
            )


if __name__ == "__main__":
    unittest.main()
