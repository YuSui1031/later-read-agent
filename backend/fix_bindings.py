#!/usr/bin/env python
"""
修复绑定关系脚本：
1. 为现有用户创建plugin_id（基于现有的插件本地ID）
2. 将analysis_results表中的user_id更新为数据库用户ID
"""
import sqlite3
import os
import uuid
from sqlalchemy import create_engine, text
from config import DATABASE_URL

def fix_bindings():
    """修复用户绑定关系"""
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    
    with engine.connect() as conn:
        # 1. 获取现有的插件本地ID（从analysis_results表中）
        result = conn.execute(text("SELECT DISTINCT user_id FROM analysis_results WHERE user_id LIKE 'user_%'"))
        plugin_ids = [row[0] for row in result.fetchall()]
        
        print(f"找到 {len(plugin_ids)} 个插件本地ID: {plugin_ids}")
        
        # 2. 获取现有用户
        result = conn.execute(text("SELECT id, openid, plugin_id FROM users"))
        users = result.fetchall()
        
        if not users:
            print("没有找到用户记录，创建新用户...")
            # 创建新用户并绑定第一个插件ID
            if plugin_ids:
                new_user_id = str(uuid.uuid4())
                plugin_id = plugin_ids[0]
                conn.execute(
                    text("INSERT INTO users (id, plugin_id) VALUES (:user_id, :plugin_id)"),
                    {"user_id": new_user_id, "plugin_id": plugin_id}
                )
                conn.commit()
                print(f"创建用户 {new_user_id} 并绑定 plugin_id: {plugin_id}")
                users = [(new_user_id, None, plugin_id)]
            else:
                print("错误：没有插件ID，无法创建用户")
                return
        
        # 3. 为现有用户分配plugin_id（如果还没有）
        for user_id, openid, current_plugin_id in users:
            if not current_plugin_id and plugin_ids:
                # 分配一个未使用的plugin_id
                plugin_id = plugin_ids.pop(0)
                conn.execute(
                    text("UPDATE users SET plugin_id = :plugin_id WHERE id = :user_id"),
                    {"plugin_id": plugin_id, "user_id": user_id}
                )
                print(f"为用户 {user_id} 绑定 plugin_id: {plugin_id}")
        
        conn.commit()
        
        # 4. 更新analysis_results表中的user_id
        result = conn.execute(text("SELECT id, plugin_id FROM users WHERE plugin_id IS NOT NULL"))
        user_map = {plugin_id: user_id for user_id, plugin_id in result.fetchall()}
        
        print(f"\n用户映射关系: {user_map}")
        
        updated_count = 0
        for plugin_id, db_user_id in user_map.items():
            result = conn.execute(
                text("UPDATE analysis_results SET user_id = :db_user_id WHERE user_id = :plugin_id"),
                {"db_user_id": db_user_id, "plugin_id": plugin_id}
            )
            updated_count += result.rowcount
            print(f"更新 {result.rowcount} 条记录: {plugin_id} -> {db_user_id}")
        
        conn.commit()
        
        # 5. 显示统计信息
        print(f"\n修复完成！共更新了 {updated_count} 条记录")
        
        # 显示最终状态
        result = conn.execute(text("SELECT id, openid, plugin_id FROM users"))
        print("\n用户表最终状态:")
        for user_id, openid, plugin_id in result.fetchall():
            print(f"  用户ID: {user_id}, OpenID: {openid}, 插件ID: {plugin_id}")
        
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN user_id LIKE 'user_%' THEN 1 END) as plugin_ids,
                COUNT(CASE WHEN user_id NOT LIKE 'user_%' AND LENGTH(user_id) = 36 THEN 1 END) as db_ids
            FROM analysis_results
        """))
        stats = result.fetchone()
        print(f"\n分析结果表统计:")
        print(f"  总记录数: {stats[0]}")
        print(f"  插件ID格式: {stats[1]}")
        print(f"  数据库ID格式: {stats[2]}")

if __name__ == "__main__":
    print("开始修复绑定关系...")
    fix_bindings()
    print("\n修复完成！")