"""
账号与安全服务
负责统一身份认证账号核验及密码修改
"""
import re
import time
from typing import Dict, Any
from urllib.parse import quote
import requests

from ..core.constants import BASE_URL_RZPT, BASE_URL_YDXY, USER_AGENT_WEB
from ..core.exceptions import HncuException, NetworkError
from ..core.session import HncuSession
from ..auth.auth_service import AuthService


class AccountService:
    """账号核验与密码服务"""

    def __init__(self, hncu_session: HncuSession, auth_service: AuthService):
        self.hncu_session = hncu_session
        self.session = hncu_session.session
        self.auth = auth_service

    def check_account(self, name: str, id_card: str) -> Dict[str, Any]:
        """
        通过姓名和身份证号检验统一身份认证账号
        """
        ts = int(time.time())
        url = f"{BASE_URL_RZPT}/lyuapServer/checkAccount?_t={ts}&username={quote(name)}&cardID={id_card}"
        try:
            resp = self.session.get(url, timeout=self.hncu_session.timeout, verify=self.hncu_session.verify_ssl)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            raise NetworkError(f"账号查询请求失败: {e}") from e

    def change_password(self, old_password: str, new_password: str) -> Dict[str, Any]:
        """
        修改统一身份认证/移动校园密码
        """
        self.auth.ensure_app_login()

        # 1. 获取 index 页面提取服务器内部 userId
        index_url = f"{BASE_URL_YDXY}/thirdpart_ydxy/ydxy/casUpdatePwd/index"
        try:
            resp_index = self.session.get(index_url, timeout=self.hncu_session.timeout)
            resp_index.raise_for_status()
        except requests.RequestException as e:
            raise NetworkError(f"请求修改密码页面失败: {e}") from e

        match = re.search(r'<input[^>]*id=["\']user["\'][^>]*value=["\']([^"\']*)["\']', resp_index.text)
        if not match:
            match = re.search(r'<input[^>]*value=["\']([^"\']*)["\'][^>]*id=["\']user["\']', resp_index.text)

        if not match:
            raise HncuException("无法从修改密码页面提取服务器内部 userId")

        server_user_id = match.group(1)

        # 2. 提交修改密码 POST
        update_url = f"{BASE_URL_YDXY}/thirdpart_ydxy/ydxy/casUpdatePwd/updatePwd"
        post_data = {
            "uid": "",
            "userId": server_user_id,
            "oldpassword": old_password,
            "newpassword": new_password,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": USER_AGENT_WEB,
            "X-Requested-With": "XMLHttpRequest",
            "Origin": BASE_URL_YDXY,
            "Referer": index_url,
        }

        try:
            resp_update = self.session.post(update_url, data=post_data, headers=headers, timeout=self.hncu_session.timeout)
            resp_update.raise_for_status()
            return resp_update.json()
        except requests.RequestException as e:
            raise NetworkError(f"提交修改密码失败: {e}") from e
