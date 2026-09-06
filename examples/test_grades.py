#!/usr/bin/env python3
"""
测试单元：正方教务系统历史成绩查询
通过 test_auth 模块引入共享登录会话
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hncu import Term
from test_auth import get_authenticated_client
from terminal_fx import print_banner, scramble_reveal, COLOR_GREEN, COLOR_CYAN, COLOR_YELLOW, COLOR_BOLD, COLOR_RESET


def main():
    print_banner("成绩查询测试单元", "正方教务系统 - 学生历年全部考试成绩获取")

    client = get_authenticated_client(auto_sso=True)

    query_year = os.getenv("HNCU_YEAR", "")
    query_term = os.getenv("HNCU_TERM", "")
    
    if query_year or query_term:
        t_name = Term.get_display_name(query_term) if query_term else "全部学期"
        scramble_reveal(f"正在查询 {query_year or '历年'} {t_name} 课程成绩...", prefix="  🔍 ", duration=0.25, color=COLOR_YELLOW)
        grades = client.get_grades(year=query_year, term=query_term)
    else:
        scramble_reveal("正在拉取学生历年全部学期课程成绩记录...", prefix="  🔍 ", duration=0.25, color=COLOR_YELLOW)
        grades = client.get_grades()

    scramble_reveal(f"查询成功！共获取到 {len(grades)} 门课程成绩记录：", prefix="  ✅ ", duration=0.25, color=COLOR_GREEN)
    print()

    # 赛博表头 (增加学期友好展示列)
    header = f"{'课程名称':<24} {'学期':<10} {'成绩':<8} {'绩点':<6} {'学分':<6} {'性质':<10}"
    print(f"  {COLOR_BOLD}{COLOR_CYAN}{header}{COLOR_RESET}")
    print(f"  {COLOR_CYAN}{'-' * 70}{COLOR_RESET}")

    # 前 8 门带字符动态解码
    for g in grades[:8]:
        name_str = f"{g.course_name[:20]:<24} {g.term_display:<10}"
        val_str = f"{g.score:<8} {g.grade_point:<6} {g.credit:<6} {g.course_nature:<10}"
        scramble_reveal(name_str + val_str, prefix="  ", duration=0.12, steps=4, color=COLOR_YELLOW)

    if len(grades) > 8:
        print(f"\n  ... 还有 {len(grades) - 8} 门课程已安全缓存，未完全展开")

    print()
    scramble_reveal("🎉 成绩查询单元测试执行完毕！", prefix="  ", duration=0.2, color=COLOR_GREEN)


if __name__ == "__main__":
    main()
