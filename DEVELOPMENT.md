# 钉钉工单系统 - 开发文档

## 当前进度快照

截至当前代码状态，项目已经完成一个可本地运行的工单系统 MVP：

| 模块 | 状态 | 说明 |
|------|------|------|
| 项目骨架 | 已完成 | FastAPI 应用入口、分层目录、配置文件、静态资源、模板目录均已建立 |
| 数据层 | 已完成 | SQLAlchemy 模型覆盖部门、用户、工单、工单日志；当前默认使用 SQLite |
| 工单业务 | 已完成 | 支持创建、查询、分页列表、状态流转、操作日志记录 |
| Web 管理端 | 已完成基础版 | 支持仪表盘、工单列表、创建工单、工单详情、状态流转、用户管理展示 |
| REST API | 已完成基础版 | 支持工单创建、列表、详情、动作流转、用户列表、部门列表 |
| MCP | 已完成基础版 | 已接入 MCP SDK，AI 可调用创建、列表、详情、状态更新工具 |
| 钉钉集成 | 桩代码阶段 | 已有 webhook 路由，当前仅返回“功能开发中” |
| 测试数据 | 已完成 | `scripts.seed_data` 可初始化并填充示例部门、用户、工单 |
| 自动化测试 | 已完成基础版 | 当前有 10 个 `unittest`，覆盖事务、状态机和 MCP 写操作提交 |
| 生产化能力 | 待开始 | 认证授权、CSRF、Alembic 实际迁移、Docker、HTTPS、MySQL 切换等尚未落地 |

当前推荐继续推进 **Phase 2 Web 页面增强**，然后进入 **Phase 3 钉钉真实集成**。

## 本轮完成项

### P0 风险修复

| 项目 | 状态 | 说明 |
|------|------|------|
| MCP 写操作事务提交 | 已完成 | 新增 `database.connection.session_scope()`，MCP 写操作会成功提交、异常回滚 |
| 裸 Session 事务边界 | 已完成 | `scripts.seed_data` 改用 `session_scope()`，seed 在一个事务中提交 |
| MCP 包名遮挡 | 已完成 | 本地目录从 `mcp/` 迁移为 `mcp_server/`，避免遮挡外部 MCP SDK |
| MCP 工具级回归测试 | 已完成 | 新增 MCP 创建/流转持久化测试，防止漏 commit 回归 |
| 状态机服务层测试 | 已完成 | 覆盖创建、主流程、退回、非法流转、外键校验 |

### 依赖与运行环境

| 项目 | 状态 | 说明 |
|------|------|------|
| Python 版本 | 已完成 | 使用 pyenv，项目 `.python-version` 为 `3.11.12` |
| FastAPI 升级 | 已完成 | 升级到 `fastapi==0.136.3` |
| MCP SDK 接入 | 已完成 | 使用 `mcp==1.27.2`，`mcp_server/server.py` 可正常导入 SDK |
| Starlette 1.x 兼容 | 已完成 | Web 模板响应已改为 `TemplateResponse(request, name, context)` |
| 本地服务验证 | 已完成 | `python -m uvicorn main:app --port 9255` 可运行，首页/API/静态资源验证通过 |

### Review 与验证

| 项目 | 结果 |
|------|------|
| P0 实现 review | 已完成，发现的问题已修复 |
| 依赖升级 review | 已完成，未发现兼容性问题 |
| `python -m pip check` | 通过 |
| `python -m unittest discover` | 10 tests OK |
| 本地 smoke test | `/`、`/api/users`、`/static/app.css` 正常 |

## 项目概述

这是一个基于 Python 的工单流转系统，目标是同时支持：

- Web 管理页面：给人工创建、查看、指派、验收工单使用。
- REST API：给外部系统或前端调用。
- MCP 工具：给 AI Agent 直接查询和操作工单。
- 钉钉机器人：后续在群聊内创建、查询、流转工单。

MVP 的核心闭环已经形成：创建工单 -> 指派处理 -> 提交验收 -> 验收通过或退回。

## 技术栈

| 模块 | 技术 | 当前使用情况 |
|------|------|--------------|
| Web 框架 | FastAPI 0.136.3 / Starlette 1.2.1 | 应用入口、REST API、页面路由；模板响应使用 Starlette 1.x 新签名 |
| ORM | SQLAlchemy 2.0.36 | 数据模型、Session、基础查询 |
| 数据库 | SQLite 默认，可切 MySQL | 默认连接串为 `sqlite:///./ticket.db` |
| 页面模板 | Jinja2 3.1.4 | Web 管理页面 |
| 静态资源 | CSS | `web/static/app.css` |
| MCP | MCP SDK 1.27.2 / FastMCP | `mcp_server/server.py` 提供 stdio 工具服务 |
| 钉钉预留 | FastAPI route + httpx 依赖 | webhook 路由已建立，真实 API 客户端待实现 |
| 配置 | pydantic-settings + `.env` | 支持环境变量覆盖 |

