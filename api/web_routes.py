import logging
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Ticket
from services import ticket_service as ts
from services import user_service as us
from web.templates import templates

logger = logging.getLogger(__name__)

router = APIRouter(tags=["web"])


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    counts = dict(
        db.query(Ticket.status, func.count(Ticket.id))
          .group_by(Ticket.status)
          .all()
    )
    for s in ["pending", "in_progress", "reviewing", "done", "closed"]:
        counts.setdefault(s, 0)
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "counts": counts,
    })


@router.get("/tickets", response_class=HTMLResponse)
def ticket_list(
    request: Request,
    status: str = "",
    page: int = 1,
    db: Session = Depends(get_db),
):
    filter_status = status if status else None
    tickets, total = ts.list_tickets(db, status=filter_status, page=page)
    total_pages = max(1, (total + 19) // 20)
    return templates.TemplateResponse("ticket_list.html", {
        "request": request,
        "tickets": tickets,
        "current_status": status,
        "page": page,
        "total_pages": total_pages,
    })


@router.get("/tickets/create", response_class=HTMLResponse)
def create_ticket_page(request: Request, db: Session = Depends(get_db)):
    users = us.list_users(db)
    departments = us.list_departments(db)
    return templates.TemplateResponse("ticket_form.html", {
        "request": request,
        "users": users,
        "departments": departments,
    })


@router.post("/tickets/create")
def create_ticket_post(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    creator_id: int = Form(...),
    department_id: Optional[int] = Form(None),
    priority: str = Form("medium"),
    db: Session = Depends(get_db),
):
    ts.create_ticket(db, title, description, creator_id, department_id, priority)
    return RedirectResponse(url="/tickets", status_code=303)


@router.get("/tickets/{ticket_id}", response_class=HTMLResponse)
def ticket_detail(request: Request, ticket_id: int, error: str = "", db: Session = Depends(get_db)):
    ticket = ts.get_ticket(db, ticket_id)
    if not ticket:
        return RedirectResponse(url="/tickets")
    users = us.list_users(db)
    allowed_actions = list(ts.ALLOWED_TRANSITIONS.get(ticket.status, {}).keys())
    return templates.TemplateResponse("ticket_detail.html", {
        "request": request,
        "ticket": ticket,
        "users": users,
        "allowed_actions": allowed_actions,
        "error": error,
    })


@router.post("/tickets/{ticket_id}/action")
def ticket_action_post(
    ticket_id: int,
    action: str = Form(...),
    operator_id: int = Form(...),
    comment: str = Form(""),
    assignee_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    try:
        ts.transition_ticket(
            db, ticket_id, action, operator_id,
            comment if comment else None,
            assignee_id=assignee_id,
        )
    except ValueError as e:
        logger.error("工单操作失败: ticket_id=%s action=%s operator_id=%s error=%s",
                      ticket_id, action, operator_id, e)
        return RedirectResponse(
            url=f"/tickets/{ticket_id}?error={quote(str(e))}",
            status_code=303,
        )
    return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=303)


@router.get("/users", response_class=HTMLResponse)
def user_manage(request: Request, db: Session = Depends(get_db)):
    users = us.list_users(db)
    departments = us.list_departments(db)
    return templates.TemplateResponse("user_manage.html", {
        "request": request,
        "users": users,
        "departments": departments,
    })
