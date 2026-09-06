"""
HNCU SDK 网络会话管理模块
封装 requests.Session，统一管理超时、代理策略、基础请求头与跨域 Cookie 处理
"""
from typing import Optional, Any, Dict
import requests
from .constants import DEFAULT_UNIQUE_CODE_HEADER, USER_AGENT_APP
from .exceptions import NetworkError

class HncuSession:
    """
    统一的网络会话管理器
    """
    def __init__(
        self,
        unique_code: str = DEFAULT_UNIQUE_CODE_HEADER,
        timeout: int = 15,
        verify_ssl: bool = True,
        trust_env: bool = False,
    ):
        self.unique_code = unique_code
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.trust_env = trust_env

        self.session = requests.Session()
        # 默认禁用操作系统环境代理（如 127.0.0.1:7890），确保校园内网 IP 58.47.143.* 与校内域名直连
        self.session.trust_env = self.trust_env

        # 初始化移动端基础请求头
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT_APP,
                "Unique-Code": self.unique_code,
                "AppType": "ydxy",
                "Connection": "keep-alive",
            }
        )

    def get_cookie(self, name: str, domain_pattern: Optional[str] = None) -> Optional[str]:
        """
        安全提取 Cookie，避免 requests.cookies.RequestsCookieJar 抛出 CookieConflictError
        
        :param name: Cookie 字段名 (如 JSESSIONID, CASTGC)
        :param domain_pattern: 可选匹配的域名关键词 (如 'rzpt.hncu.edu.cn' 或 '58.47.143.9')
        :return: Cookie 字符串值或 None
        """
        match_value = None
        for cookie in self.session.cookies:
            if cookie.name == name:
                match_value = cookie.value
                if domain_pattern and domain_pattern in getattr(cookie, "domain", ""):
                    return cookie.value
        return match_value

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        发送通用 HTTP 请求并自动应用默认配置
        """
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout
        if "verify" not in kwargs:
            kwargs["verify"] = self.verify_ssl

        try:
            return self.session.request(method, url, **kwargs)
        except requests.RequestException as e:
            raise NetworkError(f"HTTP 请求异常 [{method.upper()} {url}]: {e}") from e

    def get(self, url: str, **kwargs) -> requests.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        return self.request("POST", url, **kwargs)
