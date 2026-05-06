# 创建一个清理脚本 clean_database.py
import sqlite3

# 连接到数据库
conn = sqlite3.connect('ai_web_analyzer.db')
cursor = conn.cursor()

# 删除所有用户数据（保留表结构）
cursor.execute("DELETE FROM users")
cursor.execute("DELETE FROM analysis_results")

# # 重置自增ID（SQLite需要特殊处理）
# cursor.execute("DELETE FROM sqlite_sequence WHERE name='users'")
# cursor.execute("DELETE FROM sqlite_sequence WHERE name='analysis_results'")

conn.commit()
conn.close()
print("✅ 数据库已清理")