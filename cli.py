"""管理命令行"""
import logging
import sys
import argparse

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
    from mcp.server import run
    run()


def main():
    parser = argparse.ArgumentParser(description="钉钉工单系统管理工具")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="初始化数据库")
    sub.add_parser("seed", help="填充测试数据")
    sub.add_parser("mcp", help="启动 MCP Server")

    args = parser.parse_args()
    if args.command == "init":
        cmd_init()
    elif args.command == "seed":
        cmd_seed()
    elif args.command == "mcp":
        cmd_mcp()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
