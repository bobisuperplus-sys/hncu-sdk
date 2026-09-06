"""
向后兼容转发模块
"""
from .core.models import *

__all__ = [
    "StudentProfile",
    "GradeItem",
    "CourseItem",
    "ExamItem",
    "AddressBookMember",
    "NewsItem",
    "StudentDetail",
    "EmptyClassroomItem",
]
