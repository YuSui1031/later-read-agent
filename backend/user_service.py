"""
统一的用户服务
处理微信登录、用户创建/查找
"""

from sqlalchemy.orm import Session
from models import User
from wechat_service import wechat_service
from config import TEST_MODE, TEST_USER


def get_openid_from_code(code: str) -> str:
    """通过微信code获取openid（使用wechat_service）"""
    # 测试模式：直接返回测试openid
    if TEST_MODE:
        print(f"[TEST_MODE] 使用测试openid: {TEST_USER['openid']}")
        return TEST_USER["openid"]

    try:
        user_info = wechat_service.get_user_info_by_code(code)
        return user_info["openid"]
    except Exception as e:
        raise Exception(f"获取OpenID失败：{str(e)}")


def get_or_create_user_by_code(code: str, db: Session) -> User:
    """通过微信code获取或创建用户"""
    openid = get_openid_from_code(code)
    return get_or_create_user_by_openid(openid, db)


def get_or_create_user_by_openid(openid: str, db: Session) -> User:
    """通过openid获取或创建用户"""
    # 测试模式：使用固定的测试user_id
    if TEST_MODE and openid == TEST_USER["openid"]:
        user = db.query(User).filter(User.openid == openid).first()
        if not user:
            user = User(id=TEST_USER["user_id"], openid=openid)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    user = db.query(User).filter(User.openid == openid).first()

    if not user:
        user = User(openid=openid)
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


def get_user_by_id(user_id: str, db: Session) -> User | None:
    """通过用户ID获取用户"""
    return db.query(User).filter(User.id == user_id).first()
