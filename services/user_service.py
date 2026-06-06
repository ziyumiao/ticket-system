from typing import List, Optional

from sqlalchemy.orm import Session

from database.models import User, Department


def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_dingtalk(db: Session, dingtalk_user_id: str) -> Optional[User]:
    return db.query(User).filter(
        User.dingtalk_user_id == dingtalk_user_id
    ).first()


def list_users(db: Session, department_id: Optional[int] = None) -> List[User]:
    query = db.query(User)
    if department_id:
        query = query.filter(User.department_id == department_id)
    return query.order_by(User.name).all()


def create_user(
    db: Session,
    name: str,
    dingtalk_user_id: Optional[str] = None,
    department_id: Optional[int] = None,
    role: str = "user",
) -> User:
    user = User(
        name=name,
        dingtalk_user_id=dingtalk_user_id,
        department_id=department_id,
        role=role,
    )
    db.add(user)
    db.flush()
    db.refresh(user)
    return user


def get_department(db: Session, dept_id: int) -> Optional[Department]:
    return db.query(Department).filter(Department.id == dept_id).first()


def list_departments(db: Session, include_fallback: bool = False) -> List[Department]:
    query = db.query(Department)
    if not include_fallback:
        query = query.filter(Department.is_fallback == False)
    return query.order_by(Department.name).all()


def get_fallback_department(db: Session) -> Optional[Department]:
    return db.query(Department).filter(Department.is_fallback == True).first()


def create_department(
    db: Session,
    name: str,
    dingtalk_dept_id: Optional[int] = None,
    parent_id: Optional[int] = None,
) -> Department:
    dept = Department(
        name=name,
        dingtalk_dept_id=dingtalk_dept_id,
        parent_id=parent_id,
    )
    db.add(dept)
    db.flush()
    db.refresh(dept)
    return dept
