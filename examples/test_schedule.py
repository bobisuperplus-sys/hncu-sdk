#!/usr/bin/env python3
"""
测试单元：正方教务系统学期个人课表查询
通过 test_auth 模块引入共享登录会话
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hncu import Term
from test_auth import get_authenticated_client
from terminal_fx import print_banner, scramble_reveal, COLOR_GREEN, COLOR_CYAN, COLOR_YELLOW, COLOR_BOLD, COLOR_RESET


def main():
    print_banner("课表查询测试单元", "正方教务系统 - 个人学期课程时间与教室查询")

    client = get_authenticated_client(auto_sso=True)

    query_year = os.getenv("HNCU_YEAR", "2023")
    scramble_reveal(f"正在查询 {query_year} 学年第 1 学期完整课表...", prefix="  📅 ", duration=0.25, color=COLOR_YELLOW)
    courses = client.get_schedule(year=query_year, term=Term.FIRST)

    scramble_reveal(f"查询成功！共检索到 {len(courses)} 门课程排期：", prefix="  ✅ ", duration=0.2, color=COLOR_GREEN)
    print()

    header = f"{'课程名称':<22} {'时间':<14} {'教室':<16} {'授课教师':<10}"
    print(f"  {COLOR_BOLD}{COLOR_CYAN}{header}{COLOR_RESET}")
    print(f"  {COLOR_CYAN}{'-' * 66}{COLOR_RESET}")

    for c in courses[:6]:
        time_str = f"周{c.day_of_week} {c.section_display}"
        row = f"{c.course_name[:18]:<22} {time_str:<14} {c.classroom[:14]:<16} {c.teacher:<10}"
        scramble_reveal(row, prefix="  ", duration=0.12, steps=4, color=COLOR_YELLOW)

    if len(courses) > 6:
        print(f"\n  ... 还有 {len(courses) - 6} 门课程已安全缓存")

    print()
    scramble_reveal("🎉 课表查询单元测试执行完毕！", prefix="  ", duration=0.2, color=COLOR_GREEN)


if __name__ == "__main__":
    main()
