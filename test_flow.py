import requests
import json
import time

BASE_URL = "http://localhost:8001"

def test_plugin_flow():
    """测试插件完整流程"""
    print("🧪 测试插件流程...")
    
    # 1. 创建绑定会话
    response = requests.post(f"{BASE_URL}/api/auth/session")
    session = response.json()
    print(f"✅ 创建会话: {session['session_id']}")
    
    # 2. 获取小程序码
    qr_response = requests.get(f"{BASE_URL}/api/auth/qr/{session['session_id']}")
    print(f"✅ 获取小程序码: {qr_response.status_code}")
    
    # 3. 检查绑定状态（未绑定）
    status_response = requests.get(f"{BASE_URL}/api/auth/session/{session['session_id']}")
    status = status_response.json()
    print(f"✅ 绑定状态: {status['bound']}")
    
    return session['session_id']

def test_miniprogram_flow(session_id):
    """测试小程序绑定流程"""
    print("\n🧪 测试小程序流程...")
    
    # 模拟小程序登录（使用测试code）
    test_code = "test_code_123"
    bind_data = {
        "session_id": session_id,
        "code": test_code
    }
    
    # 调用绑定接口
    bind_response = requests.post(
        f"{BASE_URL}/api/mini/bind",
        json=bind_data
    )
    print(f"✅ 小程序绑定: {bind_response.status_code}")
    
    # 检查绑定状态（已绑定）
    status_response = requests.get(f"{BASE_URL}/api/auth/session/{session_id}")
    status = status_response.json()
    print(f"✅ 绑定状态: {status['bound']}")
    print(f"✅ 用户ID: {status.get('user_id', '未获取')}")
    
    return status.get('user_id')

def test_submit_content(user_id):
    """测试插件提交内容"""
    print("\n🧪 测试内容提交...")
    
    submit_data = {
        "user_id": user_id,
        "url": "https://example.com/test",
        "title": "测试页面",
        "content": "这是测试内容",
        "batch_id": "test_batch_001"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/plugin/submit",
        json=submit_data
    )
    
    print(f"✅ 提交内容: {response.status_code}")
    result = response.json()
    print(f"✅ 任务ID: {result.get('task_id')}")
    
    return result.get('task_id')

def test_query_results(user_id):
    """测试查询结果"""
    print("\n🧪 测试查询结果...")
    
    # 等待AI处理
    time.sleep(2)
    
    response = requests.get(
        f"{BASE_URL}/api/query-result",
        params={"user_id": user_id}
    )
    
    results = response.json()
    print(f"✅ 查询结果: {len(results.get('results', []))} 条记录")
    
    for item in results.get('results', []):
        print(f"  - {item.get('title')}: {item.get('status')}")

def main():
    print("🚀 开始完整流程测试")
    print("=" * 50)
    
    try:
        # 测试插件流程
        session_id = test_plugin_flow()
        
        # 测试小程序绑定
        user_id = test_miniprogram_flow(session_id)
        
        if user_id:
            # 测试内容提交
            test_submit_content(user_id)
            
            # 测试查询结果
            test_query_results(user_id)
        
        print("\n" + "=" * 50)
        print("🎉 所有测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    main()