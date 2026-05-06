import redis
import json
import time
import secrets
import string

# Redis 连接
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

SESSION_PREFIX = "session:"
SESSION_EXPIRE = 600  # 10分钟

def generate_session_id(length=16):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def create_session():
    """创建会话，返回 session_id"""
    session_id = generate_session_id()
    session_data = {
        "is_bound": False,
        "user_id": None,
        "expires_at": int(time.time()) + SESSION_EXPIRE,
        "created_at": int(time.time()),
        "qrcode_generated": False
    }
    redis_client.setex(
        SESSION_PREFIX + session_id,
        SESSION_EXPIRE,
        json.dumps(session_data)
    )
    return session_id

def get_session(session_id):
    """获取会话，不存在或过期返回 None"""
    data = redis_client.get(SESSION_PREFIX + session_id)
    if data is None:
        return None
    session = json.loads(data)
    if time.time() > session["expires_at"]:
        delete_session(session_id)
        return None
    return session

def update_session(session_id, updates: dict):
    """更新会话字段"""
    session = get_session(session_id)
    if session is None:
        return False
    session.update(updates)
    ttl = redis_client.ttl(SESSION_PREFIX + session_id)
    if ttl > 0:
        redis_client.setex(
            SESSION_PREFIX + session_id,
            ttl,
            json.dumps(session)
        )
    return True

def delete_session(session_id):
    """删除会话"""
    redis_client.delete(SESSION_PREFIX + session_id)
