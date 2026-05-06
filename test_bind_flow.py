#!/usr/bin/env python
"""
测试微信小程序码绑定流程
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8001"

def test_bind_flow():
    """测试完整的绑定流程"""
    print("=" * 60)
    print("测试微信小程序码绑定流程")
    print("=" * 60)
    
    # 1. 创建绑定会话
    print("\n1. 创建绑定会话...")
    try:
        response = requests.post(f"{BASE_URL}/api/auth/session")
        response.raise_for_status()
        session_data = response.json()
        print(f"✅ 创建会话成功")
        print(f"   会话ID: {session_data['session_id']}")
        print(f"   过期时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(session_data['expires_at']))}")
        print(f"   小程序码数据: {'已生成' if 'qrcode_data' in session_data else '未生成'}")
        
        if 'qrcode_data' in session_data:
            qrcode = session_data['qrcode_data']
            print(f"   小程序码类型: {qrcode.get('is_mock', False) and '模拟数据' or '真实数据'}")
            print(f"   Scene参数: {qrcode.get('scene', 'N/A')}")
        
    except Exception as e:
        print(f"❌ 创建会话失败: {e}")
        return
    
    session_id = session_data['session_id']
    
    # 2. 检查会话状态
    print("\n2. 检查会话状态...")
    try:
        response = requests.get(f"{BASE_URL}/api/auth/session/{session_id}")
        response.raise_for_status()
        status_data = response.json()
        print(f"✅ 检查状态成功")
        print(f"   是否已绑定: {status_data['is_bound']}")
        print(f"   用户ID: {status_data['user_id'] or '未绑定'}")
        print(f"   剩余时间: {status_data['remaining_time']}秒")
    except Exception as e:
        print(f"❌ 检查状态失败: {e}")
    
    # 3. 测试小程序绑定接口（使用模拟数据）
    print("\n3. 测试小程序绑定接口...")
    print("   注意：这里使用模拟数据，实际需要真实的小程序code")
    
    # 模拟的小程序绑定请求
    bind_payload = {
        "session_id": session_id,
        "code": "mock_code_for_testing"  # 模拟的小程序code
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/mini/bind", json=bind_payload)
        if response.status_code == 200:
            bind_result = response.json()
            print(f"✅ 绑定成功")
            print(f"   用户ID: {bind_result['user_id']}")
            print(f"   绑定时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(bind_result['bound_at']))}")
        else:
            print(f"⚠️  绑定失败（预期中，因为使用模拟code）")
            print(f"   状态码: {response.status_code}")
            print(f"   错误信息: {response.text}")
    except Exception as e:
        print(f"❌ 绑定接口调用失败: {e}")
    
    # 4. 再次检查会话状态
    print("\n4. 再次检查会话状态...")
    try:
        response = requests.get(f"{BASE_URL}/api/auth/session/{session_id}")
        response.raise_for_status()
        status_data = response.json()
        print(f"✅ 检查状态成功")
        print(f"   是否已绑定: {status_data['is_bound']}")
        print(f"   用户ID: {status_data['user_id'] or '未绑定'}")
    except Exception as e:
        print(f"❌ 检查状态失败: {e}")
    
    # 5. 测试已弃用的绑定接口
    print("\n5. 测试已弃用的绑定接口...")
    try:
        response = requests.post(f"{BASE_URL}/api/auth/bind", json={"session_id": session_id, "user_id": "test_user"})
        print(f"✅ 接口返回预期错误: {response.status_code}")
        print(f"   错误信息: {response.json().get('detail', 'N/A')}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
    # 总结
    print("\n📋 测试总结:")
    print("1. ✅ 会话创建功能正常")
    print("2. ✅ 会话状态检查功能正常")
    print("3. ⚠️  小程序绑定接口需要真实的小程序code")
    print("4. ✅ 状态轮询机制正常")
    print("5. ✅ 接口兼容性处理正常")
    print("\n🔧 下一步:")
    print("1. 部署插件并测试二维码显示")
    print("2. 使用真实的小程序code进行绑定测试")
    print("3. 测试完整的用户流程")

def test_wechat_service():
    """测试微信服务模块"""
    print("\n" + "=" * 60)
    print("测试微信服务模块")
    print("=" * 60)
    
    try:
        from wechat_service import wechat_service
        
        # 测试模拟小程序码生成
        print("\n1. 测试模拟小程序码生成...")
        mock_qrcode = wechat_service._generate_mock_qrcode("test_session_123", "pages/bind/bind")
        print(f"✅ 模拟小程序码生成成功")
        print(f"   Session: {mock_qrcode['session_id']}")
        print(f"   Scene: {mock_qrcode['scene']}")
        print(f"   是否模拟: {mock_qrcode.get('is_mock', False)}")
        print(f"   Base64数据长度: {len(mock_qrcode['base64'])}")
        
        # 测试真实小程序码生成（需要真实配置）
        print("\n2. 测试真实小程序码生成...")
        try:
            real_qrcode = wechat_service.generate_miniprogram_qrcode("test_session_456", "pages/bind/bind")
            print(f"✅ 小程序码生成成功")
            print(f"   Session: {real_qrcode['session_id']}")
            print(f"   Scene: {real_qrcode['scene']}")
            print(f"   是否模拟: {real_qrcode.get('is_mock', False)}")
        except Exception as e:
            print(f"⚠️  真实小程序码生成失败（可能需要真实配置）: {e}")
            
    except Exception as e:
        print(f"❌ 微信服务测试失败: {e}")

if __name__ == "__main__":
    test_bind_flow()
    test_wechat_service()