# 钉钉工单系统 — 开发文档

## 1. 项目概述

一个基于 Python 的工单流转系统，集成钉钉群机器人交互，支持跨部门任务流转、验收闭环和 AI 调用。

## 2. 技术栈

| 模块 | 技术 | 说明 |
|------|------|------|
| Web 框架 | **FastAPI** | 异步、自动 OpenAPI 文档 |
| ORM | **SQLAlchemy 2.0** | 兼容 SQLite / MySQL，切换仅改连接串 |
| 前端 | **Jinja2 + HTMX** | 简单管理后台，无需前后端分离 |
| 钉钉 SDK | **httpx** + 原生 API | 轻量封装（Phase 3 实现） |
| MCP | **FastMCP** | 供 AI Agent 调用 |

## 3. 工单状态机

```
        ┌──────────┐
        │   创建    │
        └────┬─────┘
             ▼
        ┌──────────┐
        │  待处理   │◄──────────────┐
        └──┬───┬───┘               │
           │   │                   │
     指派  │   │ 驳回              │
           ▼   │                   │
        ┌──────────┐               │
        │  处理中   │───────────────┘
        └────┬─────┘  验收不通过
             │
             │ 提交验收
             ▼
        ┌──────────┐
        │  待验收   │
        └──┬───┬───┘
           │   │
     通过   │   │ 不通过 → 回到处理中
           ▼
        ┌──────────┐
        │  已完成   │
        └──────────┘
```

### 可操作的动作矩阵

| 当前状态 | 可执行动作 | 目标状态 | 说明 |
|----------|-----------|---------|------|
| pending | assign | in_progress | 指派，可选指定处理人 |
| pending | reject | closed | 驳回，工单关闭 |
| in_progress | submit_review | reviewing | 提交验收 |
| reviewing | approve | done | 验收通过，工单完成 |
| reviewing | decline | in_progress | 验收不通过，退回处理中 |

## 4. 数据模型

### Ticket（工单）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| title | String(200) | 工单标题 |
| description | Text | 工单描述 |
| status | String(20) | pending / in_progress / reviewing / done / closed |
| priority | String(10) | low / medium / high / urgent |
| creator_id | Integer FK→User | 创建人 |
| assignee_id | Integer FK→User nullable | 当前处理人 |
| department_id | Integer FK→Department nullable | 所属部门 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 最后更新时间 |
| closed_at | DateTime nullable | 关闭/完成时间 |

### TicketLog（工单日志）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| ticket_id | Integer FK→Ticket | 关联工单 |
| operator_id | Integer FK→User | 操作人 |
| action | String(50) | create / assign / reject / submit_review / approve / decline |
| comment | Text nullable | 操作备注 |
| created_at | DateTime | 操作时间 |

### User（用户）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| name | String(100) | 用户姓名 |
| dingtalk_user_id | String(100) unique nullable | 钉钉 userId |
| department_id | Integer FK→Department nullable | 所属部门 |
| role | String(20) | admin / user |

### Department（部门）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| name | String(200) | 部门名称 |
| dingtalk_dept_id | Integer unique nullable | 钉钉部门 ID |
| parent_id | Integer FK→Department nullable | 父部门（支持树形结构） |

## 5. 项目结构

```
ticket_system/
├── main.py                      # FastAPI 应用入口
├── config.py                    # 配置管理
├── requirements.txt             # Python 依赖
├── DEVELOPMENT.md               # 开发文档
│
├── database/
│   ├── __init__.py
│   ├── models.py                # 数据模型定义
│   └── connection.py            # 引擎 + Session 管理 + get_db 依赖
│
├── services/
│   ├── __init__.py
│   ├── ticket_service.py        # 工单业务逻辑
│   └── user_service.py          # 用户/部门服务
│
├── api/
│   ├── __init__.py
│   ├── api_routes.py            # REST API 接口
│   ├── web_routes.py            # Web 页面路由（Jinja2）
│   └── dingtalk_routes.py       # 钉钉回调入口（桩代码）
│
├── dingtalk/
│   └── __init__.py              # 钉钉集成（Phase 3）
│
├── mcp/
│   ├── __init__.py
│   └── server.py                # MCP Server（AI 可调用）
│
├── web/
│   ├── templates.py             # Jinja2 模板引擎
│   ├── static/
│   │   └── app.css
│   └── templates/
│       ├── layout.html
│       ├── dashboard.html       # 仪表盘
│       ├── ticket_list.html     # 工单列表
│       ├── ticket_detail.html   # 工单详情
│       ├── ticket_form.html     # 创建工单
│       └── user_manage.html     # 用户管理
│
├── scripts/
│   ├── __init__.py
│   └── seed_data.py             # 测试数据填充（幂等）
│
└── cli.py                       # 管理命令行
```

## 6. API 接口设计

