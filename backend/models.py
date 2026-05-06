from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.orm import declarative_base
import datetime
import uuid

from database import engine

Base = declarative_base()

# 用户表（关联小程序OpenID）
class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    openid = Column(String(100), unique=True, index=True, comment="小程序OpenID")
    # 插件端本地用户ID，用于将 Chrome 插件和小程序/服务端用户关联
    plugin_id = Column(String(100), unique=True, index=True, nullable=True, comment="插件本地ID，可选")
    create_time = Column(DateTime, default=datetime.datetime.now)

# 分析结果表
class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), comment="关联用户ID（可选，未绑定则为空）")
    task_id = Column(String(32), unique=True, comment="任务唯一标识（插件端生成）")
    title = Column(String(200), comment="网页标题")
    url = Column(Text, comment="网页URL")
    summary = Column(Text, comment="AI摘要")
    categories = Column(String(200), comment="分类标签（逗号分隔）")
    content = Column(Text, comment="原始网页内容")
    status = Column(String(20), default="pending", comment="处理状态：pending/finished/failed")
    create_time = Column(DateTime, default=datetime.datetime.now)
    update_time = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    # 收藏标记（True=已收藏）
    favorite = Column(Integer, default=0, comment="是否收藏，0/1 表示 False/True")
    # 已读标记（True=已读）
    read = Column(Integer, default=0, comment="是否已读，0/1 表示 False/True")

# 创建表（如果列不存在则尝试添加——SQLite在已有表情况下不自动修改）
# Base.metadata.create_all(bind=engine)

# SQLite: 如果数据库已经存在且缺少favorite字段，尝试自动添加
def migrate_database():
    """数据库迁移：添加缺失的列"""
    from sqlalchemy import text

    with engine.connect() as conn:
        # 检查表是否存在
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='analysis_results'"))
        if not result.fetchone():
            # 表不存在，创建表
            Base.metadata.create_all(bind=engine)
            return

        # 检查favorite列是否存在
        try:
            result = conn.execute(text("PRAGMA table_info(analysis_results)"))
            columns = [row[1] for row in result.fetchall()]
            if 'favorite' not in columns:
                print("添加 favorite 列到 analysis_results 表...")
                conn.execute(text("ALTER TABLE analysis_results ADD COLUMN favorite INTEGER DEFAULT 0"))
                conn.commit()
                print("favorite 列添加成功")
            else:
                print("favorite 列已存在")
            # 检查read列是否存在
            if 'read' not in columns:
                print("添加 read 列到 analysis_results 表...")
                conn.execute(text("ALTER TABLE analysis_results ADD COLUMN read INTEGER DEFAULT 0"))
                conn.commit()
                print("read 列添加成功")
            else:
                print("read 列已存在")
        except Exception as e:
            print(f"数据库迁移失败: {e}")

        # 还需要检查 users 表是否存在 plugin_id 列
        try:
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result.fetchall()]
            if 'plugin_id' not in columns:
                print("添加 plugin_id 列到 users 表...")
                # sqlite 不支持直接添加 UNIQUE 约束，此处仅添加列并创建索引
                conn.execute(text("ALTER TABLE users ADD COLUMN plugin_id VARCHAR(100)"))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_plugin_id ON users(plugin_id)"))
                conn.commit()
                print("plugin_id 列添加成功")
            else:
                print("plugin_id 列已存在")
        except Exception as e:
            print(f"数据库迁移（users插件ID）失败: {e}")

# 执行迁移
migrate_database()