# AI网页分析后端

基于 FastAPI 的网页内容提取和 AI 分析后端服务，支持 Chrome 插件和微信小程序。

## 需求说明
在信息爆炸的时代，人们查阅资料的时候可能会点开十几个标签页，尽管浏览器允许添加到收藏夹，但可能就再也没有打开过这些网页。该项目允许用户在关闭浏览器前只需一次点击即可把网页内容发送到AI进行摘要提取，而后可以在浏览器或者手机小程序上进行浏览主要内容。进一步地，该项目可以学习用户感兴趣的内容，从而优先推荐重要的未浏览内容

## 项目结构

```
later_read_agent/
├── main.py                 # 应用入口，路由注册
├── config.py              # 配置管理（环境变量）
├── database.py            # 数据库连接和依赖注入
├── models.py              # SQLAlchemy 数据模型
├── ai_service.py          # AI 分析服务
├── utils.py               # 工具函数
├── routes/                # API 路由模块
│   ├── __init__.py
│   ├── plugin.py          # 插件相关接口
│   ├── mini_program.py    # 小程序相关接口
│   ├── query.py           # 查询结果接口
│   └── history.py         # 历史记录页面
├── retrieve_web_content/  # Chrome 插件前端
├── requirements.txt       # Python 依赖
├── .env.example          # 环境变量示例
└── ai_web_analyzer.db    # SQLite 数据库文件
```

## 安装和运行

1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境变量**：
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入实际的 API Key 和配置
   ```

3. **运行服务**：
   ```bash
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

- `DEEPSEEK_API_KEY` - DeepSeek API Key
- `WECHAT_APPID` - 微信小程序 AppID
- `WECHAT_APPSECRET` - 微信小程序 AppSecret
- `DATABASE_URL` - 数据库连接字符串
- `DEBUG` - 调试模式

## 开发说明

代码已按功能模块化组织：
- **配置管理**：`config.py`
- **数据库操作**：`database.py`
- **业务逻辑**：`routes/` 下的各个模块
- **工具函数**：`utils.py`
- **AI 服务**：`ai_service.py`
- **收藏功能**：在 `AnalysisResult` 中增加 `favorite` 字段，历史页面可收藏/筛选

每个模块职责单一，便于维护和扩展。