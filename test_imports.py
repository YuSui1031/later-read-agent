"""
测试所有模块的导入是否正确
"""
import sys
import os

def test_imports():
    """测试所有必要的导入"""
    print("测试模块导入...")
    
    modules_to_test = [
        ("fastapi", "FastAPI"),
        ("sqlalchemy.orm", "Session"),
        ("pydantic", "BaseModel"),
        ("models", "User, AnalysisResult"),
        ("database", "get_db"),
        ("config", "MINI_PROGRAM_CONFIG"),
        ("user_service", "get_or_create_user_by_code"),
        ("routes.auth", "router"),
        ("routes.mini_program", "router"),
        ("routes.plugin", "router"),
        ("routes.query", "router"),
        ("routes.history", "router"),
        ("routes.user", "router"),
    ]
    
    all_passed = True
    
    for module_path, imports in modules_to_test:
        try:
            # 动态导入模块
            if module_path.startswith("routes."):
                # 特殊处理routes模块
                module_name = module_path
                exec(f"from {module_path} import router")
                print(f"✅ {module_path}: 导入成功")
            else:
                # 普通模块
                exec(f"import {module_path}")
                print(f"✅ {module_path}: 导入成功")
        except Exception as e:
            print(f"❌ {module_path}: 导入失败 - {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有模块导入成功！")
    else:
        print("❌ 部分模块导入失败")
    
    return all_passed

def test_config():
    """测试配置"""
    print("\n测试配置...")
    
    try:
        from config import MINI_PROGRAM_CONFIG, DEBUG, DATABASE_URL
        
        print(f"✅ 微信APPID: {MINI_PROGRAM_CONFIG.get('APPID', '未设置')}")
        print(f"✅ 调试模式: {DEBUG}")
        print(f"✅ 数据库URL: {DATABASE_URL}")
        
        # 检查微信配置是否完整
        if not MINI_PROGRAM_CONFIG.get('APPID') or not MINI_PROGRAM_CONFIG.get('APPSECRET'):
            print("⚠️ 警告: 微信小程序配置不完整")
            return False
        
        return True
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def test_database():
    """测试数据库连接"""
    print("\n测试数据库连接...")
    
    try:
        from database import engine
        from models import Base
        
        # 尝试创建表（如果不存在）
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库连接成功")
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def test_user_service():
    """测试用户服务"""
    print("\n测试用户服务...")
    
    try:
        from user_service import (
            get_openid_from_code, 
            get_or_create_user_by_code,
            get_or_create_user_by_openid,
            get_user_by_id
        )
        
        print("✅ 用户服务函数导入成功")
        
        # 测试函数签名
        import inspect
        functions = [
            get_openid_from_code,
            get_or_create_user_by_code,
            get_or_create_user_by_openid,
            get_user_by_id
        ]
        
        for func in functions:
            sig = inspect.signature(func)
            print(f"  - {func.__name__}{sig}")
        
        return True
    except Exception as e:
        print(f"❌ 用户服务测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("系统完整性测试")
    print("=" * 60)
    
    results = []
    
    # 运行所有测试
    results.append(("模块导入", test_imports()))
    results.append(("配置检查", test_config()))
    results.append(("数据库", test_database()))
    results.append(("用户服务", test_user_service()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name:15} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！系统可以正常运行。")
        print("\n启动命令:")
        print("  python main.py")
        print("\n测试认证流程:")
        print("  python test_auth_flow.py")
    else:
        print("⚠️  部分测试失败，请检查错误信息。")
    
    sys.exit(0 if all_passed else 1)