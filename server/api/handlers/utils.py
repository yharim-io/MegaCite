import re
import http.cookies

def get_token(handler):
    token = handler.headers.get('Authorization')
    if not token and "Cookie" in handler.headers:
        try:
            cookie = http.cookies.SimpleCookie(handler.headers["Cookie"])
            if "mc_token" in cookie:
                token = cookie["mc_token"].value
        except: pass
    return token

def highlight_snippet(text, keyword, context_len=100):
    """
    在一段文字中间显示匹配关键词，前后保留 context_len 长度。
    关键词加粗加蓝。
    """
    if text is None:
        text = ""

    if not keyword:
        # 如果没有搜索内容就按照现在原来的显示方法显示 (前200字符)
        return text[:200] + "..." if len(text) > 200 else text

    # 模糊匹配 (忽略大小写)
    match = re.search(re.escape(keyword), text, re.IGNORECASE)
    if not match:
        # 没匹配到（可能是匹配了标题），默认显示开头
        return text[:200] + "..." if len(text) > 200 else text

    start, end = match.span()
    
    # 计算截取范围，确保匹配项居中
    clip_start = max(0, start - context_len)
    clip_end = min(len(text), end + context_len)
    
    snippet = text[clip_start:clip_end]
    
    # 加上省略号
    prefix = "..." if clip_start > 0 else ""
    suffix = "..." if clip_end < len(text) else ""
    
    # 在截取后的片段中进行高亮替换
    # 使用 style="color: #1a0dab; font-weight: bold;"
    highlighted = re.sub(
        f"({re.escape(keyword)})", 
        r'<span style="color: #1a0dab; font-weight: bold;">\1</span>', 
        snippet, 
        flags=re.IGNORECASE
    )
    
    return f"{prefix}{highlighted}{suffix}"

def highlight_title(title, keyword):
    if title is None:
        return ""
    if not keyword:
        return title
    return re.sub(
        f"({re.escape(keyword)})", 
        r'<span style="color: #1a0dab; font-weight: bold;">\1</span>', 
        title, 
        flags=re.IGNORECASE
    )