## 本地开发启动

### 1. 准备 Python 版本

项目使用 `pyenv` 管理 Python 版本，根目录 `.python-version` 指定为 `3.11.12`。

```bash
pyenv install 3.11.12
python --version
```

确认输出为 `Python 3.11.x` 后继续。

### 2. 安装依赖

建议在项目目录创建本地虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

### 3. 初始化数据库和测试数据

```bash
python -m scripts.seed_data
```

该脚本会创建示例部门、用户和工单。数据库表会在应用启动或 seed 时通过 SQLAlchemy 自动创建。

### 4. 启动 Web 服务

```bash
uvicorn main:app --reload --port 8000
```

如果当前环境不支持文件监听，去掉 `--reload`：

```bash
uvicorn main:app --port 8000
```

访问：

- Web 首页：`http://localhost:8000`
- API 文档：`http://localhost:8000/docs`

### 5. 启动 MCP 服务

```bash
python -m cli mcp
```

## 项目结构

```text
ticket-system/
├── main.py                      # FastAPI 应用入口
├── cli.py                       # 命令行入口，目前用于启动 MCP
├── config.py                    # 配置管理，支持 .env
├── .python-version              # pyenv 使用的 Python 版本
├── requirements.txt             # Python 依赖
├── README.md                    # 面向使用者的启动和使用说明
├── DEVELOPMENT.md               # 当前开发文档
├── TODO.md                      # 阶段计划和待办
│
├── api/
│   ├── api_routes.py            # REST API
│   ├── web_routes.py            # Web 页面路由
│   └── dingtalk_routes.py       # 钉钉 webhook 桩代码
│
├── database/
│   ├── connection.py            # engine、Session、get_db、init_db
│   └── models.py                # Department / User / Ticket / TicketLog
│
├── services/
│   ├── ticket_service.py        # 工单创建、查询、列表、状态流转
│   └── user_service.py          # 用户和部门查询/创建
│
├── mcp_server/
│   └── server.py                # MCP 工具定义
│
├── scripts/
│   └── seed_data.py             # 测试数据填充
│
└── web/
    ├── templates.py             # Jinja2Templates 初始化
    ├── static/app.css           # 页面样式
    └── templates/               # 页面模板
```

## 数据模型

### Department

部门表支持树形结构，并预留钉钉部门 ID。

| 字段 | 说明 |
|------|------|
| `id` | 自增主键 |
| `name` | 部门名称 |
| `dingtalk_dept_id` | 钉钉部门 ID，可为空，唯一 |
| `parent_id` | 父部门 ID，可为空 |

### User

用户表支持普通用户和管理员角色，并预留钉钉用户 ID。

| 字段 | 说明 |
|------|------|
| `id` | 自增主键 |
| `name` | 用户姓名 |
| `dingtalk_user_id` | 钉钉 userId，可为空，唯一 |
| `department_id` | 所属部门 ID，可为空 |
| `role` | `admin` / `user`，默认 `user` |

### Ticket

工单是核心业务实体。

| 字段 | 说明 |
|------|------|
| `id` | 自增主键 |
| `title` | 工单标题 |
| `description` | 工单描述 |
| `status` | `pending` / `in_progress` / `reviewing` / `done` / `closed` |
| `priority` | `low` / `medium` / `high` / `urgent` |
| `creator_id` | 创建人 |
| `assignee_id` | 当前处理人，可为空 |
| `department_id` | 所属部门，可为空 |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |
| `closed_at` | 完成或关闭时间，可为空 |

### TicketLog

记录工单每次关键动作。

| 字段 | 说明 |
|------|------|
| `id` | 自增主键 |
| `ticket_id` | 关联工单 |
| `operator_id` | 操作人 |
| `action` | `create` / `assign` / `reject` / `submit_review` / `approve` / `decline` |
| `comment` | 操作备注，可为空 |
| `created_at` | 操作时间 |

## 工单状态机

```text
创建
  |
  v
pending
  | assign
  v
in_progress
  | submit_review
  v
reviewing
  | approve          -> done
  | decline          -> in_progress

pending
  | reject           -> closed
```

