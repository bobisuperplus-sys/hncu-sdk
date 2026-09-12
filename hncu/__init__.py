"""
HNCU Python SDK
湖南城市学院教务系统与移动校园服务 Python 开发工具包
"""

from .client import HncuClient
from .core.constants import NewsCategory, Term
from .core.crypto import BarrettRSA, HncuCrypto

from .core.exceptions import (
    CryptoError,
    HncuException,
    LoginFailedError,
    NetworkError,
    SessionExpiredError,
    SsoConnectError,
    BusinessLogicError,
)
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
from .portal.portal_service import PortalService
from .portal.models import ECardInfo, PortalProfile

__version__ = "0.4.0"
__author__ = "Yellowtown"

__all__ = [
    # 门面客户端
    "HncuClient",
    "HncuSession",
    "HncuCrypto",
    "BarrettRSA",
    "NewsCategory",
    "Term",

    # 数据模型
    "StudentProfile",
    "StudentDetail",
    "EmptyClassroomItem",
    "GradeItem",
    "CourseItem",
    "ExamItem",
    "AddressBookMember",
    "NewsItem",
    "ECardInfo",
    "PortalProfile",
    # 异常体系
    "HncuException",
    "CryptoError",
    "LoginFailedError",
    "SsoConnectError",
    "SessionExpiredError",
    "NetworkError",
    "BusinessLogicError",
    # 独立子服务
    "AuthService",
    "GradesService",
    "ScheduleService",
    "ExamsService",
    "ClassroomService",
    "StudentService",
    "AddressBookService",
    "UserInfoService",
    "CalendarService",
    "NewsService",
    "AccountService",
    "PortalService",
]
