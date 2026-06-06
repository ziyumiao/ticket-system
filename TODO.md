# 钉钉工单系统 — 待办事项

## Phase 1 ✅ 已完成（项目骨架 + 数据层 + 两轮 Review）

- [x] FastAPI 项目结构搭建
- [x] SQLAlchemy 数据模型（Ticket / TicketLog / User / Department）
- [x] SQLite 数据库初始化
- [x] 服务层：create_ticket / get_ticket / list_tickets / transition_ticket
- [x] 服务层：用户/部门 CRUD
- [x] REST API 接口（工单创建/列表/详情/流转 + 用户/部门列表）
- [x] 工单状态机（pending → in_progress → reviewing → done，含驳回/退回）
- [x] Web 管理页面（仪表盘/工单列表/详情/创建/用户管理）
- [x] MCP Server（create / list / get / update）
- [x] 钉钉 Webhook 桩代码
- [x] Seed 测试数据（幂等）
- [x] P0 事务修复：MCP/seed 写操作统一 commit/rollback
- [x] MCP SDK 接入：迁移本地目录为 `mcp_server/`，避免包名遮挡
- [x] 基础单元测试：事务、状态机、MCP 写操作持久化
- [x] 依赖升级：FastAPI 0.136.3 + MCP 1.27.2
- [x] 两轮代码 Review + 16 项修复

## Phase 2 ⏳ Web 页面增强（待开始）

- [ ] 工单编辑功能（修改标题/描述/优先级）
- [ ] 分页导航优化
- [ ] 状态筛选器高亮当前选中
- [ ] 仪表盘图表（状态分布可视化）
- [ ] 用户/部门管理页面增删改
- [ ] 操作日志时间线优化（显示前后状态变化）

## Phase 3 🔜 钉钉集成（待开始）

- [ ] 钉钉开放平台创建企业内部应用
- [ ] 配置机器人消息接收 URL
- [ ] 实现钉钉 API 客户端（httpx）
- [ ] 通讯录同步（部门/用户定时拉取）
- [ ] 钉钉消息发送封装
- [ ] 交互式卡片构建
- [ ] 群聊自然语言创建/查询工单
- [ ] 钉钉回调事件处理
- [ ] 钉钉请求签名验证

## Phase 4 🔜 MCP 增强（待开始）

- [ ] MCP 工具支持指定创建人/处理人
- [ ] MCP 工具支持按关键字搜索
- [ ] MCP 工具返回格式化卡片

## Phase 5 🔜 生产化（待开始）

- [ ] MySQL 数据库切换
- [ ] Alembic 迁移管理
- [ ] Docker Compose 编排
- [ ] HTTPS 配置（钉钉回调需要）
- [ ] 钉钉应用上线审批
- [ ] 认证授权（JWT / API Key）
- [ ] CSRF 保护
- [ ] 用户/部门完整 CRUD API
- [ ] 搜索/统计接口
- [ ] Web/API 集成测试

## 已知待优化项（低优先级）

- [ ] 数据库连接池配置
- [ ] 请求限流
- [ ] 操作日志记录前后状态值
- [ ] 工单关闭原因分类