动作矩阵：

| 当前状态 | 动作 | 目标状态 | 当前实现 |
|----------|------|----------|----------|
| `pending` | `assign` | `in_progress` | 支持，可指定处理人 |
| `pending` | `reject` | `closed` | 支持 |
| `in_progress` | `submit_review` | `reviewing` | 支持 |
| `reviewing` | `approve` | `done` | 支持 |
| `reviewing` | `decline` | `in_progress` | 支持 |

## Web 页面

| 路径 | 状态 | 说明 |
|------|------|------|
| `GET /` | 已完成基础版 | 仪表盘，按状态统计工单数量 |
| `GET /tickets` | 已完成基础版 | 工单列表，支持状态筛选和分页参数 |
| `GET /tickets/create` | 已完成基础版 | 创建工单表单 |
| `POST /tickets/create` | 已完成基础版 | 提交创建工单 |
| `GET /tickets/{ticket_id}` | 已完成基础版 | 工单详情、操作日志、可执行动作 |
| `POST /tickets/{ticket_id}/action` | 已完成基础版 | 执行工单状态流转 |
| `GET /users` | 已完成展示版 | 展示用户和部门，增删改待实现 |

已知 Web 待增强点：

- 工单编辑功能未实现。
- 用户/部门页面目前主要是展示，缺少增删改。
- 状态筛选器高亮、分页导航、日志时间线仍可优化。
- 暂无认证授权和 CSRF 保护。

Starlette 1.x 注意事项：

- `Jinja2Templates.TemplateResponse` 使用 `TemplateResponse(request, "template.html", context)`。
- 旧写法 `TemplateResponse("template.html", context)` 会把参数解释错，导致模板渲染异常。

## REST API

| 方法 | 路径 | 状态 | 说明 |
|------|------|------|------|
| `GET` | `/api/tickets` | 已完成 | 工单列表，支持 `status`、`creator_id`、`assignee_id`、`department_id`、分页 |
| `POST` | `/api/tickets` | 已完成 | 创建工单，会校验创建人和部门 |
| `GET` | `/api/tickets/{ticket_id}` | 已完成 | 工单详情和日志 |
| `POST` | `/api/tickets/{ticket_id}/actions/{action}` | 已完成 | 工单状态流转 |
| `GET` | `/api/users` | 已完成 | 用户列表，可按部门过滤 |
| `GET` | `/api/departments` | 已完成 | 部门列表 |
| `POST` | `/api/dingtalk/webhook` | 桩代码 | 当前仅返回固定文本 |

API 当前主要短板：

- 用户/部门缺少完整 CRUD API。
- 工单缺少编辑、搜索、统计接口。
- API 异常处理仍以基础 `ValueError` 转换为主。
- 暂无认证、授权、限流。

## MCP 工具

`mcp_server/server.py` 当前提供以下工具：

| 工具 | 状态 | 说明 |
|------|------|------|
| `create_ticket(title, description, priority)` | 已完成基础版 | 默认使用系统中第一个用户作为创建人 |
| `list_tickets(status)` | 已完成基础版 | 查询工单列表，可按状态筛选 |
| `get_ticket(ticket_id)` | 已完成基础版 | 查看工单详情 |
| `update_ticket_status(ticket_id, action, comment, operator_id)` | 已完成基础版 | 流转工单状态，`operator_id=0` 时回退为创建人 |

MCP 后续建议：

- 创建工单时支持指定创建人、部门、处理人。
- 状态流转时支持 `assign` 指定处理人。
- 输出结构化 JSON 或更稳定的卡片格式，减少自然语言解析成本。
- 增加按关键字、部门、处理人查询工具。

MCP 运行说明：

- 依赖 `mcp==1.27.2`，已写入 `requirements.txt`。
- 项目原来的本地包目录 `mcp/` 已迁移为 `mcp_server/`，避免遮挡外部 MCP SDK 的 `mcp.server.fastmcp`。
- MCP 写操作通过 `database.connection.session_scope()` 管理事务，避免返回成功但未提交落库。

## 钉钉集成状态

当前仅完成入口预留：

- 路由：`POST /api/dingtalk/webhook`
- 请求模型：`DingTalkCallback`
- 返回：固定文本 `收到消息，功能开发中...`

尚未实现：

- 钉钉签名验证。
- access token 获取和缓存。
- 机器人消息发送。
- 部门和用户同步。
- 群聊内自然语言创建/查询工单。
- 交互式卡片和回调动作处理。

