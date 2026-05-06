from models import AnalysisResult


def format_analysis_result(result: AnalysisResult) -> dict:
    """格式化分析结果为字典"""
    return {
        "id": result.id,
        "task_id": result.task_id,
        "title": result.title,
        "url": result.url,
        "summary": result.summary,
        "categories": result.categories.split(",")
        if result.categories != "处理中..."
        else ["处理中..."],
        "status": result.status,
        "create_time": result.create_time.strftime("%Y-%m-%d %H:%M:%S"),
        "favorite": bool(result.favorite),
        "read": bool(result.read),
    }


def format_mini_result(result: AnalysisResult) -> dict:
    """格式化小程序结果"""
    categories = result.categories
    if categories == "处理中...":
        categories_list = ["处理中..."]
    elif categories:
        categories_list = categories.split(",")
    else:
        categories_list = []

    return {
        "id": result.id,
        "task_id": result.task_id,
        "title": result.title,
        "url": result.url,
        "summary": result.summary,
        "categories": categories_list,
        "status": result.status,
        "create_time": result.create_time.strftime("%Y-%m-%d %H:%M"),
        "favorite": bool(result.favorite),
        "read": bool(result.read),
    }


import secrets
import string


def generate_short_id(length=16):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))
