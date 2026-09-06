"""
正方教务系统 - 个人学期课表查询服务
"""
from typing import Union, List, Dict, Any
import requests

from ..core.constants import BASE_URL_JWGLXT, USER_AGENT_WEB, Term
from ..core.exceptions import NetworkError
from ..core.models import CourseItem
from ..core.session import HncuSession
from ..auth.auth_service import AuthService


class ScheduleService:
    """个人课表查询服务"""

    def __init__(self, hncu_session: HncuSession, auth_service: AuthService):
        self.hncu_session = hncu_session
        self.session = hncu_session.session
        self.auth = auth_service

    def query(
        self,
        year: Union[int, str],
        term: Union[Term, str] = Term.FIRST,
        raw: bool = False,
    ) -> Union[List[CourseItem], Dict[str, Any]]:
        """
        查询学生个人学期课表

        :param year: 学年（如 2023 代表 2023-2024 学年）
        :param term: 学期（如 Term.FIRST: 第一学期/秋季）
        :param raw: 是否返回原始 JSON
        :return: CourseItem 列表或原始数据字典
        """
        self.auth.ensure_sso()
        url = f"{BASE_URL_JWGLXT}/jwglxt/kbcx/xskbcx_cxXsgrkb.html?gnmkdm=N2151"

        term_val = Term.normalize(term)
        post_data = {
            "xnm": str(year),
            "xqm": term_val,
            "kzlx": "ck",
            "xsdm": "",
        }

        headers = {
            "User-Agent": USER_AGENT_WEB,
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": BASE_URL_JWGLXT,
            "Referer": f"{BASE_URL_JWGLXT}/jwglxt/kbcx/xskbcx_cxXskbcxIndex.html?gnmkdm=N2151&layout=default",
        }

        try:
            resp = self.session.post(url, data=post_data, headers=headers, timeout=self.hncu_session.timeout)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            raise NetworkError(f"课表查询网络请求失败: {e}") from e

        if raw:
            return data

        kb_list = data.get("kbList", [])
        return [CourseItem.from_dict(item) for item in kb_list]
