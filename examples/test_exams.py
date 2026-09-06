#!/usr/bin/env python3
"""
测试单元：正方教务系统期末考场与日程查询
通过 test_auth 模块引入共享登录会话
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hncu import Term
from test_auth import get_authenticated_client
from terminal_fx import (
    print_banner,
    scramble_reveal,
    pad_display,
    COLOR_GREEN,
    COLOR_CYAN,
    COLOR_YELLOW,
    COLOR_BOLD,
    COLOR_RESET,
)


def main():
    print_banner("考试安排测试单元", "正方教务系统 - 期末考试考场、座位号与日程")

    client = get_authenticated_client(auto_sso=True)

    query_year = os.getenv("HNCU_YEAR", "2024")
    query_term = int(os.getenv("HNCU_TERM", "1"))
    term_display = Term.get_display_name(query_term)
    scramble_reveal(f"正在检索 {query_year} 学年{term_display}期末考场数据...", prefix="  📝 ", duration=0.25, color=COLOR_YELLOW)
    exams = client.get_exams(year=query_year, term=query_term)

    if exams:
        scramble_reveal(f"查询成功！共获取到 {len(exams)} 门期末考试安排：", prefix="  ✅ ", duration=0.2, color=COLOR_GREEN)
        print()
        col_course = pad_display("考试科目", 24)
        col_time = pad_display("考试时间", 26)
        col_room = pad_display("考场地点", 18)
        col_type = pad_display("形式", 8)
        col_seat = pad_display("座位号", 8)
        header = f"{col_course} {col_time} {col_room} {col_type} {col_seat}"
        print(f"  {COLOR_BOLD}{COLOR_CYAN}{header}{COLOR_RESET}")
        print(f"  {COLOR_CYAN}{'-' * 88}{COLOR_RESET}")
        for ex in exams:
            c_name = pad_display(ex.course_name[:11], 24)
            c_time = pad_display(ex.exam_time, 26)
            c_room = pad_display(ex.exam_room, 18)
            c_type = pad_display(ex.exam_type or "笔试", 8)
            c_seat = pad_display(ex.seat_number, 8)
            row = f"{c_name} {c_time} {c_room} {c_type} {c_seat}"
            scramble_reveal(row, prefix="  ", duration=0.12, steps=4, color=COLOR_YELLOW)
    else:
        scramble_reveal(f"{query_year} 学年{term_display}当前未排考或已完成考务归档", prefix="  📌 ", duration=0.2, color=COLOR_GREEN)

    print()
    scramble_reveal("🎉 考试安排单元测试执行完毕！", prefix="  ", duration=0.2, color=COLOR_GREEN)


if __name__ == "__main__":
    main()
