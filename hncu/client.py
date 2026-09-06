"""
HNCU SDK 统一客户端门面模块 (Facade)
聚合所有底层子模块服务，提供统一、优雅、开箱即用的开发接口
"""
from typing import Optional, Union, List, Dict, Any

from .core.constants import DEFAULT_UNIQUE_CODE_HEADER, NewsCategory, Term
from .core.crypto import HncuCrypto
from .core.models import (
    AddressBookMember,
    CourseItem,
    EmptyClassroomItem,
    ExamItem,
    GradeItem,
    NewsItem,
    StudentDetail,
    StudentProfile,
)
from .core.session import HncuSession
from .auth.auth_service import AuthService
from .jwglxt.grades import GradesService
from .jwglxt.schedule import ScheduleService
from .jwglxt.exams import ExamsService
from .jwglxt.classrooms import ClassroomService
from .jwglxt.student import StudentService
from .mobile.address_book import AddressBookService
from .mobile.user_info import UserInfoService
from .mobile.calendar import CalendarService
from .news.news_service import NewsService
from .account.account_service import AccountService


class HncuClient:
    """
    湖南城市学院 (HNCU) 综合开发工具包客户端
    """

    def __init__(
        self,
        unique_code: str = DEFAULT_UNIQUE_CODE_HEADER,
        timeout: int = 15,
        verify_ssl: bool = True,
        trust_env: bool = False,
    ):
        """
        初始化客户端

        :param unique_code: 移动客户端设备唯一识别码
        :param timeout: 请求超时时间 (秒)
        :param verify_ssl: 是否校验证书有效性
        :param trust_env: 是否继承系统环境代理 (默认 False，直连校园网避免超时)
        """
        # 1. 核心网络会话与加密引擎
        self.hncu_session = HncuSession(
            unique_code=unique_code,
            timeout=timeout,
            verify_ssl=verify_ssl,
            trust_env=trust_env,
        )
        self.session = self.hncu_session.session
        self.crypto = HncuCrypto()

        # 2. 注入认证服务
        self.auth = AuthService(self.hncu_session, self.crypto)

        # 3. 注入正方教务子服务
        self.grades = GradesService(self.hncu_session, self.auth)
        self.schedule = ScheduleService(self.hncu_session, self.auth)
        self.exams = ExamsService(self.hncu_session, self.auth)
        self.classrooms = ClassroomService(self.hncu_session, self.auth)
        self.student = StudentService(self.hncu_session, self.auth)

        # 4. 注入移动校园子服务
        self.address_book = AddressBookService(self.hncu_session, self.crypto, self.auth)
        self.user_info = UserInfoService(self.hncu_session, self.crypto, self.auth)
        self.calendar = CalendarService(self.hncu_session, self.crypto, self.auth)

        # 5. 注入公开资讯与账号安全子服务
        self.news_service = NewsService(self.hncu_session)
        self.account = AccountService(self.hncu_session, self.auth)

    # =========================================================================
    # 状态属性
    # =========================================================================

    @property
    def profile(self) -> Optional[StudentProfile]:
        """获取当前已登录用户的学生身份档案"""
        return self.auth.profile

    @property
    def is_sso_connected(self) -> bool:
        """检查正方教务系统单点登录会话是否已激活"""
        return self.auth.is_sso_connected

    # =========================================================================
    # 快捷门面 API (Facade Shortcuts - 保持 100% 向后兼容)
    # =========================================================================

    def login(self, user_id: str, password: str, auto_sso: bool = True) -> StudentProfile:
        """登录移动校园并（可选）自动打通正方教务系统单点登录"""
        return self.auth.login(user_id=user_id, password=password, auto_sso=auto_sso)

    def sso_connect(self) -> bool:
        """建立正方教务系统 CAS 单点登录免密会话"""
        return self.auth.sso_connect()

    def get_grades(
        self,
        year: Optional[Union[int, str]] = None,
        term: Union[Term, str] = Term.ALL,
        raw: bool = False,
    ) -> Union[List[GradeItem], Dict[str, Any]]:
        """查询学生历年或学期期末成绩"""
        return self.grades.query(year=year, term=term, raw=raw)

    def get_schedule(
        self,
        year: Union[int, str],
        term: Union[Term, str] = Term.FIRST,
        raw: bool = False,
    ) -> Union[List[CourseItem], Dict[str, Any]]:
        """查询个人学期课程表"""
        return self.schedule.query(year=year, term=term, raw=raw)

    def get_exams(
        self,
        year: Union[int, str],
        term: Union[Term, str] = Term.FIRST,
        raw: bool = False,
    ) -> Union[List[ExamItem], Dict[str, Any]]:
        """查询期末考试考场日程与座位"""
        return self.exams.query(year=year, term=term, raw=raw)

    def get_empty_classrooms(
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
        """查询空闲自习教室列表"""
        return self.classrooms.query(
            year=year,
            term=term,
            week=week,
            day_of_week=day_of_week,
            section_start=section_start,
            section_end=section_end,
            campus_id=campus_id,
            building=building,
            room_name=room_name,
            room_type=room_type,
            page=page,
            page_size=page_size,
            raw=raw,
        )

    def get_student_detail(self, raw: bool = False) -> Union[StudentDetail, Dict[str, str]]:
        """查询学生完整学籍详细档案（身份证号、民族、政治面貌、籍贯等）"""
        return self.student.get_detail(raw=raw)

    def get_class_address_book(
        self, class_id: Optional[str] = None, raw: bool = False
    ) -> Union[List[AddressBookMember], List[Dict[str, Any]]]:
        """获取班级通讯录与人员联系信息"""
        return self.address_book.get_members(class_id=class_id, raw=raw)

    def get_user_info(self, gh: Optional[str] = None) -> Dict[str, Any]:
        """获取教工或学生个人档案信息"""
        return self.user_info.get_info(gh=gh)

    def get_term_info(self) -> Dict[str, Any]:
        """获取当前学期校历时间信息"""
        return self.calendar.get_term_info()

    def get_news(
        self,
        category: NewsCategory = NewsCategory.NOTICE,
        page: int = 1,
        page_size: int = 10,
    ) -> List[NewsItem]:
        """获取校园公开新闻与通知公告（免登录）"""
        return self.news_service.get_news(category=category, page=page, page_size=page_size)

    def check_account(self, name: str, id_card: str) -> Dict[str, Any]:
        """检验统一身份认证账号状态"""
        return self.account.check_account(name=name, id_card=id_card)

    def change_password(self, old_password: str, new_password: str) -> Dict[str, Any]:
        """修改统一身份认证/移动校园密码"""
        return self.account.change_password(old_password=old_password, new_password=new_password)
