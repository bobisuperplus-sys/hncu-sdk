"""
智慧校园综合服务门户与一卡通业务服务模块
"""
import json
import time
from typing import Optional, Dict, Any, List
import requests

from ..core.constants import BASE_URL_YWPT
from ..core.exceptions import NetworkError, SessionExpiredError, BusinessLogicError
from ..core.session import HncuSession
from ..auth.auth_service import AuthService
from .models import ECardInfo, PortalProfile


class PortalService:
    """智慧门户与一卡通业务服务"""

    # 核心卡片 ID 定义
    CARD_ID_USER_PROFILE = "dc564953ad2e414bb13aba9f645c7a7a"   # 个人信息卡片
    CARD_ID_ECARD_INFO = "2e8adf1b553541a895500f1c74ed1ccd"     # 一卡通基本数据卡片

    def __init__(self, hncu_session: HncuSession, auth_service: AuthService):
        self.hncu_session = hncu_session
        self.session = hncu_session.session
        self.auth = auth_service
        self._auth_token: Optional[str] = None

    def _extract_jti(self, jwt_token: str) -> Optional[str]:
        """从 JWT 令牌 Payload 中安全解析 jti 字段 (用作 customsid 会话标识)"""
        try:
            import base64
            parts = jwt_token.split(".")
            if len(parts) >= 2:
                payload_b64 = parts[1]
                payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
                payload_json = base64.urlsafe_b64decode(payload_b64.encode("utf-8")).decode("utf-8")
                data = json.loads(payload_json)
                return data.get("jti")
        except Exception:
            pass
        return None

    def set_token(self, token: str):
        """
        手动设置门户 Authorization 鉴权令牌 (JWT)

        :param token: JWT Bearer Token
        """
        self._auth_token = token.strip()
        # 同步写入 session cookie
        self.session.cookies.set("Authorization", self._auth_token, domain="ywpt.hncu.edu.cn")
        jti = self._extract_jti(self._auth_token)
        if jti:
            self.session.cookies.set("customsid", jti, domain="ywpt.hncu.edu.cn")

    def _ensure_auth(self):
        """确保已持有智慧门户有效凭证"""
        if self._auth_token:
            return

        # 尝试从 session cookie 获取
        auth_cookie = self.session.cookies.get("Authorization")
        if auth_cookie:
            self.set_token(auth_cookie)
            return

        # 尝试从 auth_service 的 web_auth_data 获取
        web_auth = getattr(self.auth, "web_auth_data", None)
        if isinstance(web_auth, dict) and web_auth.get("authorization"):
            self.set_token(web_auth["authorization"])
            return

        raise SessionExpiredError("尚未通过 Web 统一认证登录智慧门户，请先调用 client.login_web(...) 或 client.portal.set_token(...)")

    def _get_headers(self) -> Dict[str, str]:
        """构建门户微服务标准请求头"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/plain, */*",
            "Referer": f"{BASE_URL_YWPT}/",
        }
        if self._auth_token:
            jti = self._extract_jti(self._auth_token)
            cookie_parts = []
            if jti:
                cookie_parts.append(f"customsid={jti}")
            cookie_parts.append(f"Authorization={self._auth_token}")
            headers["Cookie"] = "; ".join(cookie_parts)
        return headers

    def query_card_raw(self, card_id: str) -> Any:
        """
        按 Card ID 查询门户卡片后端原始响应数据

        :param card_id: 门户卡片唯一标识 GUID
        :return: 解析后的卡片数据列表或字典
        """
        self._ensure_auth()
        ts = int(time.time())
        url = f"{BASE_URL_YWPT}/api/upp/contentDisplay/queryAppointCard/{card_id}?_t={ts}"

        try:
            resp = self.session.get(
                url,
                headers=self._get_headers(),
                timeout=self.hncu_session.timeout,
                verify=self.hncu_session.verify_ssl,
            )
            resp.raise_for_status()
            res_json = resp.json()
        except requests.RequestException as e:
            raise NetworkError(f"请求门户卡片接口网络异常: {e}") from e
        except json.JSONDecodeError as e:
            raise BusinessLogicError(f"门户接口返回了非预期格式: {resp.text[:200]}") from e

        meta = res_json.get("meta", {})
        if not meta.get("success", False) and meta.get("statusCode") != 200:
            msg = meta.get("message", "查询卡片数据失败")
            if meta.get("statusCode") == 401:
                raise SessionExpiredError(f"门户会话已失效 (401): {msg}")
            raise BusinessLogicError(msg)

        data_field = res_json.get("data", {}).get("data")
        if isinstance(data_field, str) and data_field.strip():
            try:
                return json.loads(data_field)
            except json.JSONDecodeError:
                return data_field
        return data_field

    def get_profile(self) -> PortalProfile:
        """
        获取智慧门户登记的完整个人综合档案信息
        包含学号、姓名、身份证号、学院、性别、高清证件照 Base64、最近登录 IP 及时间等

        :return: PortalProfile 数据模型对象
        """
        raw_list = self.query_card_raw(self.CARD_ID_USER_PROFILE)
        if isinstance(raw_list, list) and len(raw_list) > 0:
            return PortalProfile.from_dict(raw_list[0])
        elif isinstance(raw_list, dict):
            return PortalProfile.from_dict(raw_list)
        raise BusinessLogicError("未获取到有效的个人档案卡片数据")

    def get_ecard_info(self) -> ECardInfo:
        """
        获取一卡通基础信息
        包含卡实时余额（元）、挂失状态、冻结状态

        :return: ECardInfo 数据模型对象
        """
        raw_list = self.query_card_raw(self.CARD_ID_ECARD_INFO)
        if isinstance(raw_list, list) and len(raw_list) > 0:
            return ECardInfo.from_dict(raw_list[0])
        elif isinstance(raw_list, dict):
            return ECardInfo.from_dict(raw_list)
        raise BusinessLogicError("未获取到有效的一卡通卡片数据")

    def get_login_user_summary(self) -> Dict[str, Any]:
        """
        获取当前登录用户的核心概要（从 /tryLoginUserInfo 端点）
        包含学号、姓名、学院、角色类型、邮箱、性别代码等
        """
        self._ensure_auth()
        url = f"{BASE_URL_YWPT}/tryLoginUserInfo"

        try:
            resp = self.session.post(
                url,
                headers=self._get_headers(),
                timeout=self.hncu_session.timeout,
                verify=self.hncu_session.verify_ssl,
            )
            resp.raise_for_status()
            res_json = resp.json()
        except requests.RequestException as e:
            raise NetworkError(f"请求用户概要网络异常: {e}") from e
        except json.JSONDecodeError as e:
            raise BusinessLogicError(f"服务端响应非预期: {resp.text[:200]}") from e

        return res_json.get("data", {})
