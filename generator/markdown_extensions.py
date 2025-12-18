from xml.etree import ElementTree
from markdown.inlinepatterns import InlineProcessor, AutolinkInlineProcessor
from markdown.extensions import Extension
from core.config import SERVER_CONFIG

# 匹配 [text](url)
LINK_RE = r'\[([^\]]+)\]\(([^)]+)\)'
# 匹配 <http://...>
AUTOLINK_RE = r'<((?:http|https):[^>]+)>'
# 内部 CID 协议头
CID_SCHEME = "http://megacite.cid/"

class CiteLinkProcessor(InlineProcessor):
    """
    处理 [text](url) 格式的链接。
    如果是外部链接，尝试转换为 [text](http://megacite.cid/<cid>) 并触发数据库更新。
    """
    def __init__(self, pattern, md, url_mgr, db_callback):
        super().__init__(pattern, md)
        self.url_mgr = url_mgr
        self.db_callback = db_callback

    def handleMatch(self, m, data):
        text = m.group(1)
        href = m.group(2)
        el = ElementTree.Element("a")
        el.text = text
        target_cid = None

        # 1. 识别内部引用
        if href.startswith(CID_SCHEME):
            target_cid = href[len(CID_SCHEME):]
        # 2. 识别外部链接并尝试转换
        else:
            target_cid = self.url_mgr.get_cid_from_external_url(href)
            if target_cid:
                old_str = m.group(0)
                new_str = f"[{text}]({CID_SCHEME}{target_cid})"
                self.db_callback(old_str, new_str, target_cid)

        # 渲染逻辑
        if target_cid:
            if href.startswith(CID_SCHEME):
                self.db_callback(None, None, target_cid)

            real_path = self.url_mgr.get_url_by_cid(target_cid)
            if real_path:
                el.set("href", real_path)
                # 如果显示文本看起来像个 URL，则将其替换为真实的完整 URL 以便展示
                if el.text.strip().startswith(("http://", "https://")):
                     el.text = f"http://{SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}{real_path}"
            else:
                el.set("href", "#unknown-cid")
            return el, m.start(0), m.end(0)

        el.set("href", href)
        return el, m.start(0), m.end(0)

class CiteAutoLinkProcessor(AutolinkInlineProcessor):
    """
    处理 <http://...> 格式的自动链接。
    如果是外部链接，尝试转换为 <http://megacite.cid/<cid>> 并触发数据库更新。
    """
    def __init__(self, pattern, md, url_mgr, db_callback):
        super().__init__(pattern, md)
        self.url_mgr = url_mgr
        self.db_callback = db_callback

    def handleMatch(self, m, data):
        href = m.group(1)
        el = ElementTree.Element("a")
        target_cid = None

        # 1. 识别内部引用
        if href.startswith(CID_SCHEME):
            target_cid = href[len(CID_SCHEME):]
        # 2. 识别外部链接并尝试转换
        else:
            target_cid = self.url_mgr.get_cid_from_external_url(href)
            if target_cid:
                old_str = m.group(0)
                new_str = f"<{CID_SCHEME}{target_cid}>"
                self.db_callback(old_str, new_str, target_cid)

        if target_cid:
            if href.startswith(CID_SCHEME):
                self.db_callback(None, None, target_cid)

            real_path = self.url_mgr.get_url_by_cid(target_cid)
            if real_path:
                el.set("href", real_path)
                # 始终显示完整的真实 URL
                el.text = f"http://{SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}{real_path}"
            else:
                el.set("href", "#unknown-cid")
                el.text = href
            return el, m.start(0), m.end(0)
        
        return super().handleMatch(m, data)

class CiteReferenceExtension(Extension):
    def __init__(self, **kwargs):
        self.url_mgr = kwargs.pop('url_mgr')
        self.db_callback = kwargs.pop('db_callback')
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        # 优先级设为 165，介于代码块(175)和标准链接(160)之间
        md.inlinePatterns.register(
            CiteLinkProcessor(LINK_RE, md, self.url_mgr, self.db_callback),
            'cite_link', 165
        )
        md.inlinePatterns.register(
            CiteAutoLinkProcessor(AUTOLINK_RE, md, self.url_mgr, self.db_callback),
            'cite_autolink', 165
        )