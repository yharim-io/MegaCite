from abc import ABC, abstractmethod

class PlatformVerifier(ABC):
    @abstractmethod
    def login(self) -> bool:
        """交互式登录并返回 Cookies (仅用于本地客户端，不保存到服务端存储)"""
        pass

    @abstractmethod
    def check_ownership(self, url: str, user_id: int) -> bool:
        """
        非交互式验证 URL 所有权
        user_id: 当前操作的用户ID，用于加载对应的 Cookie
        """
        pass