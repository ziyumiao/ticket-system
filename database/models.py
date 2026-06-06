from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Boolean, create_engine
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    dingtalk_dept_id = Column(Integer, unique=True, nullable=True)
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    is_fallback = Column(Boolean, default=False, nullable=False)

    parent = relationship("Department", remote_side=[id], back_populates="children")
    children = relationship("Department", back_populates="parent")
    users = relationship("User", back_populates="department")
    tickets = relationship("Ticket", back_populates="department",
                           foreign_keys="Ticket.department_id")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    dingtalk_user_id = Column(String(100), unique=True, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    role = Column(String(20), default="user")

    department = relationship("Department", back_populates="users")
    created_tickets = relationship(
        "Ticket", back_populates="creator", foreign_keys="Ticket.creator_id"
    )
    assigned_tickets = relationship(
        "Ticket", back_populates="assignee", foreign_keys="Ticket.assignee_id"
    )
    ticket_logs = relationship("TicketLog", back_populates="operator")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    status = Column(String(20), default="pending")
    priority = Column(String(10), default="medium")

    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    closed_at = Column(DateTime, nullable=True)

    creator = relationship("User", back_populates="created_tickets",
                           foreign_keys=[creator_id])
    assignee = relationship("User", back_populates="assigned_tickets",
                            foreign_keys=[assignee_id])
    department = relationship("Department", back_populates="tickets",
                              foreign_keys=[department_id])
    logs = relationship("TicketLog", back_populates="ticket",
                        order_by="TicketLog.created_at",
                        cascade="all, delete-orphan")


class TicketLog(Base):
    __tablename__ = "ticket_logs"

    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    ticket = relationship("Ticket", back_populates="logs")
    operator = relationship("User", back_populates="ticket_logs")
