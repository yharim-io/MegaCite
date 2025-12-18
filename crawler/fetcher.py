import re
import trafilatura
from bs4 import BeautifulSoup
from curl_cffi import requests
from playwright.sync_api import sync_playwright
from client.cookie_store import load_cookies

def fetch_html(url: str, user_id: int) -> str:
    # 针对语雀 (Yuque) 的特殊处理：SPA 动态渲染 + 权限控制 + 专用清洗
    if "yuque.com" in url:
        return _fetch_dynamic(url, "yuque", user_id)
    
    # 其他默认静态抓取
    return _fetch_static(url)

def _fetch_dynamic(url: str, platform: str, user_id: int) -> str:
    print(f"[*] Using Playwright for {platform}...")
    try:
        # [修复] 传入 user_id 以加载对应用户的 Cookie
        cookies = load_cookies(user_id, platform) or []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            if cookies:
                context.add_cookies(cookies)
            
            page = context.new_page()
            page.goto(url)
            
            # 等待语雀阅读器核心容器
            try:
                page.wait_for_selector(".ne-viewer-body", timeout=15000)
                # 获取核心内容区域的 HTML，而非整个页面
                content = page.locator(".ne-viewer-body").inner_html()
            except Exception:
                # 兜底
                page.wait_for_load_state("networkidle")
                content = page.content()
                
            browser.close()
            
            if platform == "yuque":
                return _process_yuque_content(content)
                
            return _clean_content(content)
    except Exception as e:
        print(f"[-] Dynamic Fetch Error: {e}")
        return ""

def _process_yuque_content(html_source: str) -> str:
    """
    专门针对语雀的 <ne-*> 标签体系进行清洗和标准化转换。
    目标是生成下游 AI 转换器能理解的 '类 HTML' 或 'Markdown 混合体'。
    """
    print("[*] Pre-processing Yuque DOM structure...")
    soup = BeautifulSoup(html_source, "html.parser")

    # 1. 移除干扰元素 (SVG, 锚点、折叠按钮、填充符、操作按钮等)
    selectors_to_remove = [
        "svg", "style", "script", "noscript",
        ".ne-heading-ext", ".ne-heading-anchor", ".ne-heading-fold", 
        ".ne-viewer-b-filler", ".ne-ui-exit-max-view-btn", "button",
        "ne-uli-i", "ne-oli-i" 
    ]
    for selector in selectors_to_remove:
        for tag in soup.select(selector):
            tag.decompose()

    # 2. 标签映射表 (Yuque Tag -> Standard Tag)
    tag_map = {
        "ne-h1": "h1", "ne-h2": "h2", "ne-h3": "h3",
        "ne-h4": "h4", "ne-h5": "h5", "ne-h6": "h6",
        "ne-p": "p",
        "ne-quote": "blockquote"
    }

    for ne_tag, std_tag in tag_map.items():
        for tag in soup.find_all(ne_tag):
            tag.name = std_tag
            tag.attrs = {} # 移除所有属性，保持纯净

    # 3. 特殊处理：列表 (ne-uli / ne-oli)
    for uli in soup.find_all("ne-uli"):
        text = uli.get_text(strip=True)
        new_tag = soup.new_tag("p")
        new_tag.string = f"- {text}" 
        uli.replace_with(new_tag)

    for oli in soup.find_all("ne-oli"):
        text = oli.get_text(strip=True)
        text = re.sub(r'^\d+\.', '', text).strip()
        new_tag = soup.new_tag("p")
        new_tag.string = f"1. {text}"
        oli.replace_with(new_tag)

    # 4. 特殊处理：代码块 (ne-card[data-card-name="codeblock"])
    for card in soup.find_all("ne-card", attrs={"data-card-name": "codeblock"}):
        code_content = ""
        cm_content = card.select_one(".cm-content")
        if cm_content:
            lines = [line.get_text() for line in cm_content.select(".cm-line")]
            code_content = "\n".join(lines)
        else:
            code_content = card.get_text("\n")

        pre_tag = soup.new_tag("pre")
        code_tag = soup.new_tag("code")
        code_tag.string = code_content
        pre_tag.append(code_tag)
        card.replace_with(pre_tag)

    # 5. 特殊处理：分割线 (ne-card[data-card-name="hr"])
    for hr_card in soup.find_all("ne-card", attrs={"data-card-name": "hr"}):
        hr_tag = soup.new_tag("hr")
        hr_card.replace_with(hr_tag)

    # 6. 最后的清理：unwrap 掉无用的包装标签
    for wrapper in soup.select("ne-heading-content, ne-text"):
        wrapper.unwrap()

    print(f"[*] Yuque DOM normalized. Length: {len(str(soup))}")
    return str(soup)

def _fetch_static(url: str) -> str:
    try:
        resp = requests.get(
            url, 
            impersonate="chrome120", 
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
            timeout=10
        )
        if resp.status_code != 200:
            print(f"[-] HTTP Error: {resp.status_code}")
            return ""
        return _clean_content(resp.text)
    except Exception as e:
        print(f"[-] Static Fetch Error: {e}")
        return ""

def _clean_content(html_source: str) -> str:
    try:
        cleaned_content = trafilatura.extract(
            html_source,
            include_formatting=True, 
            include_links=True,      
            include_images=False,    
            include_tables=True,     
            include_comments=False,
            output_format='html'     
        )
        
        if not cleaned_content:
            print("[-] Warning: Trafilatura extracted nothing. Returning raw body slice.")
            if "body" in html_source:
                return html_source 
            return ""
            
        print(f"[*] Success. Length: {len(cleaned_content)} chars")
        return cleaned_content

    except Exception as e:
        print(f"[-] Cleaning Error: {e}")
        return ""