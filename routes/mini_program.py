from fastapi import HTTPException, Depends
from fastapi.routing import APIRouter
from pydantic import BaseModel
from sqlalchemy.orm import Session
import time
from database import get_db
from models import AnalysisResult, User
from user_service import get_or_create_user_by_code
from utils import format_mini_result
from redis_session import get_session, update_session, delete_session
from config import TEST_MODE, TEST_USER

router = APIRouter()


# 请求模型
class MiniProgramLoginRequest(BaseModel):
    code: str  # 小程序登录获取的临时code


class MiniProgramBindRequest(BaseModel):
    session_id: str  # 小程序码中的session参数
    code: str  # 小程序登录code，用于获取openid


class MiniProgramSceneBindRequest(BaseModel):
    scene: str  # 小程序码scene参数，格式为"session=xxx"
    code: str | None = None  # 小程序登录code（可选）
    user_id: str | None = None  # 用户ID（可选，小程序端主导绑定时使用）


class UpdateStatusRequest(BaseModel):
    user_id: str
    task_id: str
    read: int | None = None
    favorite: int | None = None


class ClearHistoryRequest(BaseModel):
    user_id: str


@router.post("/login")
async def mini_program_login(
    request: MiniProgramLoginRequest, db: Session = Depends(get_db)
):
    """小程序登录，获取用户ID"""
    try:
        # 测试模式：直接返回测试用户
        if TEST_MODE:
            print(f"[TEST_MODE] 小程序登录使用测试用户: {TEST_USER['user_id']}")
            user = db.query(User).filter(User.openid == TEST_USER["openid"]).first()
            if not user:
                user = User(id=TEST_USER["user_id"], openid=TEST_USER["openid"])
                db.add(user)
                db.commit()
                db.refresh(user)
            return {
                "code": 200,
                "user_id": user.id,
                "openid": user.openid,
                "message": "登录成功（测试模式）",
            }

        # 使用统一的服务获取或创建用户
        user = get_or_create_user_by_code(request.code, db)

        return {
            "code": 200,
            "user_id": user.id,
            "openid": user.openid,
            "message": "登录成功",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登录失败：{str(e)}")


@router.post("/bind")
async def mini_program_bind(
    request: MiniProgramBindRequest, db: Session = Depends(get_db)
):
    """小程序扫码绑定：将用户绑定到会话"""
    try:
        # 1. 验证会话是否存在且未过期
        session = get_session(request.session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="会话不存在或已过期")

        # 检查会话是否已绑定
        if session["is_bound"]:
            raise HTTPException(status_code=400, detail="会话已被其他用户绑定")

        # 测试模式：使用测试用户
        if TEST_MODE:
            user_id = TEST_USER["user_id"]
            print(f"[TEST_MODE] 绑定使用测试用户: {user_id}")
        else:
            # 2. 通过code获取用户信息
            user = get_or_create_user_by_code(request.code, db)
            user_id = user.id

        # 3. 更新会话状态
        update_session(
            request.session_id,
            {"is_bound": True, "user_id": user_id, "bound_at": int(time.time())},
        )

        return {
            "code": 200,
            "message": "绑定成功",
            "user_id": user_id,
            "session_id": request.session_id,
            "bound_at": int(time.time()),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"绑定失败：{str(e)}")


@router.post("/scene-bind")
async def mini_program_scene_bind(
    request: MiniProgramSceneBindRequest, db: Session = Depends(get_db)
):
    """小程序码scene参数绑定：解析scene参数并绑定用户"""
    try:
        # 1. 解析scene参数，格式为"session=xxx"
        scene_params = {}
        for param in request.scene.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                scene_params[key] = value

        session_id = scene_params.get("session")
        if not session_id:
            raise HTTPException(
                status_code=400, detail="scene参数格式错误，缺少session参数"
            )

        # 2. 验证会话是否存在且未过期
        session = get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="会话不存在或已过期")

        # 检查会话是否已绑定
        if session["is_bound"]:
            raise HTTPException(status_code=400, detail="会话已被其他用户绑定")

        # 3. 获取用户ID
        if TEST_MODE:
            # 测试模式：使用测试用户
            user_id = TEST_USER["user_id"]
            print(f"[TEST_MODE] scene-bind 使用测试用户: {user_id}")
        elif request.user_id:
            # 小程序端主导绑定：直接使用传入的 user_id
            user_id = request.user_id
            print(f"[小程序端主导绑定] 使用传入的 user_id: {user_id}")
        elif request.code:
            # 传统方式：通过 code 获取用户
            user = get_or_create_user_by_code(request.code, db)
            user_id = user.id
            print(f"[传统绑定] 通过 code 获取用户: {user_id}")
        else:
            raise HTTPException(status_code=400, detail="缺少 user_id 或 code 参数")

        # 4. 更新会话状态
        update_session(
            session_id,
            {"is_bound": True, "user_id": user_id, "bound_at": int(time.time())},
        )

        return {
            "code": 200,
            "message": "绑定成功",
            "user_id": user_id,
            "session_id": session_id,
            "scene": request.scene,
            "bound_at": int(time.time()),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"绑定失败：{str(e)}")


