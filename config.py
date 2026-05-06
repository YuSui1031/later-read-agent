import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ========== 配置项 ==========
API_KEY = os.getenv('DEEPSEEK_API_KEY', '')

# 微信小程序配置
MINI_PROGRAM_CONFIG = {
    "APPID": os.getenv('WECHAT_APPID', ''),
    "APPSECRET": os.getenv('WECHAT_APPSECRET', ''),
    "access_token_url": "https://api.weixin.qq.com/cgi-bin/token",
    "jscode2session_url": "https://api.weixin.qq.com/sns/jscode2session",
    "wxacode_url": "https://api.weixin.qq.com/wxa/getwxacodeunlimit",
}

# 数据库配置
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./ai_web_analyzer.db')

# 其他配置
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# 测试模式配置
TEST_MODE = os.getenv('TEST_MODE', 'False').lower() == 'true'
TEST_USER = {
    "user_id": "test-user-001",
    "openid": "test-openid-001",
}