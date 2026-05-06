"""
⚠️ 已废弃的插件ID绑定接口
新的QR码认证流程不再使用plugin_id绑定
请使用 /api/auth 接口进行用户认证
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import User

router = APIRouter()


class PluginRegisterRequest(BaseModel):
    plugin_id: str


@router.post("/register")
async def register_plugin_user(request: PluginRegisterRequest, db: Session = Depends(get_db)):
    """⚠️ 已废弃：旧的插件ID绑定接口"""
    return {
        "code": 410,  # Gone
        "message": "此接口已废弃，请使用新的QR码认证流程",
        "new_endpoint": "/api/auth/session"
    }


@router.get("/qr-info/{plugin_id}")
async def get_qr_info(plugin_id: str, db: Session = Depends(get_db)):
    """⚠️ 已废弃：旧的二维码信息接口"""
    return {
        "code": 410,
        "message": "此接口已废弃，请使用新的QR码认证流程",
        "new_endpoint": "/api/auth/session"
    }
