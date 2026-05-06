from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import DEBUG
from models import Base, engine
from routes import plugin, mini_program, query, history, user, auth

# 创建数据库表
Base.metadata.create_all(bind=engine)

# ========== 初始化FastAPI应用 ==========
app = FastAPI(title="AI网页分析后端", version="1.0", debug=DEBUG)

# 解决跨域问题（Chrome插件发送请求必须加这个）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境替换成插件ID，格式：chrome-extension://插件ID
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # 明确允许的方法
    allow_headers=["Content-Type", "Authorization", "Accept"],  # 明确允许的请求头
    expose_headers=["Content-Length"],  # 暴露响应头
)

# ========== 注册路由 ==========
app.include_router(plugin, prefix="/api/plugin", tags=["插件接口"])
app.include_router(mini_program, prefix="/api/mini", tags=["小程序接口"])
app.include_router(user, prefix="/api/user", tags=["用户接口"])
app.include_router(auth, prefix="/api/auth", tags=["认证接口"])
app.include_router(query, prefix="/api/query-result", tags=["查询接口"])
app.include_router(history, prefix="/history", tags=["历史页面"])

# ========== 启动后端 ==========
if __name__ == "__main__":
    import uvicorn
    # 启动服务，监听本地8001端口，允许外部访问
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)