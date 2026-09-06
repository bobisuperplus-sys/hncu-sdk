#!/usr/bin/env python3
"""
测试单元：正方教务系统学生完整学籍详细档案
通过 test_auth 模块引入共享登录会话
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from test_auth import get_authenticated_client
from terminal_fx import print_banner, print_status_item, scramble_reveal, COLOR_GREEN, COLOR_YELLOW


def main():
    print_banner("学籍档案测试单元", "正方教务系统 - 个人学籍详细档案与身份资料")

    client = get_authenticated_client(auto_sso=True)

    scramble_reveal("正在请求教务系统 DOM 结构并清洗个人学籍档案...", prefix="  🪪 ", duration=0.25, color=COLOR_YELLOW)
    detail = client.get_student_detail()

    scramble_reveal("学籍详细档案已安全解密与结构化提取：", prefix="  ✅ ", duration=0.2, color=COLOR_GREEN)
    print()

    print_status_item("姓名", f"{detail.user_name} ({detail.pinyin})", icon="👤")
    print_status_item("学号", detail.user_id, icon="🆔")
    print_status_item("性别", detail.gender, icon="⚧")
    print_status_item("证件类型", f"{detail.id_card_type} ({detail.id_card_number})", icon="🪪")
    print_status_item("民族", detail.nation, icon="👥")
    print_status_item("政治面貌", detail.political_status, icon="🚩")
    print_status_item("所属学院", detail.department, icon="🏛️")
    print_status_item("专业名称", detail.major, icon="🎓")
    print_status_item("行政班级", detail.class_name, icon="🏫")
    print_status_item("年级", detail.grade, icon="📅")
    print_status_item("学历层次", detail.education_level, icon="📜")
    print_status_item("学制", f"{detail.schooling_years} 年", icon="⏳")
    print_status_item("学籍状态", f"{detail.student_status} (在校: {detail.is_in_school})", icon="📌")

    print()
    scramble_reveal("🎉 学籍档案单元测试执行完毕！", prefix="  ", duration=0.2, color=COLOR_GREEN)


if __name__ == "__main__":
    main()
