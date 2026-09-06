"""
移动校园 - 校历与学期信息服务
"""
import json
import time
from typing import Dict, Any
import requests

from ..core.constants import BASE_URL_YDXY
from ..core.crypto import HncuCrypto
from ..core.exceptions import NetworkError
from ..core.session import HncuSession
from ..auth.auth_service import AuthService


class CalendarService:
    """校历与学期日程服务"""

    def __init__(self, hncu_session: HncuSession, crypto: HncuCrypto, auth_service: AuthService):
        self.hncu_session = hncu_session
        self.session = hncu_session.session
        self.crypto = crypto
        self.auth = auth_service

    def get_term_info(self) -> Dict[str, Any]:
        """
        获取当前学期校历与起止时间信息
        """
        self.auth.ensure_app_login()
        url = f"{BASE_URL_YDXY}/mobileapi_ydxy/api/schedule/termInfo"

        # 每次调用前刷新带有时戳的 access-token
        access_token_dict = {
            "clientVersion": "3.2.0",
            "sessionKey": self.auth.profile.session_key,
            "userId": self.auth.profile.user_id,
            "userType": "1",
            "xxdm": "HNCU",
            "currentTime": str(int(time.time() * 1000)),
        }
        self.session.headers["Access-Token"] = self.crypto.encrypt(
            json.dumps(access_token_dict, separators=(",", ":"))
        )

        try:
            resp = self.session.get(url, timeout=self.hncu_session.timeout)
            resp.raise_for_status()
            res_json = resp.json()
        except requests.RequestException as e:
            raise NetworkError(f"校历信息查询网络异常: {e}") from e

        decrypted_text = self.crypto.decrypt(res_json.get("data", ""))
        return self.crypto.extract_and_parse_json(decrypted_text, expect_array=False)
