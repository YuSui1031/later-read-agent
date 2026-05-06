#!/usr/bin/env python
"""
微信服务模块：处理真实微信API调用
"""

import requests
import json
import base64
from typing import Optional, Dict, Tuple
from config import MINI_PROGRAM_CONFIG, TEST_MODE
import time


class WechatService:
    """微信服务类（真实API版本）"""

    def __init__(self):
        self.app_id = MINI_PROGRAM_CONFIG["APPID"]
        self.app_secret = MINI_PROGRAM_CONFIG["APPSECRET"]
        self.access_token = None
        self.token_expire_time = 0

    def _get_access_token(self) -> str:
        """获取微信access_token（带缓存）"""
        # 测试模式：返回模拟token
        if TEST_MODE:
            print("[TEST_MODE] 使用模拟access_token")
            return "test_access_token"

        now = time.time()

        # 检查token是否过期（微信token有效期为7200秒）
        if self.access_token and now < self.token_expire_time - 300:  # 提前5分钟刷新
            return self.access_token

        # 获取新token
        url = f"{MINI_PROGRAM_CONFIG['access_token_url']}"
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret,
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "access_token" in data:
                self.access_token = data["access_token"]
                self.token_expire_time = now + data.get("expires_in", 7200)
                print(f"✅ 获取微信access_token成功: {self.access_token[:20]}...")
                return self.access_token
            else:
                raise Exception(f"获取access_token失败: {data}")

        except Exception as e:
            print(f"❌ 获取微信access_token失败: {e}")
            raise

    def get_user_info_by_code(self, code: str) -> Dict:
        """通过code获取用户openid和session_key"""
        # 测试模式：返回测试openid
        if TEST_MODE:
            from config import TEST_USER

            print(f"[TEST_MODE] 返回测试用户信息: {TEST_USER['openid']}")
            return {
                "openid": TEST_USER["openid"],
                "session_key": "test_session_key",
                "unionid": "",
            }

        url = f"{MINI_PROGRAM_CONFIG['jscode2session_url']}"
        params = {
            "appid": self.app_id,
            "secret": self.app_secret,
            "js_code": code,
            "grant_type": "authorization_code",
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "openid" in data:
                print(f"✅ 获取用户信息成功: openid={data['openid'][:10]}...")
                return {
                    "openid": data["openid"],
                    "session_key": data.get("session_key", ""),
                    "unionid": data.get("unionid", ""),
                }
            else:
                error_msg = data.get("errmsg", "未知错误")
                raise Exception(f"获取用户信息失败: {error_msg}")

        except Exception as e:
            print(f"❌ 获取用户信息失败: {e}")
            raise

    def generate_miniprogram_qrcode(
        self, session_id: str, page: str = "pages/bind/bind"
    ) -> Dict:
        """生成微信小程序码（真实API）"""
        # 测试模式：返回模拟二维码
        if TEST_MODE:
            print(f"[TEST_MODE] 返回模拟小程序码: session={session_id}")
            return self._generate_mock_qrcode(session_id, page)

        access_token = self._get_access_token()
        url = f"{MINI_PROGRAM_CONFIG['wxacode_url']}?access_token={access_token}"

        # 构建请求数据
        data = {
            "scene": f"session={session_id}",  # 最大32个字符
            "page": page,  # 必须是已发布的小程序页面
            "width": 280,  # 二维码宽度
            "auto_color": False,
            "line_color": {"r": "0", "g": "0", "b": "0"},
            "is_hyaline": False,  # 是否透明背景
        }

        try:
            response = requests.post(url, json=data, timeout=15)
            response.raise_for_status()

            # 检查返回的是否是图片
            content_type = response.headers.get("content-type", "")

            if "image" in content_type:
                # 成功获取图片
                image_data = response.content
                base64_data = base64.b64encode(image_data).decode("utf-8")

                return {
                    "success": True,
                    "base64": f"data:image/png;base64,{base64_data}",
#                    "raw_data": image_data,
#                    "session_id": session_id,
                }
            else:
                # 可能是错误信息
                error_data = response.json()
                error_msg = error_data.get("errmsg", "生成二维码失败")
                print(f"❌ 微信API返回错误: {error_msg}")

                # 返回模拟二维码作为降级方案
                return self._generate_mock_qrcode(session_id, page)

        except Exception as e:
            print(f"❌ 生成小程序码失败: {e}")
            # 降级到模拟二维码
            return self._generate_mock_qrcode(session_id, page)

    def _generate_mock_qrcode(self, session_id: str, page: str) -> Dict:
        """生成模拟的二维码（SVG格式，用于测试）"""
        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="280" height="280" viewBox="0 0 280 280">
  <rect width="280" height="280" fill="white"/>
  <rect x="10" y="10" width="260" height="260" fill="none" stroke="#333" stroke-width="2"/>
  <text x="140" y="120" text-anchor="middle" font-size="12" fill="#333">测试小程序码</text>
  <text x="140" y="145" text-anchor="middle" font-size="10" fill="#666">session={session_id[:8]}...</text>
  <text x="140" y="170" text-anchor="middle" font-size="10" fill="#999">请使用微信扫码</text>
  <rect x="60" y="190" width="160" height="40" rx="5" fill="#07C160"/>
  <text x="140" y="215" text-anchor="middle" font-size="12" fill="white">TEST MODE</text>
</svg>"""

        base64_data = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")

        return {
            "success": True,
            "base64": f"data:image/svg+xml;base64,{base64_data}",
            "session_id": session_id,
            "is_mock": True,
        }


# 全局实例
wechat_service = WechatService()