钉钉真实接入前需要 HTTPS 公网地址，并在钉钉开放平台配置机器人消息接收 URL。

## 配置说明

默认配置在 `config.py`：

```python
app_name = "钉钉工单系统"
app_version = "0.1.0"
database_url = "sqlite:///./ticket.db"
dingtalk_app_key = ""
dingtalk_app_secret = ""
dingtalk_agent_id = 0
dingtalk_robot_code = ""
```

可在项目根目录创建 `.env` 覆盖：

```env
DATABASE_URL=sqlite:///./ticket.db
DINGTALK_APP_KEY=
DINGTALK_APP_SECRET=
DINGTALK_AGENT_ID=0
DINGTALK_ROBOT_CODE=
```

切换 MySQL 时，连接串示例：

```env
DATABASE_URL=mysql+pymysql://用户名:密码@localhost/数据库名
```

注意：`requirements.txt` 当前没有 `pymysql`，正式切换 MySQL 前需要补充驱动依赖，并建议启用 Alembic 迁移。

## 当前已知风险

| 风险 | 影响 | 建议 |
|------|------|------|
| 无认证授权 | 任意访问者可操作工单 | Phase 5 增加登录、角色权限或 API Key |
| 无 CSRF 保护 | Web 表单存在跨站提交风险 | Web 表单引入 CSRF token |
| 钉钉 webhook 无签名验证 | 无法确认请求来源 | 钉钉接入时优先实现 |
| 无正式迁移体系 | 数据模型演进风险 | 引入 Alembic revision，不只依赖 `create_all` |
| 缺少 Web/API 集成测试 | 页面和接口升级时仍可能有回归 | 为关键 Web 表单、REST API 和静态资源增加集成测试 |

## 当前验证记录

最近一次验证环境：

| 项目 | 结果 |
|------|------|
| Python | `3.11.12`（pyenv，来自 `.python-version`） |
| pip 依赖检查 | `python -m pip check` 通过 |
| 单元测试 | `python -m unittest discover`，10 tests OK |
| FastAPI / MCP 导入 | `main.app` 与 `mcp_server.server` 可正常导入 |
| 本地服务 | `python -m uvicorn main:app --port 9255` 启动成功 |
| 首页 | `GET http://127.0.0.1:9255/` 返回 200 |
| 用户 API | `GET http://127.0.0.1:9255/api/users` 返回种子用户 |
| 静态资源 | `GET http://127.0.0.1:9255/static/app.css` 返回 200 |

当前 Codex 沙箱环境中 `--reload` 文件监听和端口绑定可能受限；用本机 zsh 授权环境启动可以正常监听端口。真实终端可按常规方式运行。

## 下一步开发建议

### Phase 2：Web 页面增强

优先级建议：

1. 增加工单编辑：标题、描述、优先级、部门。
2. 优化分页导航和状态筛选高亮。
3. 用户/部门管理支持新增、编辑、删除。
4. 操作日志时间线展示前后状态和备注。
5. 仪表盘增加简单图表和最近工单列表。

### Phase 3：钉钉集成

优先级建议：

1. 实现钉钉签名验证。
2. 实现 access token 获取、缓存和刷新。
3. 实现部门/用户同步。
4. 实现机器人发送文本消息。
5. 实现群聊创建工单、查询工单、查看详情。
6. 实现交互式卡片动作流转。

### Phase 4：MCP 增强

优先级建议：

1. `create_ticket` 支持 `creator_id`、`department_id`。
2. `update_ticket_status` 支持 `assignee_id`。
3. 返回结构化结果，便于 Agent 稳定消费。
4. 增加工单搜索和统计工具。

### Phase 5：生产化

优先级建议：

1. 增加认证授权。
2. 增加 CSRF 保护。
3. 增加 Alembic 迁移。
4. 切换 MySQL 并补齐驱动依赖。
5. 增加 Docker Compose。
6. 增加单元测试和集成测试。
7. 配置 HTTPS 和部署环境。

## 开发注意事项

- 服务层应继续作为业务规则入口，路由层只做参数接收、响应转换和错误处理。
- 状态流转必须通过 `transition_ticket`，避免绕过状态机。
- 创建和流转工单时都应记录 `TicketLog`。
- Web、REST API、MCP 三个入口应共享同一套服务层逻辑。
- 后续接入钉钉时，钉钉用户 ID 应映射到本地 `User.dingtalk_user_id`。
- 生产环境不要继续依赖 `Base.metadata.create_all` 管理表结构，应切换到 Alembic。
