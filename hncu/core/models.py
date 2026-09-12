"""
HNCU SDK 数据结构模型模块
提供类型提示与友好的数据对象封装
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class StudentProfile:
    """学生/用户基础身份档案"""
    user_id: str
    user_name: str
    class_name: str
    class_id: str
    grade: str
    profession_name: str
    department: str
    role_id: str
    first_login_time: str
    session_key: str
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "StudentProfile":
        return cls(
            user_id=str(d.get("userId", "")),
            user_name=str(d.get("userName", "")),
            class_name=str(d.get("className", "")),
            class_id=str(d.get("bjid", "")),
            grade=str(d.get("grade", "")),
            profession_name=str(d.get("professionName", "")),
            department=str(d.get("department", "")),
            role_id=str(d.get("roleId", "")),
            first_login_time=str(d.get("firstLoginTime", "")),
            session_key=str(d.get("session_key", "")),
            raw_data=d
        )


@dataclass
class GradeItem:
    """单门课程成绩项"""
    course_name: str          # 课程名称 (kcmc)
    course_code: str          # 课程代码 (kch)
    score: str                # 最终成绩 (cj)
    grade_point: float        # 绩点 (jd)
    credit: float             # 学分 (xf)
    course_nature: str        # 课程性质 (kcxzmc: 必修/选修/通识等)
    exam_nature: str          # 考试性质 (ksxz: 正常考试/补考/重修)
    normal_score: str = ""    # 平时成绩 (pscj: 需教务处开放分项权限，HNCU 默认策略下为空)
    final_score: str = ""     # 期末成绩 (qmcj: 需教务处开放分项权限，HNCU 默认策略下为空)
    year: str = ""            # 学年 (xnm)
    term: str = ""            # 学期 (xqm)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_passed(self) -> bool:
        """是否及格/通过（总成绩 >= 60 或等级评定非不及格）"""
        try:
            val = float(self.score)
            return val >= 60.0
        except (ValueError, TypeError):
            return self.score.strip() not in ("不及格", "不合格", "缺考", "违纪", "作弊", "0", "")

    @property
    def is_makeup(self) -> bool:
        """是否为补考或重修成绩"""
        return "补考" in self.exam_nature or "重修" in self.exam_nature

    @property
    def term_display(self) -> str:
        """获取学期友好展示名称 (第 1 学期, 第 2 学期, 第 3 学期 (暑假实习))"""
        from .constants import Term
        return Term.get_display_name(self.term)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GradeItem":
        try:
            gp = float(d.get("jd", 0.0) or 0.0)
        except (ValueError, TypeError):
            gp = 0.0

        try:
            cr = float(d.get("xf", 0.0) or 0.0)
        except (ValueError, TypeError):
            cr = 0.0

        return cls(
            course_name=str(d.get("kcmc", "")),
            course_code=str(d.get("kch_id", d.get("kch", ""))),
            score=str(d.get("cj", "")),
            grade_point=gp,
            credit=cr,
            course_nature=str(d.get("kcxzmc", "")),
            exam_nature=str(d.get("ksxz", "")),
            normal_score=str(d.get("pscj", "")),
            final_score=str(d.get("qmcj", "")),
            year=str(d.get("xnm", "")),
            term=str(d.get("xqm", "")),
            raw_data=d
        )


@dataclass
class CourseItem:
    """单门课程时间表项"""
    course_name: str          # 课程名 (kcmc)
    teacher: str              # 任课教师 (xm)
    classroom: str            # 上课教室/地点 (cdmc)
    day_of_week: int          # 星期几 (xqj: 1-7)
    section_display: str      # 节次显示 (jc: 如 "1-2节")
    weeks_display: str        # 周次显示 (zcd: 如 "1-16周(单)")
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CourseItem":
        return cls(
            course_name=str(d.get("kcmc", "")),
            teacher=str(d.get("xm", "")),
            classroom=str(d.get("cdmc", "")),
            day_of_week=int(d.get("xqj", 0) or 0),
            section_display=str(d.get("jc", "")),
            weeks_display=str(d.get("zcd", "")),
            raw_data=d
        )


@dataclass
class ExamItem:
    """期末考试安排项"""
    course_name: str          # 考试科目 (kcmc)
    exam_time: str            # 考试时间 (kssj)
    exam_room: str            # 考场地点 (cdmc)
    seat_number: str          # 座位号 (zwh)
    exam_type: str            # 考查形式 (ksfs)
    exam_name: str = ""       # 考试轮次/名称 (ksmc)
    credit: str = ""          # 学分 (xf)
    campus: str = ""          # 校区 (cdxqmc)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ExamItem":
        seat = str(d.get("zwh") or d.get("zw") or "").strip()
        if not seat or seat.lower() == "none":
            seat = "-"
        return cls(
            course_name=str(d.get("kcmc", "")).strip(),
            exam_time=str(d.get("kssj", "")).strip(),
            exam_room=str(d.get("cdmc", "")).strip(),
            seat_number=seat,
            exam_type=str(d.get("ksfs", "")).strip(),
            exam_name=str(d.get("ksmc", "")).strip(),
            credit=str(d.get("xf", "")).strip(),
            campus=str(d.get("cdxqmc", "")).strip(),
            raw_data=d
        )


@dataclass
class AddressBookMember:
    """班级通讯录成员"""
    user_id: str              # 学号 (XH / xh)
    user_name: str            # 姓名 (XM / xm)
    phone: str                # 手机号 (SJHM / lxdh)
    backup_phone: str         # 备用手机号 (BDSJH)
    gender: str               # 性别 (XB / xb)
    dormitory: str            # 宿舍 (ssh)
    class_id: str             # 班级ID (BJID)
    college_name: str         # 学院 (BMMC)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AddressBookMember":
        return cls(
            user_id=str(d.get("XH") or d.get("xh") or d.get("userId") or ""),
            user_name=str(d.get("XM") or d.get("xm") or d.get("userName") or ""),
            phone=str(d.get("SJHM") or d.get("lxdh") or d.get("phone") or ""),
            backup_phone=str(d.get("BDSJH") or ""),
            gender=str(d.get("XB") or d.get("xb") or d.get("gender") or ""),
            dormitory=str(d.get("ssh") or d.get("dormitory") or ""),
            class_id=str(d.get("BJID") or d.get("bjid") or ""),
            college_name=str(d.get("BMMC") or d.get("bmmc") or ""),
            raw_data=d
        )


@dataclass
class NewsItem:
    """校园资讯与通知项"""
    title: str
    date: str
    url: str
    category: str
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StudentDetail:
    """学生教务系统完整学籍详细档案"""
    user_id: str                      # 学号 (xh)
    user_name: str                    # 姓名 (xm)
    pinyin: str                       # 姓名拼音 (xmpy)
    gender: str                       # 性别 (xbm)
    id_card_type: str                 # 证件类型 (zjlxm)
    id_card_number: str               # 身份证/证件号码 (zjhm)
    birthday: str                     # 出生日期 (csrq)
    nation: str                       # 民族 (mzm)
    political_status: str             # 政治面貌 (zzmmm)
    enrollment_date: str              # 入学日期 (rxrq)
    native_place: str                 # 籍贯 (jg)
    household_location: str           # 户口所在地 (hkszd)
    source_location: str              # 生源地 (syd)
    grade: str                        # 年级 (njdm_id)
    department: str                   # 学院 (jg_id)
    major: str                        # 专业 (zyh_id)
    class_name: str                   # 班级 (bh_id)
    schooling_years: str              # 学制 (xz)
    student_status: str               # 学籍状态 (xjztdm)
    is_in_school: str                 # 是否在校 (sfzx)
    education_level: str              # 学历层次 (xlccdm)
    training_mode: str                # 培养方式 (pyfsdm)
    photo_url: str                    # 照片图片地址
    fields: Dict[str, str] = field(default_factory=dict)  # 原始键值对字典


@dataclass
class EmptyClassroomItem:
    """空闲教室信息项"""
    room_id: str                      # 教室场地ID (cd_id)
    room_code: str                    # 场地编号 (cdbh)
    room_name: str                    # 教室名称 (cdmc)
    room_type: str                    # 场地类别 (cdlbmc, 如多媒体教室)
    building_name: str                # 教学楼名称 (jxlmc)
    building_code: str                # 教学楼编号 (lh)
    campus_name: str                  # 校区 (xqmc)
    seats: int                        # 总座位数 (zws)
    exam_seats: int                   # 考试座位数 (kszws1)
    department: str                   # 归属管理部门 (jgmc)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EmptyClassroomItem":
        def _to_int(val):
            try:
                return int(val)
            except (ValueError, TypeError):
                return 0

        return cls(
            room_id=str(d.get("cd_id", "")),
            room_code=str(d.get("cdbh", "")),
            room_name=str(d.get("cdmc", "")),
            room_type=str(d.get("cdlbmc", "")),
            building_name=str(d.get("jxlmc", "")),
            building_code=str(d.get("lh", "")),
            campus_name=str(d.get("xqmc", "")),
            seats=_to_int(d.get("zws", 0)),
            exam_seats=_to_int(d.get("kszws1", 0)),
            department=str(d.get("jgmc", "")),
            raw_data=d
        )


@dataclass
class EvaluationSummary:
    """教学评价整体概况"""
    saved_count: int                  # 保存门次 (bcgs)
    submitted_count: int              # 提交门次 (tjgs)
    unrated_count: int                # 未评门次 (wpgs)
    prompt_message: str               # 评价提示信息 (pjtsxx)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_all_completed(self) -> bool:
        """是否全部评价完成 (未评和保存均为 0)"""
        return self.unrated_count == 0 and self.saved_count == 0

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EvaluationSummary":
        def _to_int(val):
            try:
                return int(val)
            except (ValueError, TypeError):
                return 0

        return cls(
            saved_count=_to_int(d.get("bcgs", 0)),
            submitted_count=_to_int(d.get("tjgs", 0)),
            unrated_count=_to_int(d.get("wpgs", 0)),
            prompt_message=str(d.get("pjtsxx", "")),
            raw_data=d
        )


@dataclass
class EvaluationCourseItem:
    """可评价教学班/课程项"""
    teaching_class_id: str            # 教学班ID (jxb_id)
    course_id: str                    # 课程号ID (kch_id)
    teacher_id: str                   # 教师工号ID (jgh_id)
    teacher_name: str                 # 教师姓名 (jzgmc)
    course_name: str                  # 课程名称 (kcmc)
    teaching_class_name: str          # 教学班名称 (jxbmc)
    period_code: str                  # 学时代码 (xsdm: "01" 理论, "03" 实践)
    period_name: str                  # 学时名称 (xsmc)
    status_code: str                  # 状态代码 (tjzt: "1" 已提交, "0" 已保存, "-1" 未评)
    status_name: str                  # 状态名称 (tjztmc: 提交/保存/未评)
    template_id: str                  # 评价模版ID (pjmbmcb_id)
    is_grade_teacher: str             # 是否成绩录入教师 (sfcjlrjs)
    department: str                   # 开课学院 (jgmc)
    score: Optional[str]              # 最终评分 (bfzpf)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_submitted(self) -> bool:
        """是否已经最终提交"""
        return self.status_code == "1"

    @property
    def is_saved(self) -> bool:
        """是否为暂存状态"""
        return self.status_code == "0"

    @property
    def is_unrated(self) -> bool:
        """是否为完全未评状态"""
        return self.status_code == "-1"

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EvaluationCourseItem":
        return cls(
            teaching_class_id=str(d.get("jxb_id", "")),
            course_id=str(d.get("kch_id", "")),
            teacher_id=str(d.get("jgh_id", "")),
            teacher_name=str(d.get("jzgmc", "")),
            course_name=str(d.get("kcmc", "")).strip(),
            teaching_class_name=str(d.get("jxbmc", "")).strip(),
            period_code=str(d.get("xsdm", "01")),
            period_name=str(d.get("xsmc", "理论")),
            status_code=str(d.get("tjzt", "-1")),
            status_name=str(d.get("tjztmc", "未评")),
            template_id=str(d.get("pjmbmcb_id", "")),
            is_grade_teacher=str(d.get("sfcjlrjs", "1")),
            department=str(d.get("jgmc", "")),
            score=str(d.get("bfzpf", "")) if d.get("bfzpf") else None,
            raw_data=d
        )