### REST API（已验证）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/tickets | 工单列表（支持 status/assignee_id/department_id 筛选，分页） |
| POST | /api/tickets | 创建工单（含外键校验） |
| GET | /api/tickets/{id} | 工单详情 + 操作日志 |
| POST | /api/tickets/{id}/actions/{action} | 状态流转（assign/reject/submit_review/approve/decline） |
| GET | /api/users | 用户列表 |
| GET | /api/departments | 部门列表 |

### Web 页面（已验证）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / | 仪表盘（GROUP BY 统计） |
| GET | /tickets | 工单列表页 |
| GET | /tickets/create | 创建工单页 |
| POST | /tickets/create | 提交创建工单 |
| GET | /tickets/{id} | 工单详情页（含状态流转按钮+错误提示） |
| POST | /tickets/{id}/action | 执行状态流转 |
| GET | /users | 用户管理页 |

### MCP 接口（已验证）

```python
create_ticket(title, description, priority)                              # 创建工单
list_tickets(status)                                                      # 查询工单列表
get_ticket(ticket_id)                                                     # 工单详情
update_ticket_status(ticket_id, action, comment, operator_id)             # 状态流转
```

## 7. 代码质量保障（两轮 Review 完成）

### Round 1 — 修复 10 项

| # | 问题 | 修复方式 |
|---|------|---------|
| 1 | MCP 使用 creator_id 代替操作人 | 增加 operator_id 参数，0 时回退 |
| 2 | assign 不能指定处理人 | transition_ticket 增加 assignee_id 参数 |
| 3 | Web 表单 department_id 类型错误 | 改为 Optional[int] |
| 4 | Web 表单错误被静默吞掉 | 改为日志记录 + URL 参数传递错误信息 |
| 5 | 缺少 session rollback | get_db 改为 try/except/rollback 模式 |
| 6 | Seed 数据不幂等 | 增加 get_or_create 逻辑 |
| 7 | 重复的 get_db 定义 | 合并到 database/connection.py |
| 8 | 未使用的 api/templates.py | 删除 |
| 9 | 用 print 代替 logging | 替换为 logging 模块 |
| 10 | 日志返回非结构化 dict | 增加 TicketLogOut Pydantic 模型 |

### Round 2 — 修复 6 项

| # | 问题 | 修复方式 |
|---|------|---------|
| R1 | get_db 无条件 rollback | 改为标准 commit-on-success 模式 |
| R2 | 缺少外键存在性校验 | create_ticket 中校验 creator_id/department_id |
| R3 | 仪表盘加载 1000 行计数 | 改为 GROUP BY 查询 |
| R4 | Web 页面不显示错误信息 | 模板增加 error 显示 + CSS |
| R5 | datetime 序列化不一致 | TicketLogOut.created_at 改为 datetime 类型 |
| R6 | Web UI 无法指派给他人 | 增加 assignee_id 表单字段 + 模板 |

### 未解决（低优先级/后续阶段）

| # | 问题 | 说明 |
|---|------|------|
| P1 | 无认证授权 | Phase 5 处理 |
| P2 | 无 CSRF 保护 | Phase 5 处理 |
| P3 | 无钉钉签名验证 | Phase 3 处理 |
| P4 | Seed 非原子性 | 低优先级 |
| P5 | 缺少用户/部门 CRUD API | Phase 5 补充 |
| P6 | 缺少搜索/统计接口 | Phase 5 补充 |
| P7 | 缺少 Alembic 迁移 | 切换到 MySQL 时添加 |

## 8. 钉钉应用配置要点

1. 登录 [open-dev.dingtalk.com](https://open-dev.dingtalk.com) → 创建企业内部应用
2. 应用功能 → 机器人 → 启用，配置消息接收 URL：`https://你的域名/api/dingtalk/webhook`
3. 权限管理 → 申请以下权限：
   - `qyapi_robot_sendmsg`（机器人发送消息）
   - `qyapi_robot_receive`（机器人接收消息）
   - `qyapi_get_department_list`（获取部门列表）
   - `qyapi_get_user_list_by_department`（获取部门成员）
   - `qyapi_get_user_info`（获取用户详情）
4. 保存 `AppKey` 和 `AppSecret` 到 `.env` 文件

## 9. 配置参考

```python
# config.py（支持 .env 文件覆盖）
DATABASE_URL: str = "sqlite:///./ticket.db"       # 生产切 MySQL
DINGTALK_APP_KEY: str = ""
DINGTALK_APP_SECRET: str = ""
DINGTALK_AGENT_ID: int = 0
DINGTALK_ROBOT_CODE: str = ""
```

## 10. 开发环境启动

```bash
cd ticket_system
pip install -r requirements.txt
python -m scripts.seed_data       # 初始化 + 填充测试数据
uvicorn main:app --reload --port 8000
```

## 11. MCP 服务启动

```bash
cd ticket_system
python -m cli mcp                 # 通过 CLI 启动
# 或
python mcp/server.py              # 直接启动
```
