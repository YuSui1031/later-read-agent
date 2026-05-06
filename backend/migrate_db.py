#!/usr/bin/env python3
"""
数据库迁移脚本
用于添加缺失的数据库列
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import migrate_database

if __name__ == "__main__":
    print("开始数据库迁移...")
    migrate_database()
    print("迁移完成")