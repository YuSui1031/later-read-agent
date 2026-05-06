#!/usr/bin/env python
"""
数据迁移脚本：将analysis_results表中的user_id从插件本地ID更新为数据库用户ID
"""
import sqlite3
import os
from sqlalchemy import create_engine, text
from config import DATABASE_URL

def migrate_user_ids():
    """迁移用户ID：将插件本地ID替换为数据库用户ID"""
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    
    with engine.connect() as conn:
        # 1. 获取所有用户记录
        users_result = conn.execute(text("SELECT id, plugin_id FROM users"))
        users = users_result.fetchall()
        
        user_map = {}
        for user_id, plugin_id in users:
            if plugin_id:
                user_map[plugin_id] = user_id
        
        print(f"找到 {len(user_map)} 个有plugin_id的用户")
        
        # 2. 获取所有分析记录
        results_result = conn.execute(text("SELECT id, user_id FROM analysis_results"))
        results = results_result.fetchall()
        
        updated_count = 0
        for result_id, old_user_id in results:
            # 如果user_id是插件ID，尝试映射到数据库用户ID
            if old_user_id and old_user_id in user_map:
                new_user_id = user_map[old_user_id]
                conn.execute(
                    text("UPDATE analysis_results SET user_id = :new_id WHERE id = :result_id"),
                    {"new_id": new_user_id, "result_id": result_id}
                )
                updated_count += 1
                print(f"更新记录 {result_id}: {old_user_id} -> {new_user_id}")
            elif old_user_id and old_user_id.startswith("user_"):
                # 这是旧的插件本地ID格式，但没有对应的用户记录
                print(f"警告：记录 {result_id} 的user_id {old_user_id} 没有对应的用户记录")
        
        conn.commit()
        print(f"\n迁移完成！共更新了 {updated_count} 条记录")
        
        # 3. 显示迁移后的统计信息
        stats_result = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN user_id LIKE 'user_%' THEN 1 END) as plugin_ids,
                COUNT(CASE WHEN user_id NOT LIKE 'user_%' AND LENGTH(user_id) = 36 THEN 1 END) as db_ids
            FROM analysis_results
        """))
        stats = stats_result.fetchone()
        print(f"\n迁移后统计:")
        print(f"  总记录数: {stats[0]}")
        print(f"  插件ID格式: {stats[1]}")
        print(f"  数据库ID格式: {stats[2]}")

if __name__ == "__main__":
    print("开始迁移用户ID...")
    migrate_user_ids()
    print("\n迁移完成！")