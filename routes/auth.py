from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import time
import base64
from database import get_db
from user_service import get_or_create_user_by_code
from wechat_service import wechat_service
from redis_session import (
    create_session as redis_create_session,
    get_session,
    update_session,
    delete_session,
)
from config import TEST_MODE, TEST_USER

router = APIRouter()


class CreateSessionRequest(BaseModel):
    pass  # 不需要参数，后端生成session


class SessionInfo(BaseModel):
    session_id: str
    qr_url: str
    qrcode_data: dict  # 小程序码数据
    expires_at: int
    is_test: bool = False  # 是否是测试模式
    test_user_id: str | None = None  # 测试用户ID


class BindRequest(BaseModel):
    session_id: str
    user_id: str  # 小程序登录后获得的user_id


class BindStatus(BaseModel):
    session_id: str
    is_bound: bool
    user_id: str | None = None
    expires_at: int
    remaining_time: int  # 剩余时间（秒）


@router.post("/session", response_model=SessionInfo)
async def create_session_endpoint():
    """创建绑定会话，返回session_id和微信小程序码"""
    # 创建会话
    session_id = redis_create_session()

    # 生成微信小程序码
    qrcode_data = wechat_service.generate_miniprogram_qrcode(session_id)

    if qrcode_data is None:
        raise HTTPException(status_code=500, detail="生成小程序码失败")

    update_session(session_id, {"qrcode_generated": True, "qrcode_data": qrcode_data})

    session = get_session(session_id)
    qr_url = f"https://sakuranightingale.top/api/auth/qr/{session_id}"

    result = {
        "session_id": session_id,
        "qr_url": qr_url,
        "qrcode_data": qrcode_data,
        "expires_at": session["expires_at"],
    }

    # 测试模式：添加测试用户信息
    if TEST_MODE:
        result["is_test"] = True
        result["test_user_id"] = TEST_USER["user_id"]
        # 自动绑定测试用户
        update_session(session_id, {"is_bound": True, "user_id": TEST_USER["user_id"]})
    else:
        result["is_test"] = False

    return result


@router.get("/session/{session_id}", response_model=BindStatus)
async def get_session_status(session_id: str):
    """获取会话状态"""
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    # 计算剩余时间
    current_time = time.time()
    remaining_time = int(session["expires_at"] - current_time)

    return {
        "session_id": session_id,
        "is_bound": session["is_bound"],
        "user_id": session["user_id"],
        "expires_at": session["expires_at"],
        "remaining_time": remaining_time,
    }


@router.post("/bind")
async def bind_user(request: BindRequest, db: Session = Depends(get_db)):
    """兼容性接口：已迁移到 /api/mini/bind"""
    raise HTTPException(
        status_code=410, detail="此接口已弃用，请使用 /api/mini/bind 接口进行绑定"
    )


@router.get("/qr/{session_id}")
async def get_qr_image(session_id: str):
    """获取微信小程序码图片（直接返回图片响应）"""
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    # 检查会话中是否有小程序码数据
    if "qrcode_data" not in session:
        raise HTTPException(status_code=404, detail="小程序码数据不存在")

    # 获取小程序码的base64数据
    qrcode_data = session["qrcode_data"]
    base64_image = qrcode_data.get("base64", "")

    if not base64_image:
        raise HTTPException(status_code=404, detail="小程序码数据不完整")

    # 解析base64数据
    try:
        # 去掉data:image/png;base64,前缀
        if base64_image.startswith("data:image/"):
            base64_image = base64_image.split(",", 1)[1]

        # 解码base64
        image_bytes = base64.b64decode(base64_image)

        # 返回图片响应
        from fastapi.responses import Response

        content_type = "image/png"
        if qrcode_data.get("is_mock"):
            content_type = "image/svg+xml"

        return Response(content=image_bytes, media_type=content_type)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理小程序码失败: {str(e)}")


@router.get("/qr-info/{session_id}")
async def get_qr_info_json(session_id: str):
    """获取二维码信息（JSON格式，包含小程序码数据）"""
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    # 返回完整的二维码信息
    return {
        "code": 200,
        "session_id": session_id,
        "is_bound": session["is_bound"],
        "expires_at": session["expires_at"],
        "qrcode_data": session.get("qrcode_data", {}),
        "remaining_time": max(0, session["expires_at"] - int(time.time())),
    }


@router.get("/bind-page/{session_id}")
async def bind_page(session_id: str):
    """绑定页面（小程序扫码后打开的页面）"""
    session = get_session(session_id)
    if session is None:
        from fastapi.responses import HTMLResponse

        return HTMLResponse(content="<h1>会话不存在或已过期</h1>")

    # 简单的HTML页面，引导用户在小程序中操作
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>绑定插件</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
            .container {{ max-width: 400px; margin: 0 auto; }}
            .success {{ color: green; }}
            .error {{ color: red; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>绑定Chrome插件</h1>
            <p>会话ID: <code>{session_id}</code></p>
            <p>请在微信小程序中完成绑定操作</p>
            <p>绑定后，插件将自动获取用户信息</p>
        </div>
    </body>
    </html>
    """

    from fastapi.responses import HTMLResponse

    return HTMLResponse(content=html_content)
