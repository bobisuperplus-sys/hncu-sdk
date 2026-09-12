"""
正方教务系统 - 空闲教室/自习室查询服务
"""
import time
from typing import Optional, Union, List, Dict, Any
import requests

from ..core.constants import BASE_URL_JWGLXT, USER_AGENT_WEB, Term
from ..core.exceptions import NetworkError
from ..core.models import EmptyClassroomItem
from ..core.session import HncuSession
from ..auth.auth_service import AuthService


class ClassroomService:
    """空闲教室查询服务"""

    def __init__(self, hncu_session: HncuSession, auth_service: AuthService):
        self.hncu_session = hncu_session
        self.session = hncu_session.session
        self.auth = auth_service

    def query(
        self,
        year: Union[int, str],
        term: Union[Term, str] = Term.FIRST,
        week: int = 1,
        day_of_week: int = 1,
        section_start: int = 1,
        section_end: int = 2,
        campus_id: str = "AADC7199FC2EB679E055C18C75144BC0",
        building: str = "",
        room_name: str = "",
        room_type: str = "001",
        page: int = 1,
        page_size: int = 15,
        raw: bool = False,
    ) -> Union[List[EmptyClassroomItem], Dict[str, Any]]:
        """
        查询指定学年、学期、周次、星期与节次的空闲教室列表

        :param year: 学年（如 2026）
        :param term: 学期（Term.FIRST: 3, Term.SECOND: 12）
        :param week: 周次（1-25 周）
        :param day_of_week: 星期几（1: 周一 ... 7: 周日）
        :param section_start: 起始节次（1-12）
        :param section_end: 结束节次（1-12）
        :param campus_id: 校区ID（默认新校区 AADC7199FC2EB679E055C18C75144BC0）
        :param building: 教学楼/楼号 (如 "003")
        :param room_name: 教室名称模糊检索 (如 "1教")
        :param room_type: 教室类型 (默认 "001" 普通/多媒体教室)
        :param page: 页码
        :param page_size: 每页条数
        :param raw: 是否返回原始 JSON
        :return: EmptyClassroomItem 列表或原始响应字典
        """
        self.auth.ensure_sso()

        # 1. 预热访问功能页面，激活该模块的会话权限上下文
        menu_init_url = f"{BASE_URL_JWGLXT}/jwglxt/cdjy/cdjy_cxKxcdlb.html?gnmkdm=N2155&layout=default"
        try:
            self.session.get(menu_init_url, headers={"User-Agent": USER_AGENT_WEB}, timeout=self.hncu_session.timeout)
        except requests.RequestException:
            pass

        # 2. 计算周次与节次二进制位掩码 (Bitmask)
        zcd_val = 1 << (max(1, week) - 1)
        jcd_val = 0
        for s in range(max(1, section_start), max(section_start, section_end) + 1):
            jcd_val |= (1 << (s - 1))

        term_val = Term.normalize(term)
        post_data = {
            "xqh_id": campus_id,
            "xnm": str(year),
            "xqm": term_val,
            "cdlb_id": room_type,
            "cdejlb_id": "",
            "qszws": "",
            "jszws": "",
            "cdmc": room_name,
            "lh": building,
            "jyfs": "0",
            "cdjylx": "",
            "sfbhkc": "",
            "zcd": str(zcd_val),
            "xqj": str(day_of_week),
            "jcd": str(jcd_val),
            "_search": "false",
            "nd": str(int(time.time() * 1000)),
            "queryModel.showCount": str(page_size),
            "queryModel.currentPage": str(page),
            "queryModel.sortName": "cdbh+",
            "queryModel.sortOrder": "asc",
            "time": "0",
        }

        query_url = f"{BASE_URL_JWGLXT}/jwglxt/cdjy/cdjy_cxKxcdlb.html?doType=query&gnmkdm=N2155"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "User-Agent": USER_AGENT_WEB,
            "Referer": menu_init_url,
            "X-Requested-With": "XMLHttpRequest",
        }

        try:
            resp = self.session.post(query_url, data=post_data, headers=headers, timeout=self.hncu_session.timeout)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            raise NetworkError(f"空闲教室查询网络异常: {e}") from e

        if raw:
            return data

        items = data.get("items", [])
        return [EmptyClassroomItem.from_dict(it) for it in items]

    def query_study_rooms(
        self,
        period: str = "all_day",
        building: str = "",
        min_seats: int = 0,
        room_name: str = "",
        week: Optional[int] = None,
        day_of_week: Optional[int] = None,
        year: Optional[Union[int, str]] = None,
        term: Optional[Union[Term, str]] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> List[EmptyClassroomItem]:
        """
        【深度自习室 / 考研教室检索】
        支持按常用自习时段预设、教学楼与最小座位数智能检索空闲自习教室。

        :param period: 目标自习时段预设:
                       - "all_day": 全天连续空闲 (1-10 节全空)
                       - "morning": 上午空闲 (1-4 节)
                       - "afternoon": 下午空闲 (5-8 节)
                       - "evening": 晚自习空闲 (9-10 节)
                       - "daytime": 白天连续空闲 (1-8 节)
        :param building: 教学楼名称或编号 (如 "1教", "2教", "3教", 或留空查全校)
        :param min_seats: 最低空闲座位数要求 (如过滤 60 座以上大自习室)
        :param room_name: 教室名称模糊搜索 (如 "301", "阶梯")
        :param week: 教学周次 (1-25 周，默认自动推算为第 1 周)
        :param day_of_week: 星期几 (1: 周一 ... 7: 周日，默认取系统今日星期)
        :param year: 学年 (默认 2026)
        :param term: 学期 (默认第 1 学期)
        :param page: 分页页码
        :param page_size: 每页数量 (默认 50)
        :return: EmptyClassroomItem 空闲自习教室列表
        """
        import datetime

        # 1. 映射自习时段节次
        period_map = {
            "all_day": (1, 10),
            "morning": (1, 4),
            "afternoon": (5, 8),
            "evening": (9, 10),
            "daytime": (1, 8),
        }
        sec_start, sec_end = period_map.get(period.lower().strip(), (1, 10))

        # 2. 智能推算当前星期几与周次
        today = datetime.date.today()
        target_dow = day_of_week if day_of_week is not None else today.isoweekday()
        target_week = week if week is not None else 1
        target_year = year if year is not None else 2026
        target_term = term if term is not None else Term.FIRST

        # 3. 基础教学楼名称映射兼容
        target_building = building
        if building in ("1", "1教", "一教"):
            target_building = "1"
        elif building in ("2", "2教", "二教"):
            target_building = "2"
        elif building in ("3", "3教", "三教"):
            target_building = "3"

        # 4. 执行多维查询
        results = self.query(
            year=target_year,
            term=target_term,
            week=target_week,
            day_of_week=target_dow,
            section_start=sec_start,
            section_end=sec_end,
            building=target_building,
            room_name=room_name,
            page=page,
            page_size=page_size,
        )

        # 5. 过滤最低座位数要求
        if min_seats > 0 and isinstance(results, list):
            results = [r for r in results if r.seats >= min_seats]

        return results
