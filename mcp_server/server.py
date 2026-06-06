try:
    from mcp.server.fastmcp import FastMCP
    _fastmcp_import_error = None
except ModuleNotFoundError as exc:
    _fastmcp_import_error = exc

    class FastMCP:
        def __init__(self, name: str):
            self.name = name

        def tool(self):
            def decorator(func):
                return func

            return decorator

        def run(self, transport: str = "stdio"):
            raise RuntimeError(
                "MCP SDK 未安装或无法导入，请安装提供 mcp.server.fastmcp 的 MCP 包后再启动 MCP 服务"
            ) from _fastmcp_import_error

from database.connection import session_scope
from services import ticket_service as ts
from services import user_service as us

mcp = FastMCP("钉钉工单系统")


@mcp.tool()
def create_ticket(title: str, description: str = "", priority: str = "medium") -> str:
    """创建工单（默认使用第一个用户作为创建人，后续可指定）"""
    with session_scope() as db:
        user = us.list_users(db)
        if not user:
            return "错误: 系统中无用户"
        ticket = ts.create_ticket(
            db, title=title, description=description,
            creator_id=user[0].id, priority=priority,
        )
        return f"工单创建成功: #{ticket.id} {ticket.title} (状态: {ticket.status})"


@mcp.tool()
def list_tickets(status: str = "") -> str:
    """查询工单列表，可按状态筛选"""
    with session_scope() as db:
        filter_status = status if status else None
        tickets, total = ts.list_tickets(db, status=filter_status)
        if not tickets:
            return "暂无工单"
        lines = [f"共 {total} 个工单:"]
        for t in tickets:
            assignee = t.assignee.name if t.assignee else "未指派"
            lines.append(
                f"#{t.id} [{t.status}] {t.title} - {assignee}"
            )
        return "\n".join(lines)


@mcp.tool()
def get_ticket(ticket_id: int) -> str:
    """查看工单详情"""
    with session_scope() as db:
        t = ts.get_ticket(db, ticket_id)
        if not t:
            return f"工单 #{ticket_id} 不存在"
        lines = [
            f"工单 #{t.id}",
            f"标题: {t.title}",
            f"描述: {t.description}",
            f"状态: {t.status}",
            f"优先级: {t.priority}",
            f"创建人: {t.creator.name if t.creator else ''}",
            f"处理人: {t.assignee.name if t.assignee else '未指派'}",
            f"部门: {t.department.name if t.department else ''}",
            f"创建时间: {t.created_at}",
        ]
        if t.closed_at:
            lines.append(f"关闭时间: {t.closed_at}")
        return "\n".join(lines)


@mcp.tool()
def update_ticket_status(ticket_id: int, action: str, comment: str = "", operator_id: int = 0) -> str:
    """流转工单状态
    action 可选值: assign(指派), reject(驳回), submit_review(提交验收), approve(验收通过), decline(验收不通过)
    """
    try:
        with session_scope() as db:
            t = ts.get_ticket(db, ticket_id)
            if not t:
                return f"工单 #{ticket_id} 不存在"
            if operator_id == 0:
                operator_id = t.creator_id
            t = ts.transition_ticket(
                db, ticket_id, action, operator_id,
                comment if comment else None,
            )
            return f"操作成功: #{t.id} 状态变更为 {t.status}"
    except ValueError as e:
        return f"操作失败: {e}"


def run():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run()
