"""
移动校园 - 用户个人详细资料服务
"""
import json
from typing import Optional, Dict, Any
from urllib.parse import quote
import requests

from ..core.constants import BASE_URL_YDXY
from ..core.crypto import HncuCrypto
from ..core.exceptions import NetworkError
from ..core.session import HncuSession
from ..auth.auth_service import AuthService


class UserInfoService:
    """移动校园用户详细资料服务"""

    def __init__(self, hncu_session: HncuSession, crypto: HncuCrypto, auth_service: AuthService):
        self.hncu_session = hncu_session
        self.session = hncu_session.session
        self.crypto = crypto
        self.auth = auth_service

    def get_info(self, gh: Optional[str] = None) -> Dict[str, Any]:
        """
        获取教工或学生个人详细档案信息

        :param gh: 工号/学号 (留空默认当前用户)
        """
        self.auth.ensure_app_login()
        target_gh = gh or (self.auth.profile.user_id if self.auth.profile else "")

        payload = json.dumps({"gh": target_gh})
        encrypted_param = quote(self.crypto.encrypt(payload))

        url = f"{BASE_URL_YDXY}/mobileapi_ydxy/api/addressbook/userInfo?data={encrypted_param}"

        try:
            resp = self.session.get(url, timeout=self.hncu_session.timeout)
            resp.raise_for_status()
            res_json = resp.json()
        except requests.RequestException as e:
            raise NetworkError(f"个人信息查询网络异常: {e}") from e

        decrypted_text = self.crypto.decrypt(res_json.get("data", ""))
        return self.crypto.extract_and_parse_json(decrypted_text, expect_array=False)
