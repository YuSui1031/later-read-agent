# AI网页分析后端

基于 FastAPI 的网页内容提取和 AI 分析后端服务，支持 Chrome 插件和微信小程序。

## 需求说明

在信息爆炸的时代，人们查阅资料的时候可能会点开十几个标签页，尽管浏览器允许添加到收藏夹，但可能就再也没有打开过这些网页。该项目允许用户在关闭浏览器前只需一次点击即可把网页内容发送到AI进行摘要提取，而后可以在浏览器或者手机小程序上进行浏览主要内容。进一步地，该项目可以学习用户感兴趣的内容，从而优先推荐重要的未浏览内容。

## 项目结构

```
later_read_agent/
├── backend/                 # 后端核心代码
│   ├── main.py              # 应用入口，路由注册
│   ├── config.py            # 配置管理（环境变量）
│   ├── database.py          # 数据库连接和依赖注入
│   ├── models.py            # SQLAlchemy 数据模型
│   ├── ai_service.py        # AI 分析服务（DeepSeek API）
│   ├── utils.py             # 工具函数
│   ├── wechat_service.py    # 微信小程序服务
│   ├── user_service.py      # 用户管理服务
│   ├── redis_session.py     # Redis 会话管理
│   ├── .env.example         # 环境变量示例
│   └── clean_database.py    # 数据库清理工具
├── routes/                  # API 路由模块
│   ├── plugin.py            # Chrome 插件相关接口
│   ├── mini_program.py      # 微信小程序相关接口
│   ├── query.py             # 查询结果接口
│   ├── history.py           # 历史记录页面
│   ├── user.py              # 用户接口
│   └── auth.py              # 认证接口
├── miniprogram/             # 微信小程序前端
│   ├── app.js / app.json / app.wxss
│   └── pages/               # 页面（绑定/详情/探索/收藏/历史）
├── retrieve_web_content/    # Chrome 插件前端
│   ├── popup.html / popup.js
│   └── manifest.json
├── requirements.txt         # Python 依赖
├── 开发日志.log              # 开发记录
└── README.md
```

## 安装和运行

1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境变量**：
   ```bash
   cp backend/.env.example backend/.env
   # 编辑 backend/.env 文件，填入实际的 API Key 和配置
   ```

3. **运行服务**（从项目根目录）：
   ```bash
   cd backend
   python main.py
   ```

   服务将在 `http://127.0.0.1:8001` 启动。

## API 接口

### 插件接口 (`/api/plugin`)
- `POST /api/plugin/submit` - 提交网页内容进行分析

### 小程序接口 (`/api/mini`)
- `POST /api/mini/login` - 小程序登录
- `GET /api/mini/results` - 查询分析结果

### 查询接口 (`/api/query-result`)
- `GET /api/query-result` - 查询任务结果
   - 可传递 `user_id`、`task_id` 或 `favorite` 参数过滤（如 `?user_id=xxx&favorite=true`）
   - 返回字段包含 `favorite` 布尔值
   - `POST /api/query-result/favorite` - 设置某条分析的收藏状态，接口接收 JSON `{task_id, favorite}`

### 用户接口 (`/api/user`)
- `POST /api/user/register` - 插件注册/获取统一用户ID，参数 `{local_id}`（或 `plugin_id`），返回 `{user_id}`
- `POST /api/user/bind` - 将已有 `user_id` 与插件本地ID绑定，参数 `{user_id, plugin_id}`

### 历史页面 (`/history`)
- `GET /history?user_id=xxx` - 历史记录页面

## 环境变量

| 变量名 | 说明 |
|--------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API Key |
| `WECHAT_APPID` | 微信小程序 AppID |
| `WECHAT_APPSECRET` | 微信小程序 AppSecret |
| `DATABASE_URL` | 数据库连接字符串 |
| `DEBUG` | 调试模式 |
| `TEST_MODE` | 测试模式（使用模拟账号） |

## 技术栈

- **后端**: FastAPI + SQLAlchemy + uvicorn
- **AI**: DeepSeek API (openai 兼容接口)
- **前端**: Chrome Extension (Vanilla JS) + 微信小程序
- **数据库**: SQLite (开发) / 可切换 PostgreSQL

## License

MIT
