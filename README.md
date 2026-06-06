# 🎫 钉钉工单系统

一个基于 Python 的工单系统，支持 Web 管理页面和钉钉机器人操作。

---

## 📦 安装

### 1. 安装 pyenv 和 Python

本项目使用 `pyenv` 管理 Python 版本，项目根目录的 `.python-version` 已指定为 `3.11.12`。

如果还没有安装 `pyenv`，macOS 可以用 Homebrew 安装：

```bash
brew install pyenv
```

安装项目需要的 Python 版本：

```bash
pyenv install 3.11.12
```

进入项目目录后，`pyenv` 会自动读取 `.python-version` 并切换到对应版本。可以用下面的命令确认：

```bash
python --version
```

如果看到 `Python 3.11.x`，说明已经切换好了。

### 2. 下载项目

把项目放到你的电脑上，比如放在 `~/pydata/ticket_system/` 目录。

### 3. 创建虚拟环境并安装依赖库

打开终端，进入项目目录：

```bash
cd ~/pydata/ticket_system
```

创建并启用虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate
```

安装项目需要的 Python 包：

```bash
pip install -r requirements.txt
```

看到 `Successfully installed ...` 就说明装好了。

---

## 🚀 启动系统

### 1. 执行数据库迁移 + 填充测试数据

```bash
# 执行数据库迁移（创建表结构）
python -m cli db upgrade

# 填充测试数据
python -m scripts.seed_data
```

你会看到类似这样的输出：

```
INFO  [alembic.runtime.migration] Running upgrade  -> 0001, ...
测试数据填充完成！
  部门: 未分类(fallback=True), 技术部, 运维部, 业务部
  用户: 张三, 李四, 王五, 赵六
  工单: #1 服务器磁盘空间不足
         #2 新员工入职 - 配置开发环境
         #3 数据库查询慢
```

### 2. 启动 Web 服务

```bash
uvicorn main:app --reload --port 8000
```

看到类似这样的输出就说明启动成功了：

```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 3. 打开浏览器

访问：http://localhost:8000

你会看到工单系统的仪表盘页面。

---

## 🖥️ 使用 Web 页面

### 仪表盘

打开首页 http://localhost:8000，可以看到五个状态的工单数量：

- **待处理** — 新创建的工单，等待指派
- **处理中** — 有人正在处理的工单
- **待验收** — 处理完成，等待创建人确认
- **已完成** — 验收通过的工单
- **已关闭** — 被驳回的工单

### 创建工单

1. 点击顶部导航栏的 **创建工单**
2. 填写标题、描述、创建人、部门、优先级
3. 点击 **创建** 按钮

### 查看工单列表

点击顶部导航栏的 **工单列表**，可以看到所有工单。

上方有筛选按钮：全部 / 待处理 / 处理中 / 待验收 / 已完成 / 已关闭

### 流转工单

点击某个工单的 **详情** 按钮，进入工单详情页。

根据当前状态，你可以执行以下操作：

| 当前状态 | 可以做的操作 | 结果 |
|---------|------------|------|
| 待处理 | **指派** — 选择处理人，点击提交 | 状态变为"处理中" |
| 待处理 | **驳回** — 输入原因，点击提交 | 状态变为"已关闭" |
| 处理中 | **提交验收** — 点击提交 | 状态变为"待验收" |
| 待验收 | **验收通过** — 点击提交 | 状态变为"已完成" |
| 待验收 | **验收不通过** — 输入原因，点击提交 | 状态变为"处理中" |

操作日志会显示在工单详情下方，记录每一步的操作人和时间。

---

## 🤖 使用 MCP（AI 可调用）

如果你使用支持 MCP 的编辑器（如 Cursor、Windsurf、Zed 等），可以让 AI 直接操作工单。

### 启动 MCP 服务

```bash
python -m cli mcp
```

### 可用的工具

AI 可以调用以下功能：

| 功能 | 说明 | 示例 |
|------|------|------|
| create_ticket | 创建工单 | "帮我创建一个工单：服务器磁盘不足" |
| list_tickets | 查看工单列表 | "查看有哪些待处理的工单" |
| get_ticket | 查看工单详情 | "查看工单 #1 的详情" |
| update_ticket_status | 流转工单状态 | "把工单 #1 指派给张三" |

---

## 🔧 配置文件

项目根目录的 `config.py` 里有一些配置项，可以通过 `.env` 文件覆盖。

创建一个 `.env` 文件（和 `main.py` 放在一起）：

```env
DATABASE_URL=sqlite:///./ticket.db
```

以后切换到 MySQL 时，改成：

```env
DATABASE_URL=mysql+pymysql://用户名:密码@localhost/数据库名
```

---

## 📂 项目文件说明

```
ticket-system/
├── main.py                # 启动入口，运行这个文件就能启动 Web 服务
├── config.py              # 配置文件（数据库、钉钉等）
├── requirements.txt       # 依赖库列表
│
├── database/
│   ├── models.py          # 数据模型（工单、用户、部门）
│   └── connection.py      # 数据库连接管理
│
├── services/
│   ├── ticket_service.py  # 工单业务逻辑（创建、查询、流转）
│   └── user_service.py    # 用户/部门业务逻辑
│
├── api/
│   ├── api_routes.py      # REST API 接口
│   ├── web_routes.py      # Web 页面路由
│   └── dingtalk_routes.py  # 钉钉接口（预留）
│
├── mcp_server/
│   └── server.py          # MCP 服务（AI 调用用）
│
├── web/
│   ├── templates/         # 网页模板
│   └── static/            # CSS 样式
│
├── scripts/
│   └── seed_data.py       # 填充测试数据
│
├── alembic/               # 数据库迁移
│   ├── env.py
│   ├── script.py.mako
│   └── versions/          # 迁移版本
│
├── cli.py                 # 命令行工具
├── DEVELOPMENT.md         # 详细开发文档
└── TODO.md                # 待做事项
```

---

## ⚠️ 常见问题

### Q: 启动时报错 `ModuleNotFoundError: No module named 'xxx'`

没有安装依赖，运行：

```bash
pip install -r requirements.txt
```

### Q: 页面打不开

确保 uvicorn 正常运行，浏览器访问 http://localhost:8000

如果端口被占用，可以换一个端口：

```bash
uvicorn main:app --reload --port 8080
```

### Q: sqlite3.OperationalError: unable to open database file

运行 seed 脚本时要在项目根目录下执行：

```bash
cd ~/pydata/ticket_system
python -m scripts.seed_data
```

### Q: 如何重置数据？

删除 `ticket.db` 文件，然后重新执行迁移和 seed：

```bash
rm ticket.db
python -m cli db upgrade
python -m scripts.seed_data
```
