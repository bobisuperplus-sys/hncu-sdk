"""
正方教务系统 - 考试成绩查询服务
"""
import time
from typing import Optional, Union, List, Dict, Any
import requests

from ..core.constants import BASE_URL_JWGLXT, USER_AGENT_WEB, Term
from ..core.exceptions import NetworkError
from ..core.models import GradeItem
from ..core.session import HncuSession
from ..auth.auth_service import AuthService


class GradesService:
    """学生历史成绩查询服务"""

    def __init__(self, hncu_session: HncuSession, auth_service: AuthService):
        self.hncu_session = hncu_session
        self.session = hncu_session.session
        self.auth = auth_service

    def query(
        self,
        year: Optional[Union[int, str]] = None,
        term: Union[Term, str] = Term.ALL,
        raw: bool = False,
    ) -> Union[List[GradeItem], Dict[str, Any]]:
        """
        查询期末考试成绩

        :param year: 学年（如 2023 代表 2023-2024 学年，留空查全部）
        :param term: 学期（Term.FIRST: "3", Term.SECOND: "12", Term.ALL: 全部）
        :param raw: 是否返回原始 JSON 数据字典 (默认 False)
        :return: GradeItem 列表或原始响应字典
        """
        self.auth.ensure_sso()
        menu_init_url = f"{BASE_URL_JWGLXT}/jwglxt/cjcx/cjcx_cxDgXscj.html?gnmkdm=N305005&layout=default"
        try:
            self.session.get(menu_init_url, headers={"User-Agent": USER_AGENT_WEB}, timeout=self.hncu_session.timeout)
        except requests.RequestException:
            pass

        url = f"{BASE_URL_JWGLXT}/jwglxt/cjcx/cjcx_cxDgXscj.html?doType=query&gnmkdm=N305005"

        term_val = term.value if isinstance(term, Term) else str(term)
        user_id = self.auth.profile.user_id if self.auth.profile else ""
        post_data = {
            "xh_id": user_id,
            "xnm": str(year) if year else "",
            "xqm": term_val if term_val else "",
            "_search": "false",
            "nd": str(int(time.time() * 1000)),
            "queryModel.showCount": "100",
            "queryModel.currentPage": "1",
            "queryModel.sortName": "xnmmc",
            "queryModel.sortOrder": "desc",
        }

        headers = {
            "User-Agent": USER_AGENT_WEB,
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": BASE_URL_JWGLXT,
            "Referer": menu_init_url,
        }

        try:
            resp = self.session.post(url, data=post_data, headers=headers, timeout=self.hncu_session.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise NetworkError(f"成绩查询网络请求失败: {e}") from e

        try:
            data = resp.json()
        except (ValueError, Exception):
            data = {"items": []}

        if raw:
            return data

        items = data.get("items", [])
        return [GradeItem.from_dict(item) for item in items]
