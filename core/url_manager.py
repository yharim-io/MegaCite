import urllib.parse
from core.config import SERVER_CONFIG
from dao.factory import create_connection
from dao.url_map_dao import MySQLUrlMapDAO

class URLManager:
    """
    负责路径映射和 URL 解析。
    """
    _instance = None
    _cid_map: dict[str, str] = {} # cid -> rel_path

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(URLManager, cls).__new__(cls)
        return cls._instance

    def safe_title(self, title: str) -> str:
        """生成 URL 安全标题 (Slug)。"""
        if not title:
            return "untitled"
        
        safe = title.strip()
        
        # 1. 恢复空格转横杠的功能 (Slugify)
        safe = safe.replace(" ", "-")
        
        # 2. 替换文件系统非法字符，但保留中文不进行 URL 编码
        # 这样生成的文件名在文件系统中是可见字符 (如中文)，http.server 也能正确找到
        for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
            safe = safe.replace(char, '-')
            
        # 3. 合并连续的横杠
        while "--" in safe:
            safe = safe.replace("--", "-")
            
        return safe

    def register_mapping(self, cid: str, username: str, category: str, title: str) -> str:
        """
        生成路径并确保写入数据库。
        返回相对路径前缀: username/category/safe-title
        """
        s_cat = self.safe_title(category)
        s_title = self.safe_title(title)
        
        rel_path = f"{username}/{s_cat}/{s_title}"
        self._cid_map[cid] = rel_path

        # 持久化到数据库，确保 external_url 可以被查到
        conn = create_connection()
        try:
            map_dao = MySQLUrlMapDAO(conn)
            # 存入绝对路径 /username/cat/title.html
            url_path = f"/{rel_path}.html"
            map_dao.upsert_mapping(cid, url_path)
        finally:
            conn.close()

        return rel_path

    def remove_mapping(self, cid: str) -> str | None:
        return self._cid_map.pop(cid, None)

    def get_cid_from_external_url(self, url: str) -> str | None:
        """解析外界传入的完整 URL，返回对应的 CID。"""
        try:
            parsed = urllib.parse.urlparse(url)
        except ValueError:
            return None
        
        # 验证端口: 必须与服务器配置一致
        if parsed.port != SERVER_CONFIG['port']:
            return None

        # 验证 Host: 宽松匹配，允许 localhost/127.0.0.1/配置Host
        allowed_hosts = {'localhost', '127.0.0.1', SERVER_CONFIG['host']}
        if parsed.hostname not in allowed_hosts:
            return None
            
        # 提取路径并解码 (防止数据库存的是中文，但 URL 是编码过的情况)
        url_path = urllib.parse.unquote(parsed.path)
        
        # 查库
        conn = create_connection()
        try:
            map_dao = MySQLUrlMapDAO(conn)
            cid = map_dao.get_cid_by_url(url_path)
            return cid
        finally:
            conn.close()

    def get_url_by_cid(self, cid: str) -> str | None:
        """通过 CID 查询完整的 URL 路径"""
        # 优先查内存
        if cid in self._cid_map:
            return "/" + self._cid_map[cid] + ".html"

        # 查库
        conn = create_connection()
        try:
            map_dao = MySQLUrlMapDAO(conn)
            path = map_dao.get_url_by_cid(cid)
            return path if path else None
        finally:
            conn.close()