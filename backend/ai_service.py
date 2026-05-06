import json
import re
from config import API_KEY


def parse_ai_response(ai_response: str) -> dict:
    """
    清理AI返回的JSON字符串并解析
    """
    try:
        cleaned = re.sub(r"```json\s*|\s*```", "", ai_response)

        # 解析JSON
        result = json.loads(cleaned.strip())
        return result

    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}")
        print(f"清理后的内容: {cleaned}")
        # 备用方案：返回默认值
        return {"summary": ai_response[:200], "categories": ["未分类"]}


def analyze_with_ai(content: str) -> dict:
    """调用AI做摘要和分类"""

    # 检查 API_KEY
    from config import API_KEY

    print(f"[AI服务] API_KEY 已配置: {'是' if API_KEY else '否'}")

    prompt = f"""
    请分析以下网页内容，完成两个任务：
    1. 生成简洁的摘要（300字以内）；
    2. 给出3-5个分类标签（比如：科研、资讯、技术、娱乐、教育等）。
    内容：{content[:5000]}
    输出格式要求：JSON字符串，包含summary和categories两个字段，categories是数组。
    """

    if not API_KEY:
        print("[AI服务] 警告：API_KEY 为空，使用模拟摘要")
        return {
            "summary": f"【模拟摘要】{content[:200]}...",
            "categories": ["科研", "网页内容", "未分类"],
        }

    try:
        import openai

        print(f"[AI服务] openai 版本: {openai.__version__}")

        from openai import OpenAI

        # 新版本使用 OpenAI 类
        client = OpenAI(api_key=API_KEY)
        # 设置 base_url
        client.base_url = "https://api.deepseek.com/v1"

        print("[AI服务] 开始调用 DeepSeek API...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000,
        )
        print("[AI服务] DeepSeek API 调用成功")
        # 解析AI返回结果
        ai_response = response.choices[0].message.content
        return parse_ai_response(ai_response)

    except Exception as e:
        # 备用方案：如果没有AI Key，返回模拟结果
        print(f"[AI服务] AI调用失败：{e}")
        return {
            "summary": f"【模拟摘要】{content[:200]}...",
            "categories": ["科研", "网页内容", "未分类"],
        }

    try:
        import openai

        # 使用旧版 API 方式（兼容性问题）
        openai.api_key = API_KEY
        openai.base_url = "https://api.deepseek.com"

        print("[AI服务] 开始调用 DeepSeek API...")
        response = openai.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000,
        )
        print("[AI服务] DeepSeek API 调用成功")
        # 解析AI返回结果
        ai_response = response.choices[0].message.content
        return parse_ai_response(ai_response)

    except Exception as e:
        # 备用方案：如果没有AI Key，返回模拟结果
        print(f"[AI服务] AI调用失败：{e}")
        return {
            "summary": f"【模拟摘要】{content[:200]}...",
            "categories": ["科研", "网页内容", "未分类"],
        }
