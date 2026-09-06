"""
移动校园服务子模块导出
"""
from .address_book import AddressBookService
from .calendar import CalendarService
from .user_info import UserInfoService

__all__ = [
    "AddressBookService",
    "UserInfoService",
    "CalendarService",
]
