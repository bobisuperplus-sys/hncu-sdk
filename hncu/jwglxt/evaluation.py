"""
正方教务系统 - 一键全自动教学评价服务模块
"""
import json
import random
import re
import time
from typing import Optional, List, Dict, Any, Union
from urllib.parse import quote
import requests

from ..core.constants import BASE_URL_JWGLXT, USER_AGENT_WEB
from ..core.exceptions import NetworkError, SessionExpiredError, BusinessLogicError
from ..core.models import EvaluationSummary, EvaluationCourseItem
from ..core.session import HncuSession
from ..auth.auth_service import AuthService


# 默认优质好评评语池（自动轮换，生动丰富且无敏感词）
DEFAULT_POSITIVE_COMMENTS = [
    "老师备课非常充分，讲课生动有趣，重点难点剖析清晰透彻，获益匪浅！",
    "教学态度极其认真负责，治学严严谨，耐心为同学们答疑解惑，深受大家喜爱！",
    "课堂互动积极活跃，教学内容前沿丰富，理论结合实际，实践指导性极强！",
    "授课逻辑严密条理清晰，由浅入深循循善诱，极大激发了同学们的专业学习兴趣！",
    "老师教学经验丰富，富有亲和力与感染力，对学生关怀备至，是一名非常优秀的教师！",
    "教学方法先进得当，课件图文并茂，课程安排科学合理，学习效果非常显著！",
    "上课仪态端庄规范，言传身教为人师表，不仅传授专业技能更引导大家树立远大目标！",
    "注重启发学生独立思考，因材施教耐心辅导，深受全班同学由衷尊敬与好评！",
]


