"""
正方教务系统 - 期末考试日程与考场安排查询服务
"""
import time
import json
from typing import Union, List, Dict, Any
import requests

from ..core.constants import BASE_URL_JWGLXT, USER_AGENT_WEB, Term
from ..core.exceptions import NetworkError
from ..core.models import ExamItem
from ..core.session import HncuSession
from ..auth.auth_service import AuthService


class ExamsService:
    """期末考试安排查询服务"""

    def __init__(self, hncu_session: HncuSession, auth_service: AuthService):
        self.hncu_session = hncu_session
        self.session = hncu_session.session
        self.auth = auth_service

    def query(
        self,
        year: Union[int, str],
        term: Union[Term, str] = Term.FIRST,
        raw: bool = False,
    ) -> Union[List[ExamItem], Dict[str, Any]]:
        """
        查询期末考试安排

        :param year: 学年（如 2023）
        :param term: 学期（Term.FIRST: 3, Term.SECOND: 12）
        :param raw: 是否返回原始字典
        :return: ExamItem 列表或原始字典
        """
        self.auth.ensure_sso()
        menu_init_url = f"{BASE_URL_JWGLXT}/jwglxt/kwgl/kscx_cxXsksxxIndex.html?gnmkdm=N358105&layout=default"
        try:
            self.session.get(menu_init_url, headers={"User-Agent": USER_AGENT_WEB}, timeout=self.hncu_session.timeout)
        except requests.RequestException:
            pass

        url = f"{BASE_URL_JWGLXT}/jwglxt/kwgl/kscx_cxXsksxxIndex.html?doType=query&gnmkdm=N358105"

        term_val = term.value if isinstance(term, Term) else str(term)
        post_data = {
            "xnm": str(year),
            "xqm": term_val,
            "ksmcdmb_id": "",
            "kch": "",
            "kc": "",
            "ksrq": "",
            "kkbm_id": "",
            "_search": "false",
            "nd": str(int(time.time())),
            "queryModel.showCount": "50",
            "queryModel.currentPage": "1",
            "queryModel.sortName": "+",
            "queryModel.sortOrder": "asc",
            "time": "0",
        }

        headers = {
            "User-Agent": USER_AGENT_WEB,
            "Referer": menu_init_url,
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
        }

        try:
            resp = self.session.post(url, data=post_data, headers=headers, timeout=self.hncu_session.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise NetworkError(f"考试安排查询网络请求失败: {e}") from e

        try:
            data = resp.json()
        except (ValueError, json.JSONDecodeError):
            # 教务系统在未排考或无考试记录时可能返回提示 HTML 页面
            data = {"items": []}

        if raw:
            return data

        items = data.get("items", [])
        return [ExamItem.from_dict(item) for item in items]
