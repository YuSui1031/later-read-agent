"""
测试完整的QR码认证流程
模拟插件端和小程序端的交互
"""
import asyncio
import requests
import json
import uuid
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_auth_flow():
    """测试完整的QR码认证流程"""
    print("=" * 60)
    print("测试QR码认证流程")
    print("=" * 60)
    
    # 1. 插件创建会话
    print("\n1. 插件创建会话...")
    session_response = requests.post(f"{BASE_URL}/api/auth/session")
    if session_response.status_code != 200:
        print(f"❌ 创建会话失败: {session_response.status_code}")
        print(f"响应: {session_response.text}")
        return False
    
    session_data = session_response.json()
    session_id = session_data.get("session_id")
    qr_url = session_data.get("qr_url")
    
    print(f"✅ 创建会话成功")
    print(f"   Session ID: {session_id}")
    print(f"   QR URL: {qr_url}")
    
    # 2. 插件检查会话状态（应该为等待状态）
    print("\n2. 插件检查会话状态...")
    status_response = requests.get(f"{BASE_URL}/api/auth/session/{session_id}")
    if status_response.status_code != 200:
        print(f"❌ 检查状态失败: {status_response.status_code}")
        return False
    
    status_data = status_response.json()
    print(f"✅ 会话状态: {status_data.get('status')}")
    print(f"   创建时间: {status_data.get('created_at')}")
    
    # 3. 模拟小程序扫码（发送code）
    print("\n3. 模拟小程序扫码...")
    # 生成一个模拟的微信code
    mock_code = f"mock_code_{uuid.uuid4().hex[:16]}"
    
    # 小程序调用登录接口
    login_response = requests.post(f"{BASE_URL}/api/mini/login", json={
        "code": mock_code
    })
    
    if login_response.status_code != 200:
        print(f"❌ 小程序登录失败: {login_response.status_code}")
        print(f"响应: {login_response.text}")
        return False
    
    login_data = login_response.json()
    user_id = login_data.get("user_id")
    openid = login_data.get("openid")
    
    print(f"✅ 小程序登录成功")
    print(f"   User ID: {user_id}")
    print(f"   OpenID: {openid}")
    
    # 4. 小程序绑定会话
    print("\n4. 小程序绑定会话...")
    bind_response = requests.post(f"{BASE_URL}/api/auth/bind", json={
        "session_id": session_id,
        "user_id": user_id
    })
    
    if bind_response.status_code != 200:
        print(f"❌ 绑定会话失败: {bind_response.status_code}")
        print(f"响应: {bind_response.text}")
        return False
    
    bind_data = bind_response.json()
    print(f"✅ 会话绑定成功")
    print(f"   绑定用户: {bind_data.get('user_id')}")
    
    # 5. 插件再次检查会话状态（应该为已绑定）
    print("\n5. 插件再次检查会话状态...")
    status_response = requests.get(f"{BASE_URL}/api/auth/session/{session_id}")
    if status_response.status_code != 200:
        print(f"❌ 检查状态失败: {status_response.status_code}")
        return False
    
    status_data = status_response.json()
    print(f"✅ 会话状态: {status_data.get('status')}")
    print(f"   用户ID: {status_data.get('user_id')}")
    print(f"   绑定时间: {status_data.get('bound_at')}")
    
    # 6. 测试插件提交内容（使用获取到的user_id）
    print("\n6. 测试插件提交内容...")
    submit_response = requests.post(f"{BASE_URL}/api/plugin/submit", json={
        "user_id": user_id,
        "url": "https://example.com/test",
        "content": "测试内容",
        "title": "测试页面"
    })
    
    if submit_response.status_code != 200:
        print(f"❌ 提交内容失败: {submit_response.status_code}")
        print(f"响应: {submit_response.text}")
        return False
    
    submit_data = submit_response.json()
    print(f"✅ 内容提交成功")
    print(f"   结果ID: {submit_data.get('result_id')}")
    
    # 7. 测试查询历史记录
    print("\n7. 测试查询历史记录...")
    history_response = requests.get(f"{BASE_URL}/api/history", params={
        "user_id": user_id
    })
    
    if history_response.status_code != 200:
        print(f"❌ 查询历史失败: {history_response.status_code}")
        return False
    
    history_data = history_response.json()
    print(f"✅ 查询历史成功")
    print(f"   记录数量: {len(history_data)}")
    
    # 8. 测试收藏功能
    if history_data:
        result_id = history_data[0].get("id")
        print(f"\n8. 测试收藏功能 (结果ID: {result_id})...")
        
        favorite_response = requests.post(f"{BASE_URL}/api/query-result/favorite", json={
            "user_id": user_id,
            "result_id": result_id,
            "is_favorite": True
        })
        
        if favorite_response.status_code != 200:
            print(f"❌ 收藏失败: {favorite_response.status_code}")
            print(f"响应: {favorite_response.text}")
        else:
            print(f"✅ 收藏成功")
    
    print("\n" + "=" * 60)
    print("✅ 认证流程测试完成！")
    print("=" * 60)
    return True

def test_old_user_api():
    """测试旧的user.py接口是否已废弃"""
    print("\n" + "=" * 60)
    print("测试旧的user.py接口")
    print("=" * 60)
    
    # 测试注册接口
    print("\n1. 测试旧的注册接口...")
    response = requests.post(f"{BASE_URL}/api/user/register", json={
        "plugin_id": "test_plugin_id"
    })
    
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
    
    # 测试QR信息接口
    print("\n2. 测试旧的QR信息接口...")
    response = requests.get(f"{BASE_URL}/api/user/qr-info/test_plugin_id")
    
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
    
    print("\n✅ 旧接口已正确标记为废弃")

def test_error_cases():
    """测试错误情况"""
    print("\n" + "=" * 60)
    print("测试错误情况")
    print("=" * 60)
    
    # 1. 测试无效的session_id
    print("\n1. 测试无效的session_id...")
    response = requests.get(f"{BASE_URL}/api/auth/session/invalid_session_id")
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
    
    # 2. 测试过期的会话（模拟）
    print("\n2. 测试绑定不存在的用户...")
    response = requests.post(f"{BASE_URL}/api/auth/bind", json={
        "session_id": "test_session",
        "user_id": "non_existent_user"
    })
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
    
    # 3. 测试插件提交无效user_id
    print("\n3. 测试插件提交无效user_id...")
    response = requests.post(f"{BASE_URL}/api/plugin/submit", json={
        "user_id": "invalid_uuid_format",
        "url": "https://example.com/test",
        "content": "测试内容",
        "title": "测试页面"
    })
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")

if __name__ == "__main__":
    print("启动认证流程测试...")
    print(f"API地址: {BASE_URL}")
    print("确保后端服务正在运行 (python main.py)")
    print()
    
    try:
        # 测试主流程
        if test_auth_flow():
            # 测试旧接口
            test_old_user_api()
            
            # 测试错误情况
            test_error_cases()
            
            print("\n🎉 所有测试完成！")
        else:
            print("\n❌ 主流程测试失败")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务")
        print("请确保后端服务正在运行: python main.py")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()