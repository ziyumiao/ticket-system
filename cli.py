"""管理命令行"""
import logging
import sys
import argparse

from alembic.config import Config
from alembic import command

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


def cmd_init():
    from database.connection import init_db
    init_db()
    logger.info("数据库初始化完成")


def cmd_seed():
    from scripts.seed_data import seed
    seed()


def cmd_mcp():
    from mcp_server.server import run
    run()


def cmd_db_upgrade():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    logger.info("数据库迁移完成")


def cmd_db_current():
    alembic_cfg = Config("alembic.ini")
    command.current(alembic_cfg)


def main():
    parser = argparse.ArgumentParser(description="钉钉工单系统管理工具")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="初始化数据库")
    sub.add_parser("seed", help="填充测试数据")
    sub.add_parser("mcp", help="启动 MCP Server")

    db_parser = sub.add_parser("db", help="数据库迁移管理")
    db_sub = db_parser.add_subparsers(dest="db_command")
    db_sub.add_parser("upgrade", help="升级到最新迁移版本")
    db_sub.add_parser("current", help="查看当前迁移版本")

    args = parser.parse_args()
    if args.command == "init":
        cmd_init()
    elif args.command == "seed":
        cmd_seed()
    elif args.command == "mcp":
        cmd_mcp()
    elif args.command == "db":
        if args.db_command == "upgrade":
            cmd_db_upgrade()
        elif args.db_command == "current":
            cmd_db_current()
        else:
            print("请指定 db 子命令: upgrade, current")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
