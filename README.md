# 错题本（Error Notebook）

基于 AI 视觉识别的智能错题整理与复习系统。拍照上传错题，自动识别题目、公式、图形并结构化存储，结合艾宾浩斯遗忘曲线生成科学复习计划，帮助孩子高效攻克薄弱知识点。

## ✨ 核心功能

- **AI 拍照识题** — 上传错题照片，调用 Qwen-VL-Max 自动提取题目正文、LaTeX 公式、SVG 图形、学生答案、正确答案、错因分类与解题分析，支持一图多题。
- **艾宾浩斯复习** — 每道错题自动生成 6 轮复习计划（1/2/4/7/15/30 天），根据掌握程度（1-5 星）动态调整间隔，真正实现个性化复习。
- **PDF 导出** — 按科目/标签/日期筛选错题导出 PDF，一键生成月度学习报告。
- **统计分析** — 错题总量、科目分布、错因占比、录入趋势、掌握程度分布，学习情况一目了然。
- **复习提醒** — 每日 8:00 自动推送今日待复习提醒（微信订阅消息 / Server酱 / 企业微信机器人）。
- **多孩子管理** — 一个家长账号可管理多个孩子的错题，数据隔离。

## 🏗️ 项目结构

```
error-notebook/
├── backend/                # FastAPI 后端
│   ├── api/                # 路由层
│   │   ├── auth.py         # 微信登录 + JWT
│   │   ├── errors.py       # 错题上传/列表/详情/修改/删除
│   │   ├── review.py       # 复习计划（今日/未来/完成）
│   │   ├── export.py       # PDF 导出 + 月度报告
│   │   ├── stats.py        # 统计概览/趋势/掌握分布
│   │   ├── users.py        # 用户信息
│   │   ├── notify.py       # 消息通知
│   │   └── children.py     # 孩子管理
│   ├── models/             # SQLAlchemy 数据模型
│   │   ├── user.py
│   │   ├── error_question.py
│   │   ├── review_plan.py
│   │   └── child.py
│   ├── services/           # 业务服务层
│   │   ├── qwen_vl.py      # Qwen-VL 图片识别
│   │   ├── ebbinghaus.py   # 遗忘曲线算法
│   │   ├── image_processor.py
│   │   ├── pdf_exporter.py # WeasyPrint PDF 渲染
│   │   ├── scheduler.py    # APScheduler 定时任务
│   │   ├── notifier.py     # Server酱/企业微信推送
│   │   ├── wx_subscribe.py # 微信订阅消息
│   │   ├── task_queue.py   # 异步任务队列
│   │   └── oss_storage.py  # 阿里云 OSS（可选）
│   ├── alembic/            # 数据库迁移
│   └── tests/              # pytest 测试
├── miniprogram/            # 微信小程序前端
│   ├── pages/              # 首页/上传/错题列表/详情/复习/统计/导出/我的
│   ├── utils/              # api 请求 / auth 登录 / 工具函数
│   └── components/
├── docs/                   # 开发文档
├── docker-compose.yml      # PostgreSQL + 后端
└── Makefile                # 常用命令快捷方式
```

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + Uvicorn（全异步） |
| 数据库 | PostgreSQL 16 + SQLAlchemy 2.0（async） + Alembic |
| AI 识别 | Qwen-VL-Max（阿里云 DashScope） |
| 图片处理 | OpenCV（透视矫正 / 预处理） |
| PDF 生成 | WeasyPrint + Jinja2 |
| 定时任务 | APScheduler |
| 认证 | 微信小程序登录（code2session）+ JWT |
| 前端 | 微信小程序原生开发 |
| 部署 | Docker Compose |

## 🚀 快速开始

### 环境要求

- Python 3.11+
- PostgreSQL 16
- Node.js（仅小程序开发者工具需要）
- 微信开发者工具

### 1. 克隆项目

```bash
git clone <repo-url>
cd error-notebook
```

### 2. 启动数据库