@router.get("/results")
async def mini_get_results(
    user_id: str,
    status: str | None = None,
    limit: int | None = None,
    db: Session = Depends(get_db),
):
    """小程序查询用户的分析结果，支持按状态筛选"""
    import sys

    try:
        print(
            f"[results] user_id={user_id}, status={status}, limit={limit}", flush=True
        )

        # 基础查询：该用户的所有记录（直接使用数据库用户ID）
        query = db.query(AnalysisResult).filter(AnalysisResult.user_id == user_id)

        # 先看看该用户总共有多少条记录
        total = query.count()
        print(f"[results] 用户 {user_id} 总记录数: {total}", flush=True)

        # 按状态筛选
        if status:
            if status == "unread":
                query = query.filter(AnalysisResult.read == 0)
            elif status == "read":
                query = query.filter(AnalysisResult.read == 1)
            elif status == "favorite":
                query = query.filter(AnalysisResult.favorite == 1)
            else:
                raise HTTPException(
                    status_code=400, detail="status参数必须是unread/read/favorite之一"
                )

        # 按创建时间倒序
        query = query.order_by(AnalysisResult.create_time.desc())

        # 限制条数
        if limit and limit > 0:
            query = query.limit(limit)

        results = query.all()
        print(f"[results] 查询结果数: {len(results)}", flush=True)

        # 格式化结果
        formatted_results = [format_mini_result(r) for r in results]

        return {
            "code": 200,
            "results": formatted_results,
            "count": len(formatted_results),
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[results] 查询失败: {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.post("/update-status")
async def update_status(request: UpdateStatusRequest, db: Session = Depends(get_db)):
    """更新消息的已读/收藏状态"""
    try:
        # 查找记录：直接使用数据库用户ID
        result = (
            db.query(AnalysisResult)
            .filter(
                AnalysisResult.task_id == request.task_id,
                AnalysisResult.user_id == request.user_id,
            )
            .first()
        )

        if not result:
            raise HTTPException(status_code=404, detail="未找到该任务结果")

        # 更新字段
        if request.read is not None:
            result.read = request.read
        if request.favorite is not None:
            result.favorite = request.favorite

        db.commit()

        return {
            "code": 200,
            "task_id": request.task_id,
            "read": result.read,
            "favorite": result.favorite,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新状态失败：{str(e)}")


@router.post("/clear-history")
async def clear_history(request: ClearHistoryRequest, db: Session = Depends(get_db)):
    """清空用户历史（将所有read标记清零）"""
    try:
        # 将该用户所有记录的read标记设为0
        updated = (
            db.query(AnalysisResult)
            .filter(AnalysisResult.user_id == request.user_id)
            .update({"read": 0})
        )

        db.commit()

        return {
            "code": 200,
            "message": f"已清空{updated}条历史记录",
            "cleared_count": updated,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空历史失败：{str(e)}")
