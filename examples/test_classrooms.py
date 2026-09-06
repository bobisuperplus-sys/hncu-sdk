#!/usr/bin/env python3
"""
测试单元：正方教务系统空闲自习教室检索
通过 test_auth 模块引入共享登录会话
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hncu import Term
from test_auth import get_authenticated_client
from terminal_fx import print_banner, scramble_reveal, COLOR_GREEN, COLOR_CYAN, COLOR_YELLOW, COLOR_BOLD, COLOR_RESET


def main():
    print_banner("空闲教室测试单元", "正方教务系统 - 周次与节次位掩码检索空闲教室")

    client = get_authenticated_client(auto_sso=True)

    query_year = int(os.getenv("HNCU_YEAR", "2024"))
    query_term = 1  # 传入直观学期数字 1 (第 1 学期 / 上学期)，SDK 自动映射为教务代码 3
    week = 1
    day_of_week = 1
    s_start = 1
    s_end = 2

    term_name = Term.get_display_name(query_term)
    cond = f"{query_year}学年 {term_name} 第{week}周 星期{day_of_week} 第{s_start}-{s_end}节"
    scramble_reveal(f"查询条件: {cond}", prefix="  🏫 ", duration=0.2, color=COLOR_YELLOW)

    classrooms = client.get_empty_classrooms(
        year=query_year,
        term=query_term,
        week=week,
        day_of_week=day_of_week,
        section_start=s_start,
        section_end=s_end,
        page=1,
        page_size=12,
    )

    scramble_reveal(f"查询成功！检索到 {len(classrooms)} 间空闲教室：", prefix="  ✅ ", duration=0.2, color=COLOR_GREEN)
    print()

    header = f"{'场地编号':<10} {'教室名称':<16} {'教学楼':<16} {'校区':<10} {'座位':<6} {'类别':<12}"
    print(f"  {COLOR_BOLD}{COLOR_CYAN}{header}{COLOR_RESET}")
    print(f"  {COLOR_CYAN}{'-' * 74}{COLOR_RESET}")

    for room in classrooms:
        row = f"{room.room_code:<10} {room.room_name:<16} {room.building_name:<16} {room.campus_name:<10} {room.seats:<6} {room.room_type:<12}"
        scramble_reveal(row, prefix="  ", duration=0.1, steps=3, color=COLOR_YELLOW)

    print()
    scramble_reveal("🎉 空闲教室检索单元测试执行完毕！", prefix="  ", duration=0.2, color=COLOR_GREEN)


if __name__ == "__main__":
    main()
