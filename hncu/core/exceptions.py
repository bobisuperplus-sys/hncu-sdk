"""
HNCU SDK 异常定义模块
"""

class HncuException(Exception):
    """HNCU SDK 基础异常类"""
    pass


class CryptoError(HncuException):
    """AES 加解密或数据格式解析异常"""
    pass


class LoginFailedError(HncuException):
    """登录失败异常（用户名密码错误、账号锁定等）"""
    def __init__(self, message: str, code: int = -1):
        super().__init__(f"登录失败 (错误代码: {code}): {message}")
        self.code = code
        self.message = message


class SsoConnectError(HncuException):
    """正方教务系统单点登录(SSO)连通失败异常"""
    pass


class SessionExpiredError(HncuException):
    """会话过期或未登录异常"""
    pass


class NetworkError(HncuException):
    """网络超时或服务不可达异常"""
    pass
