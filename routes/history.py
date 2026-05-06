from fastapi import Depends
from fastapi.routing import APIRouter
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from database import get_db
from models import AnalysisResult

router = APIRouter()

@router.get("")
async def history_page(user_id: str, db: Session = Depends(get_db)):
    """返回历史记录页面（HTML），接收user_id参数"""
    # 先查询该用户的记录总数（用于页面展示）
    total = db.query(AnalysisResult).filter(AnalysisResult.user_id == user_id).count()
    # 构造HTML页面（内嵌JS调用/api/query-result接口）
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI网页分析历史记录</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: "Microsoft Yahei", sans-serif; }}
        body {{ padding: 20px; max-width: 1200px; margin: 0 auto; background: #f5f5f5; }}
        .header {{ margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #eee; }}
        .header h1 {{ font-size: 24px; color: #333; }}
        .header .tip {{ font-size: 14px; color: #666; margin-top: 5px; }}
        .empty {{ text-align: center; padding: 50px; color: #999; font-size: 16px; }}
        .result-card {{ background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
        .result-card {{ position: relative; }}
        .result-card .fav {{ position: absolute; top: 20px; right: 20px; cursor: pointer; font-size: 18px; }}
        .result-card .title {{ font-size: 18px; font-weight: 600; color: #333; margin-bottom: 10px; }}
        .result-card .summary {{ font-size: 14px; line-height: 1.6; color: #666; margin-bottom: 10px; }}
        .result-card .tags {{ margin-bottom: 10px; }}
        .result-card .tag {{ display: inline-block; padding: 4px 10px; background: #e8f4f8; color: #4285f4; border-radius: 4px; font-size: 12px; margin-right: 5px; }}
        .result-card .meta {{ font-size: 12px; color: #999; display: flex; justify-content: space-between; }}
        .result-card .meta a {{ color: #4285f4; text-decoration: none; }}
        .status {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; }}
        .status-pending {{ background: #fff3cd; color: #856404; }}
        .status-finished {{ background: #d4edda; color: #155724; }}
        .status-failed {{ background: #f8d7da; color: #721c24; }}
        .refresh-btn {{ padding: 8px 16px; background: #4285f4; color: #fff; border: none; border-radius: 4px; cursor: pointer; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>AI网页分析历史记录</h1>
        <div class="tip">共 {total} 条记录 | 刷新可查看最新状态</div>
    </div>
    <button class="refresh-btn" onclick="loadResults()">刷新记录</button>
    <button class="refresh-btn" id="showFavoritesBtn" onclick="toggleFavorites()">显示收藏</button>
    <div id="results-container"></div>

    <script>
        // 获取URL中的user_id参数
        const user_id = new URLSearchParams(window.location.search).get('user_id');

        // 页面加载时自动加载记录
        window.onload = loadResults;

        // 加载历史记录（调用/api/query-result接口）
        let showingFavorites = false;

        function toggleFavorites() {{
            showingFavorites = !showingFavorites;
            document.getElementById('showFavoritesBtn').textContent = showingFavorites ? '显示全部' : '显示收藏';
            loadResults();
        }}

        async function loadResults() {{
            const container = document.getElementById('results-container');
            container.innerHTML = '<div style="text-align:center; padding:20px;">加载中...</div>';

            try {{
                let url = `/api/query-result?user_id=${{user_id}}`;
                if (showingFavorites) {{
                    url += '&favorite=true';
                }}
                const response = await fetch(url);
                const data = await response.json();

                if (data.code === 200 && data.results.length > 0) {{
                    // 渲染记录列表
                    let html = '';
                    data.results.forEach(item => {{
                        // 收藏图标
                        const star = item.favorite ? '⭐' : '☆';
                        // 处理标签
                        const tags = item.categories === '处理中...' ? ['处理中...'] : item.categories;
                        let tagHtml = tags.map(tag => `<span class="tag">${{tag}}</span>`).join('');

                        // 处理状态
                        let statusClass = '';
                        let statusText = '';
                        switch(item.status) {{
                            case 'pending': statusClass = 'status-pending'; statusText = '处理中'; break;
                            case 'finished': statusClass = 'status-finished'; statusText = '已完成'; break;
                            case 'failed': statusClass = 'status-failed'; statusText = '失败'; break;
                        }}

                        html += `
<div class="result-card">
    <div class="fav" onclick="toggleFavorite('${{item.task_id}}', this)">${{star}}</div>
    <div class="title">${{item.title || '无标题'}}</div>
    <div class="summary">${{item.summary}}</div>
    <div class="tags">${{tagHtml}}</div>
    <div class="meta">
        <span><span class="status ${{statusClass}}">${{statusText}}</span> | ${{item.create_time}}</span>
        <a href="${{item.url}}" target="_blank">查看原文</a>
    </div>
</div>
                        `;
                    }});
                    container.innerHTML = html;
                }} else {{
                    container.innerHTML = '<div class="empty">暂无历史记录，快去Chrome插件提取网页内容吧～</div>';
                }}
            }} catch (e) {{
                container.innerHTML = `<div class="empty">加载失败：${{e.message}}</div>`;
            }}
        }}

        // 切换单条收藏状态
        async function toggleFavorite(task_id, elem) {{
            try {{
                const newFav = elem.textContent === '☆';
                await fetch('/api/query-result/favorite', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    // 双重大括号避免Python f-string提前解析
                    body: JSON.stringify({{task_id, favorite: newFav}})
                }});
                elem.textContent = newFav ? '⭐' : '☆';
                // 如果当前正在显示收藏视图，刷新列表以显示/隐藏该记录
                if (showingFavorites) {{
                    loadResults();
                }}
            }} catch (e) {{
                console.error('收藏操作失败', e);
            }}
        }}
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content, status_code=200)