```bash
make db-up          # docker-compose 启动 PostgreSQL
```

### 3. 配置后端环境变量

复制并编辑 `backend/.env`：

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/error_notebook
DASHSCOPE_API_KEY=sk-your-dashscope-key   # 阿里云百炼 API Key
WX_APPID=your-wx-appid                     # 微信小程序 AppID
WX_SECRET=your-wx-secret                   # 微信小程序 Secret
```

### 4. 安装依赖并运行

```bash
make install       # pip install -r requirements.txt
make migrate-init  # 生成初始迁移（首次）
make migrate-up    # 执行迁移
make run           # uvicorn main:app --reload
```

后端启动后访问 http://localhost:8000，API 文档见 http://localhost:8000/docs。

### 5. 运行小程序

1. 打开微信开发者工具，导入 `miniprogram/` 目录。
2. 修改 `miniprogram/utils/api.js` 中的 `BASE_URL` 为后端地址。
3. 填入小程序 AppID。

### 6. 运行测试

```bash
make test          # pytest tests/ -v
```

## 📡 API 概览

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 认证 | POST | `/api/auth/login` | 微信 code 换取 JWT |
| 错题 | POST | `/api/errors/upload` | 上传图片，同步识别 |
| 错题 | POST | `/api/errors/upload/async` | 异步上传，返回 task_id |
| 错题 | GET | `/api/errors/upload/status/{task_id}` | 查询异步任务状态 |
| 错题 | GET | `/api/errors` | 错题列表（科目/标签/孩子筛选） |
| 错题 | GET | `/api/errors/{id}` | 错题详情 |
| 错题 | PUT | `/api/errors/{id}` | 修改错题（手动纠正） |
| 错题 | DELETE | `/api/errors/{id}` | 软删除 |
| 复习 | GET | `/api/review/today` | 今日待复习 |
| 复习 | GET | `/api/review/upcoming` | 未来 N 天计划 |
| 复习 | POST | `/api/review/{plan_id}/complete` | 完成复习（评分 1-5） |
| 导出 | GET | `/api/export/pdf` | 导出错题 PDF |
| 导出 | GET | `/api/export/monthly-report` | 导出月度报告 |
| 统计 | GET | `/api/stats/summary` | 统计概览 |
| 统计 | GET | `/api/stats/trend` | 录入趋势 |
| 统计 | GET | `/api/stats/mastery` | 掌握程度分布 |

> 认证方式：请求头 `Authorization: Bearer <JWT>`，登录后获取。

## 🐳 Docker 部署

```bash
docker-compose up -d    # 一键启动 PostgreSQL + 后端
```

## 📐 核心算法

### 艾宾浩斯遗忘曲线

新增错题时自动生成 6 轮复习计划，间隔天数为 `[1, 2, 4, 7, 15, 30]`。完成复习时根据掌握程度动态调整下一轮间隔：

| 掌握程度 | 调整策略 |
|---------|---------|
| 1-2 星（不会） | 间隔减半，尽快重练 |
| 3 星（基本掌握） | 保持原始间隔 |
| 4-5 星（熟练） | 间隔延长 1.5 倍 |

### Qwen-VL 识别

上传图片经 OpenCV 预处理（可选透视矫正）后，调用 Qwen-VL-Max 多模态模型，通过结构化 Prompt 输出 JSON 数组，包含题目正文、LaTeX 公式、SVG 图形重绘、错因分类与解题分析。内置多策略 JSON 解析容错与重试机制。

## 🔧 Makefile 命令

| 命令 | 说明 |
|------|------|
| `make install` | 安装 Python 依赖 |
| `make db-up` | 启动 PostgreSQL |
| `make db-down` | 停止并移除容器 |
| `make run` | 启动后端（热重载） |
| `make test` | 运行测试 |
| `make migrate msg="描述"` | 生成迁移脚本 |
| `make migrate-up` | 执行迁移 |
| `make migrate-down` | 回滚一次迁移 |

## 📄 License

MIT