class EvaluationService:
    """正方教务教学评价 (学生评价) 综合服务"""

    def __init__(self, hncu_session: HncuSession, auth_service: AuthService):
        self.hncu_session = hncu_session
        self.session = hncu_session.session
        self.auth = auth_service

    def _ensure_menu_context(self):
        """预热并激活学生评价功能模块会话权限上下文"""
        self.auth.ensure_sso()
        init_url = f"{BASE_URL_JWGLXT}/jwglxt/xspjgl/xspj_cxXspjIndex.html?doType=details&gnmkdm=N401605&layout=default"
        try:
            self.session.get(
                init_url,
                headers={"User-Agent": USER_AGENT_WEB},
                timeout=self.hncu_session.timeout,
            )
        except requests.RequestException:
            pass

    def get_summary(self) -> EvaluationSummary:
        """
        获取当前学期教学评价整体概况统计 (保存门数、已提交门数、未评门数)

        :return: EvaluationSummary 统计对象
        """
        self._ensure_menu_context()
        url = f"{BASE_URL_JWGLXT}/jwglxt/xspjgl/xspj_cxXspjqk.html"
        headers = {
            "User-Agent": USER_AGENT_WEB,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{BASE_URL_JWGLXT}/jwglxt/xspjgl/xspj_cxXspjIndex.html?doType=details&gnmkdm=N401605",
        }

        try:
            resp = self.session.post(url, headers=headers, timeout=self.hncu_session.timeout)
            resp.raise_for_status()
            res_json = resp.json()
        except requests.RequestException as e:
            raise NetworkError(f"获取评价概况网络异常: {e}") from e
        except json.JSONDecodeError as e:
            raise BusinessLogicError(f"服务端响应非预期数据: {resp.text[:200]}") from e

        return EvaluationSummary.from_dict(res_json)

    def get_evaluable_courses(self, status: Optional[str] = None) -> List[EvaluationCourseItem]:
        """
        获取当前学期所有可评价的教学班/课程列表

        :param status: 过滤状态 (可选: "unrated": 仅未评, "saved": 仅暂存, "submitted": 仅已提交, None: 全量)
        :return: EvaluationCourseItem 列表
        """
        self._ensure_menu_context()
        url = f"{BASE_URL_JWGLXT}/jwglxt/xspjgl/xspj_cxXspjIndex.html?doType=query&gnmkdm=N401605"
        headers = {
            "User-Agent": USER_AGENT_WEB,
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{BASE_URL_JWGLXT}/jwglxt/xspjgl/xspj_cxXspjIndex.html?doType=details&gnmkdm=N401605",
        }
        post_data = {
            "_search": "false",
            "nd": str(int(time.time() * 1000)),
            "queryModel.showCount": "100",
            "queryModel.currentPage": "1",
            "queryModel.sortName": "kcmc,jzgmc",
            "queryModel.sortOrder": "asc",
            "time": "0",
        }

        try:
            resp = self.session.post(url, data=post_data, headers=headers, timeout=self.hncu_session.timeout)
            resp.raise_for_status()
            res_json = resp.json()
        except requests.RequestException as e:
            raise NetworkError(f"获取可评价课程列表网络异常: {e}") from e
        except json.JSONDecodeError as e:
            raise BusinessLogicError(f"服务端响应非预期格式: {resp.text[:200]}") from e

        raw_items = res_json.get("items", [])
        items = [EvaluationCourseItem.from_dict(it) for it in raw_items]

        if status:
            s = status.lower().strip()
            if s in ("unrated", "未评", "-1"):
                items = [it for it in items if it.is_unrated]
            elif s in ("saved", "暂存", "0"):
                items = [it for it in items if it.is_saved]
            elif s in ("submitted", "已提交", "1"):
                items = [it for it in items if it.is_submitted]

        return items

    def get_course_detail_html(self, course: EvaluationCourseItem) -> str:
        """
        获取指定教学班的评价表单详情 HTML (内含打分指标与选项模板)
        """
        self._ensure_menu_context()
        url = f"{BASE_URL_JWGLXT}/jwglxt/xspjgl/xspj_cxXspjDisplay.html"
        headers = {
            "User-Agent": USER_AGENT_WEB,
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{BASE_URL_JWGLXT}/jwglxt/xspjgl/xspj_cxXspjIndex.html?doType=details&gnmkdm=N401605",
        }
        post_data = {
            "jxb_id": course.teaching_class_id,
            "kch_id": course.course_id,
            "xsdm": course.period_code,
            "jgh_id": course.teacher_id,
            "tjzt": course.status_code,
            "pjmbmcb_id": course.template_id,
            "sfcjlrjs": course.is_grade_teacher,
        }

        try:
            resp = self.session.post(url, data=post_data, headers=headers, timeout=self.hncu_session.timeout)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            raise NetworkError(f"获取评价表单详情网络异常: {e}") from e

    def parse_evaluation_payload(
        self,
        course: EvaluationCourseItem,
        detail_html: str,
        comment: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        根据获取到的表单 HTML，精准解析指标树并组装正方教务系统 buildRequestMap 数据字典
        """
        # 1. 提取主体比率与参数
        # ztpjbl, jszdpjbl, xykzpjbl
        ztpjbl = "100"
        jszdpjbl = "0"
        xykzpjbl = "0"
        m_bl = re.search(r'data-ztpjbl=["\'](\d+)["\']', detail_html)
        if m_bl:
            ztpjbl = m_bl.group(1)

        # 2. 提取评价模版信息 (panel-pjdx)
        # pjmbmcb_id, pjmbmc, pjdxdm, fxzgf, xspfb_id
        pjmbmcb_id = course.template_id
        pjmbmc = "学生评价教师"
        pjdxdm = "01"
        xspfb_id = ""

        m_pjmb = re.search(r'class=["\'][^"\']*panel-pjdx[^"\']*["\'][^>]*data-pjmbmcb_id=["\']([^"\']+)["\']', detail_html)
        if m_pjmb:
            pjmbmcb_id = m_pjmb.group(1)
        m_mc = re.search(r'data-pjmbmc=["\']([^"\']+)["\']', detail_html)
        if m_mc:
            pjmbmc = m_mc.group(1)
        m_xspfb = re.search(r'data-xspfb_id=["\']([^"\']+)["\']', detail_html)
        if m_xspfb:
            xspfb_id = m_xspfb.group(1)

        # 评语
        py_text = comment or random.choice(DEFAULT_POSITIVE_COMMENTS)

        data_map: Dict[str, str] = {
            "ztpjbl": ztpjbl,
            "jszdpjbl": jszdpjbl,
            "xykzpjbl": xykzpjbl,
            "jxb_id": course.teaching_class_id,
            "kch_id": course.course_id,
            "jgh_id": course.teacher_id,
            "xsdm": course.period_code,
            "modelList[0].pjmbmcb_id": pjmbmcb_id,
            "modelList[0].pjmbmc": pjmbmc,
            "modelList[0].pjdxdm": pjdxdm,
            "modelList[0].fxzgf": "",
            "modelList[0].py": quote(py_text),
            "modelList[0].xspfb_id": xspfb_id,
            "modelList[0].sfbhmgc": "0",
        }

        # 3. 提取指标与打分选项 (table.table-xspj 和 tr.tr-xspj)
        # 寻找最高等级的 pfdjdmb_id (默认为优秀档 GUID)
        default_pfdjdmb_id = "B5F66153831C60B2E055C18C75144BC0"
        m_dj = re.search(r'data-pfdjdmb_id=["\']([^"\']+)["\']', detail_html)
        if m_dj:
            default_pfdjdmb_id = m_dj.group(1)

        # 按 table-xspj 切分一级指标
        table_matches = re.findall(r'(<table[^>]*class=["\'][^"\']*table-xspj[^"\']*["\'][^>]*>.*?</table>)', detail_html, re.DOTALL)
        if not table_matches:
            # 尝试宽松匹配
            table_matches = [detail_html]

        for i, tbl_html in enumerate(table_matches):
            # 从 table 标签本身提取一级指标 ID
            m_tbl_tag = re.search(r'<table[^>]*>', tbl_html)
            m_parent_zbxm = None
            if m_tbl_tag:
                m_parent_zbxm = re.search(r'data-pjzbxm_id=["\']([^"\']+)["\']', m_tbl_tag.group(0))
            if not m_parent_zbxm:
                m_parent_zbxm = re.search(r'data-pjzbxm_id=["\']([^"\']+)["\']', tbl_html)

            if m_parent_zbxm:
                data_map[f"modelList[0].xspjList[{i}].pjzbxm_id"] = m_parent_zbxm.group(1)

            # 二级具体指标
            tr_matches = re.findall(r'<tr[^>]*class=["\'][^"\']*tr-xspj[^"\']*["\'][^>]*>', tbl_html)
            for j, tr_tag in enumerate(tr_matches):
                m_sub_zbxm = re.search(r'data-pjzbxm_id=["\']([^"\']+)["\']', tr_tag)
                m_sub_dj = re.search(r'data-pfdjdmb_id=["\']([^"\']+)["\']', tr_tag)
                m_sub_zs = re.search(r'data-zsmbmcb_id=["\']([^"\']+)["\']', tr_tag)

                sub_zbxm_id = m_sub_zbxm.group(1) if m_sub_zbxm else ""
                sub_dj_id = m_sub_dj.group(1) if m_sub_dj else default_pfdjdmb_id
                sub_zs_id = m_sub_zs.group(1) if m_sub_zs else pjmbmcb_id

                prefix = f"modelList[0].xspjList[{i}].childXspjList[{j}]"
                data_map[f"{prefix}.pjf"] = ""
                data_map[f"{prefix}.pjzbxm_id"] = sub_zbxm_id
                data_map[f"{prefix}.pfdjdmb_id"] = sub_dj_id
                data_map[f"{prefix}.zsmbmcb_id"] = sub_zs_id

        data_map["modelList[0].pjzt"] = "1"  # 标记已评完
        return data_map

    def evaluate_course(
        self,
        course: EvaluationCourseItem,
        comment: Optional[str] = None,
        submit: bool = True,
    ) -> Dict[str, Any]:
        """
        对单门课程执行教学评价（全自动组装指标、打分并提交或暂存）

        :param course: 可评价教学班对象 (EvaluationCourseItem)
        :param comment: 评价评语 (留空则从优质评语库中智能随机选取)
        :param submit: 是否执行最终提交 (True: 提交锁定, False: 仅暂存)
        :return: 接口返回信息字典
        """
        detail_html = self.get_course_detail_html(course)
        payload = self.parse_evaluation_payload(course, detail_html, comment=comment)

        endpoint = "/jwglxt/xspjgl/xspj_tjXspj.html" if submit else "/jwglxt/xspjgl/xspj_bcXspj.html"
        payload["tjzt"] = "1" if submit else "0"

        url = f"{BASE_URL_JWGLXT}{endpoint}"
        headers = {
            "User-Agent": USER_AGENT_WEB,
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{BASE_URL_JWGLXT}/jwglxt/xspjgl/xspj_cxXspjIndex.html?doType=details&gnmkdm=N401605",
        }

        try:
            resp = self.session.post(url, data=payload, headers=headers, timeout=self.hncu_session.timeout)
            resp.raise_for_status()
            text = resp.text
        except requests.RequestException as e:
            raise NetworkError(f"提交评价网络异常: {e}") from e

        is_success = "成功" in text
        return {
            "success": is_success,
            "message": text,
            "course_name": course.course_name,
            "teacher_name": course.teacher_name,
            "is_submit": submit,
        }

    def auto_evaluate_all(
        self,
        comment: Optional[str] = None,
        submit: bool = True,
        delay: float = 0.5,
    ) -> Dict[str, Any]:
        """
        【一键全自动批量评教】
        自动检索当前学期所有未评完的课程教学班，自动完成高分指标评级与优质评语填写，并一键提交。

        :param comment: 自定义评语 (若不填则自动从高质量评语池智能随机抽取)
        :param submit: 是否自动提交锁定 (默认 True)
        :param delay: 每门课程评价间隔时间 (秒，默认 0.5 秒，避免过载)
        :return: 批量评价执行统计报告
        """
        summary_before = self.get_summary()
        all_courses = self.get_evaluable_courses()
        pending_courses = [c for c in all_courses if not c.is_submitted]

        results = []
        success_count = 0
        failed_count = 0

        for idx, course in enumerate(pending_courses, start=1):
            cur_comment = comment or random.choice(DEFAULT_POSITIVE_COMMENTS)
            try:
                res = self.evaluate_course(course, comment=cur_comment, submit=submit)
                if res.get("success"):
                    success_count += 1
                else:
                    failed_count += 1
                results.append(res)
            except Exception as e:
                failed_count += 1
                results.append({
                    "success": False,
                    "message": str(e),
                    "course_name": course.course_name,
                    "teacher_name": course.teacher_name,
                })

            if delay > 0 and idx < len(pending_courses):
                time.sleep(delay)

        return {
            "total_courses": len(all_courses),
            "pending_count": len(pending_courses),
            "success_count": success_count,
            "failed_count": failed_count,
            "all_completed": (failed_count == 0 and len(pending_courses) > 0),
            "details": results,
        }
