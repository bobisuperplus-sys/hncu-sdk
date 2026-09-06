"""
正方教务系统 - 学生完整学籍详细档案服务
"""
import re
from typing import Union, Dict
import requests

from ..core.constants import BASE_URL_JWGLXT, USER_AGENT_WEB
from ..core.exceptions import NetworkError
from ..core.models import StudentDetail
from ..core.session import HncuSession
from ..auth.auth_service import AuthService


class StudentService:
    """学生学籍档案查询服务"""

    def __init__(self, hncu_session: HncuSession, auth_service: AuthService):
        self.hncu_session = hncu_session
        self.session = hncu_session.session
        self.auth = auth_service

    def get_detail(self, raw: bool = False) -> Union[StudentDetail, Dict[str, str]]:
        """
        查询正方教务系统中的完整学生学籍档案信息（包括政治面貌、籍贯、身份证号、培养方式等）

        :param raw: 是否返回原始解析出的字典
        :return: StudentDetail 强类型对象或字段字典
        """
        self.auth.ensure_sso()
        url = f"{BASE_URL_JWGLXT}/jwglxt/xsxxxggl/xsgrxxwh_cxXsgrxx.html?gnmkdm=N100801&layout=default"
        headers = {
            "User-Agent": USER_AGENT_WEB,
            "Referer": f"{BASE_URL_JWGLXT}/jwglxt/xtgl/index_initMenu.html?jsdm=xs",
        }

        try:
            resp = self.session.get(url, headers=headers, timeout=self.hncu_session.timeout)
            resp.raise_for_status()
            html_text = resp.text
        except requests.RequestException as e:
            raise NetworkError(f"学籍详细档案获取失败: {e}") from e

        # 正则提取所有 col_{name} 字段
        matches = re.findall(
            r'id=["\']col_([a-zA-Z0-9_]+)["\'][^>]*>[\s\S]*?<p[^>]*class=["\'][^"\']*form-control-static[^"\']*["\'][^>]*>([\s\S]*?)</p>',
            html_text,
        )
        fields = {}
        for k, v in matches:
            clean_v = re.sub(r"<[^>]+>", "", v).strip()
            fields[k] = clean_v

        if raw:
            return fields

        uid = fields.get("xh") or (self.auth.profile.user_id if self.auth.profile else "")
        photo_url = f"{BASE_URL_JWGLXT}/jwglxt/xtgl/photo_cxXszp4.html?xh_id={uid}&zplx=rxhzp"

        return StudentDetail(
            user_id=fields.get("xh", uid),
            user_name=fields.get("xm", self.auth.profile.user_name if self.auth.profile else ""),
            pinyin=fields.get("xmpy", ""),
            gender=fields.get("xbm", ""),
            id_card_type=fields.get("zjlxm", ""),
            id_card_number=fields.get("zjhm", ""),
            birthday=fields.get("csrq", ""),
            nation=fields.get("mzm", ""),
            political_status=fields.get("zzmmm", ""),
            enrollment_date=fields.get("rxrq", ""),
            native_place=fields.get("jg", ""),
            household_location=fields.get("hkszd", ""),
            source_location=fields.get("syd", ""),
            grade=fields.get("njdm_id", ""),
            department=fields.get("jg_id", ""),
            major=fields.get("zyh_id", ""),
            class_name=fields.get("bh_id", ""),
            schooling_years=fields.get("xz", ""),
            student_status=fields.get("xjztdm", ""),
            is_in_school=fields.get("sfzx", ""),
            education_level=fields.get("xlccdm", ""),
            training_mode=fields.get("pyfsdm", ""),
            photo_url=photo_url,
            fields=fields,
        )
