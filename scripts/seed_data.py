"""测试数据填充"""
import logging
import sys
sys.path.insert(0, ".")

from sqlalchemy.orm import Session

from database.connection import init_db, get_session
from database.models import Department, User
from services import user_service as us
from services import ticket_service as ts

logger = logging.getLogger(__name__)


def _get_or_create_dept(db: Session, name: str, **kwargs):
    dept = db.query(Department).filter(Department.name == name).first()
    if dept:
        logger.info("部门已存在，跳过: %s", name)
        return dept
    return us.create_department(db, name=name, **kwargs)


def _get_or_create_user(db: Session, name: str, **kwargs):
    user = db.query(User).filter(User.name == name).first()
    if user:
        logger.info("用户已存在，跳过: %s", name)
        return user
    return us.create_user(db, name=name, **kwargs)


def seed():
    init_db()
    db = get_session()
    try:
        tech = _get_or_create_dept(db, name="技术部")
        ops = _get_or_create_dept(db, name="运维部")
        biz = _get_or_create_dept(db, name="业务部")

        alice = _get_or_create_user(db, name="张三", department_id=tech.id, role="admin")
        bob = _get_or_create_user(db, name="李四", department_id=tech.id)
        carol = _get_or_create_user(db, name="王五", department_id=ops.id)
        dave = _get_or_create_user(db, name="赵六", department_id=biz.id)

        t1 = ts.create_ticket(
            db, title="服务器磁盘空间不足",
            description="生产服务器 /data 分区使用率已达 95%，需要清理或扩容",
            creator_id=alice.id, department_id=ops.id, priority="high",
        )
        ts.transition_ticket(db, t1.id, "assign", bob.id)
        ts.transition_ticket(db, t1.id, "submit_review", bob.id, "已清理日志文件，释放了 20G 空间")

        t2 = ts.create_ticket(
            db, title="新员工入职 - 配置开发环境",
            description="需要为新员工配置 Git 权限、开发工具和 VPN",
            creator_id=carol.id, department_id=tech.id,
        )

        t3 = ts.create_ticket(
            db, title="数据库查询慢",
            description="订单查询接口响应超过 5 秒，需要优化索引",
            creator_id=dave.id, department_id=tech.id, priority="urgent",
        )

        logger.info("测试数据填充完成！")
        logger.info("  部门: %s, %s, %s", tech.name, ops.name, biz.name)
        logger.info("  用户: %s, %s, %s, %s", alice.name, bob.name, carol.name, dave.name)
        logger.info("  工单: #%s %s", t1.id, t1.title)
        logger.info("         #%s %s", t2.id, t2.title)
        logger.info("         #%s %s", t3.id, t3.title)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
