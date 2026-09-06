"""
移动校园 - 班级通讯录服务
"""
import json
import time
from typing import Optional, Union, List, Dict, Any
from urllib.parse import quote
import requests

from ..core.constants import BASE_URL_YDXY
from ..core.crypto import HncuCrypto
from ..core.exceptions import HncuException, NetworkError
from ..core.models import AddressBookMember
from ..core.session import HncuSession
from ..auth.auth_service import AuthService


class AddressBookService:
    """班级通讯录查询服务"""

    def __init__(self, hncu_session: HncuSession, crypto: HncuCrypto, auth_service: AuthService):
        self.hncu_session = hncu_session
        self.session = hncu_session.session
        self.crypto = crypto
        self.auth = auth_service

    def get_members(
        self, class_id: Optional[str] = None, raw: bool = False
    ) -> Union[List[AddressBookMember], List[Dict[str, Any]]]:
        """
        获取班级通讯录

        :param class_id: 班级ID (留空默认使用当前用户所属班级)
        :param raw: 是否返回原始数据字典列表
        """
        self.auth.ensure_app_login()
        target_class_id = class_id or (self.auth.profile.class_id if self.auth.profile else "")
        if not target_class_id:
            raise HncuException("无法获取班级 ID，请显式提供 class_id 参数")

        # 对 payload 进行 AES 加密并 URL Encode
        payload = json.dumps({"bjid": target_class_id})
        encrypted_param = quote(self.crypto.encrypt(payload))

        url = f"{BASE_URL_YDXY}/mobileapi_ydxy/api/addressbook/getClassAddressbook?data={encrypted_param}"

        res_json = None
        for attempt in range(2):
            try:
                resp = self.session.get(url, timeout=self.hncu_session.timeout)
                resp.raise_for_status()
                res_json = resp.json()
                break
            except requests.RequestException as e:
                if attempt == 1:
                    raise NetworkError(f"通讯录查询网络异常: {e}") from e
                time.sleep(1)

        if str(res_json.get("code")) != "0":
            raise HncuException(f"获取班级通讯录失败: {res_json.get('msg', '未知错误')}")

        # 解密返回的数组成员字符串
        decrypted_text = self.crypto.decrypt(res_json.get("data", ""))
        members_data = self.crypto.extract_and_parse_json(decrypted_text, expect_array=True)

        if raw:
            return members_data

        return [AddressBookMember.from_dict(m) for m in members_data]
