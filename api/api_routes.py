from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from services import ticket_service as ts
from services import user_service as us

router = APIRouter(prefix="/api", tags=["api"])


class TicketCreate(BaseModel):
    title: str
    description: str = ""
    creator_id: int
    department_id: int
    priority: str = "medium"


class TicketUpdate(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    department_id: int
    operator_id: int
    comment: str = ""


class TicketAction(BaseModel):
    operator_id: int
    comment: Optional[str] = None
    assignee_id: Optional[int] = None


class TicketLogOut(BaseModel):
    id: int
    operator_name: str = ""
    action: str
    comment: Optional[str] = None
    created_at: datetime


class TicketOut(BaseModel):
    id: int
    title: str
    description: str
    status: str
    priority: str
    creator_id: int
    assignee_id: Optional[int] = None
    department_id: int
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    creator_name: str = ""
    assignee_name: str = ""
    department_name: str = ""
    logs: List[TicketLogOut] = []

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    id: int
    name: str
    dingtalk_user_id: Optional[str] = None
    department_id: Optional[int] = None
    role: str

    class Config:
        from_attributes = True


class DepartmentOut(BaseModel):
    id: int
    name: str
    dingtalk_dept_id: Optional[int] = None
    parent_id: Optional[int] = None
    is_fallback: bool = False

    class Config:
        from_attributes = True


def _ticket_to_out(ticket) -> TicketOut:
    logs = []
    for log in ticket.logs:
        logs.append(TicketLogOut(
            id=log.id,
            operator_name=log.operator.name if log.operator else "",
            action=log.action,
            comment=log.comment,
            created_at=log.created_at,
        ))
    return TicketOut(
        id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        status=ticket.status,
        priority=ticket.priority,
        creator_id=ticket.creator_id,
        assignee_id=ticket.assignee_id,
        department_id=ticket.department_id,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        closed_at=ticket.closed_at,
        creator_name=ticket.creator.name if ticket.creator else "",
        assignee_name=ticket.assignee.name if ticket.assignee else "",
        department_name=ticket.department.name if ticket.department else "",
        logs=logs,
    )


@router.post("/tickets", response_model=TicketOut)
def create_ticket(data: TicketCreate, db: Session = Depends(get_db)):
    try:
        ticket = ts.create_ticket(
            db,
            title=data.title,
            description=data.description,
            creator_id=data.creator_id,
            department_id=data.department_id,
            priority=data.priority,
        )
        ticket = ts.get_ticket(db, ticket.id)
        return _ticket_to_out(ticket)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/tickets/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: int, data: TicketUpdate, db: Session = Depends(get_db)):
    try:
        ticket = ts.update_ticket(
            db,
            ticket_id=ticket_id,
            operator_id=data.operator_id,
            title=data.title,
            description=data.description,
            priority=data.priority,
            department_id=data.department_id,
            comment=data.comment,
        )
        ticket = ts.get_ticket(db, ticket.id)
        return _ticket_to_out(ticket)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tickets", response_model=dict)
def list_tickets(
    status: Optional[str] = Query(None),
    creator_id: Optional[int] = Query(None),
    assignee_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    tickets, total = ts.list_tickets(
        db, status=status, creator_id=creator_id,
        assignee_id=assignee_id, department_id=department_id,
        page=page, page_size=page_size,
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_ticket_to_out(t) for t in tickets],
    }


@router.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = ts.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")
    return _ticket_to_out(ticket)


@router.post("/tickets/{ticket_id}/actions/{action}", response_model=TicketOut)
def ticket_action(
    ticket_id: int,
    action: str,
    data: TicketAction,
    db: Session = Depends(get_db),
):
    try:
        ticket = ts.transition_ticket(
            db, ticket_id, action, data.operator_id, data.comment,
            assignee_id=data.assignee_id,
        )
        ticket = ts.get_ticket(db, ticket.id)
        return _ticket_to_out(ticket)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users", response_model=List[UserOut])
def list_users(
    department_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    return us.list_users(db, department_id=department_id)


@router.get("/departments", response_model=List[DepartmentOut])
def list_departments(
    include_fallback: bool = Query(False),
    db: Session = Depends(get_db),
):
    return us.list_departments(db, include_fallback=include_fallback)
