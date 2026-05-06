from fastapi import HTTPException, Depends
from fastapi.routing import APIRouter
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models import AnalysisResult
from utils import format_analysis_result

router = APIRouter()

# 请求模型
class FavoriteRequest(BaseModel):
    task_id: str
    favorite: bool

@router.get("")
async def query_result(
    task_id: str = None,
    user_id: str = None,
    favorite: bool | None = None,
    db: Session = Depends(get_db)
):
    """查询任务结果（支持按task_id单查，或按user_id查所有）"""
    if not task_id and not user_id:
        raise HTTPException(status_code=400, detail="必须提供task_id或user_id")

    try:
        query = db.query(AnalysisResult)
        if task_id:
            # 按task_id查询单个记录
            result = query.filter(AnalysisResult.task_id == task_id).first()
            if not result:
                return {
                    "code": 404,
                    "message": "未找到该任务结果"
                }
            results = [result]  # 包装成列表
        else:
            # 按user_id查询所有记录（按创建时间倒序）
            q = query.filter(AnalysisResult.user_id == user_id)
            if favorite is True:
                q = q.filter(AnalysisResult.favorite == 1)
            elif favorite is False:
                q = q.filter((AnalysisResult.favorite == 0) | (AnalysisResult.favorite == None))
            results = q.order_by(AnalysisResult.create_time.desc()).all()

        # 格式化结果
        formatted_results = [format_analysis_result(r) for r in results]

        return {
            "code": 200,
            "results": formatted_results,
            "count": len(formatted_results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.post("/favorite")
async def set_favorite(request: FavoriteRequest, db: Session = Depends(get_db)):
    """设置某条分析的收藏状态"""
    try:
        result = db.query(AnalysisResult).filter(AnalysisResult.task_id == request.task_id).first()
        if not result:
            raise HTTPException(status_code=404, detail="未找到该任务结果")
        result.favorite = 1 if request.favorite else 0
        db.commit()
        return {"code": 200, "task_id": request.task_id, "favorite": request.favorite}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置失败：{str(e)}")