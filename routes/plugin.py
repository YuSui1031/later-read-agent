from fastapi import HTTPException, Depends
from fastapi.routing import APIRouter
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid
import asyncio
from database import get_db
from models import AnalysisResult
from ai_service import analyze_with_ai
from config import TEST_MODE, TEST_USER

router = APIRouter()


# 请求模型
class PluginSubmitRequest(BaseModel):
    content: str
    url: str
    title: str
    user_id: str = None  # 可选：用户临时ID（插件端生成）


async def process_ai_analysis_async(result_id: str, content: str, db: Session):
    """异步处理AI分析，更新任务状态"""
    try:
        # 模拟AI处理耗时
        ai_result = analyze_with_ai(content)
        # 更新数据库：状态改为finished，填充AI结果
        result = db.query(AnalysisResult).filter(AnalysisResult.id == result_id).first()
        if result:
            result.summary = ai_result["summary"]
            result.categories = ",".join(ai_result["categories"])
            result.status = "finished"
            db.commit()
    except Exception as e:
        # 处理失败，更新状态为failed
        result = db.query(AnalysisResult).filter(AnalysisResult.id == result_id).first()
        if result:
            result.status = "failed"
            result.summary = f"分析失败：{str(e)}"
            db.commit()
    finally:
        db.close()  # 关闭数据库连接


@router.post("/submit")
async def plugin_submit(request: PluginSubmitRequest, db: Session = Depends(get_db)):
    """插件提交内容，立即返回任务ID，异步处理AI分析"""
    try:
        if not request.content:
            raise HTTPException(status_code=400, detail="网页内容不能为空")

        if not request.user_id:
            raise HTTPException(status_code=400, detail="必须提供user_id")

        # 测试模式：允许测试用户ID
        if TEST_MODE and request.user_id == TEST_USER["user_id"]:
            pass  # 测试用户ID，跳过UUID验证
        else:
            # 验证user_id是否是有效的数据库用户ID（UUID格式）
            import re

            uuid_pattern = re.compile(
                r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I
            )
            if not uuid_pattern.match(request.user_id):
                raise HTTPException(
                    status_code=400, detail="无效的用户ID格式，请先绑定用户"
                )

        # 1. 生成唯一任务ID（立即做）
        task_id = str(uuid.uuid4())[:10]
        # 2. 存储原始内容，状态标记为"pending"（处理中）
        result = AnalysisResult(
            task_id=task_id,
            user_id=request.user_id,  # 存储数据库用户ID
            title=request.title,
            url=request.url,
            content=request.content,
            status="pending",  # 初始状态：处理中
            summary="处理中...",
            categories="处理中...",
        )
        db.add(result)
        db.commit()

        # 3. 异步调用AI分析（核心：不阻塞返回）
        # 本地测试：用asyncio.create_task异步执行，生产环境用Celery
        asyncio.create_task(process_ai_analysis_async(result.id, request.content, db))

        # 4. 立即返回，不等待AI结果
        return {
            "code": 200,
            "message": "任务提交成功，正在AI分析中",
            "task_id": task_id,
            "tip": "打开微信小程序即可查看分析结果",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交失败：{str(e)}")
