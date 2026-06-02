from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session, joinedload

from database.models import Ticket, TicketLog, User, Department


STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_REVIEWING = "reviewing"
STATUS_DONE = "done"
STATUS_CLOSED = "closed"

ALLOWED_TRANSITIONS = {
    STATUS_PENDING: {
        "assign": STATUS_IN_PROGRESS,
        "reject": STATUS_CLOSED,
    },
    STATUS_IN_PROGRESS: {
        "submit_review": STATUS_REVIEWING,
    },
    STATUS_REVIEWING: {
        "approve": STATUS_DONE,
        "decline": STATUS_IN_PROGRESS,
    },
}


def create_ticket(
    db: Session,
    title: str,
    description: str,
    creator_id: int,
    department_id: Optional[int] = None,
    priority: str = "medium",
) -> Ticket:
    user = db.query(User).filter(User.id == creator_id).first()
    if not user:
        raise ValueError(f"创建者不存在: {creator_id}")
    if department_id is not None:
        dept = db.query(Department).filter(Department.id == department_id).first()
        if not dept:
            raise ValueError(f"部门不存在: {department_id}")

    ticket = Ticket(
        title=title,
        description=description,
        creator_id=creator_id,
        department_id=department_id,
        priority=priority,
        status=STATUS_PENDING,
    )
    db.add(ticket)
    db.flush()

    _add_log(db, ticket.id, creator_id, "create")
    db.flush()
    db.refresh(ticket)
    return ticket


def get_ticket(db: Session, ticket_id: int) -> Optional[Ticket]:
    return db.query(Ticket).options(
        joinedload(Ticket.creator),
        joinedload(Ticket.assignee),
        joinedload(Ticket.department),
        joinedload(Ticket.logs).joinedload(TicketLog.operator),
    ).filter(Ticket.id == ticket_id).first()


def list_tickets(
    db: Session,
    status: Optional[str] = None,
    creator_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    department_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Ticket], int]:
    query = db.query(Ticket).options(
        joinedload(Ticket.creator),
        joinedload(Ticket.assignee),
    )

    if status:
        query = query.filter(Ticket.status == status)
    if creator_id:
        query = query.filter(Ticket.creator_id == creator_id)
    if assignee_id:
        query = query.filter(Ticket.assignee_id == assignee_id)
    if department_id:
        query = query.filter(Ticket.department_id == department_id)

    total = query.count()
    tickets = query.order_by(Ticket.updated_at.desc()) \
                   .offset((page - 1) * page_size) \
                   .limit(page_size) \
                   .all()
    return tickets, total


def transition_ticket(
    db: Session,
    ticket_id: int,
    action: str,
    operator_id: int,
    comment: Optional[str] = None,
    assignee_id: Optional[int] = None,
) -> Ticket:
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise ValueError(f"工单不存在: {ticket_id}")

    allowed = ALLOWED_TRANSITIONS.get(ticket.status, {})
    new_status = allowed.get(action)
    if not new_status:
        raise ValueError(
            f"工单当前状态 '{ticket.status}' 不允许执行 '{action}' 操作"
        )

    ticket.status = new_status
    ticket.updated_at = datetime.now()

    if action == "assign":
        ticket.assignee_id = assignee_id if assignee_id is not None else operator_id
    if new_status in (STATUS_DONE, STATUS_CLOSED):
        ticket.closed_at = datetime.now()

    _add_log(db, ticket_id, operator_id, action, comment)
    db.flush()
    db.refresh(ticket)
    return ticket


def _add_log(
    db: Session,
    ticket_id: int,
    operator_id: int,
    action: str,
    comment: Optional[str] = None,
):
    log = TicketLog(
        ticket_id=ticket_id,
        operator_id=operator_id,
        action=action,
        comment=comment,
    )
    db.add(log)
    db.flush()
