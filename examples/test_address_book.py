#!/usr/bin/env python3
"""
测试单元：移动校园班级通讯录与人员名单获取
通过 test_auth 模块引入共享登录会话
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from test_auth import get_authenticated_client
from terminal_fx import print_banner, scramble_reveal, COLOR_GREEN, COLOR_CYAN, COLOR_YELLOW, COLOR_BOLD, COLOR_RESET


def main():
    print_banner("通讯录测试单元", "移动校园 - 班级通讯录与人员信息列表")

    client = get_authenticated_client(auto_sso=False)

    scramble_reveal("正在请求移动校园班级通讯录加密数据包...", prefix="  👥 ", duration=0.25, color=COLOR_YELLOW)
    members = client.get_class_address_book()

    scramble_reveal(f"解密成功！班级当前共有 {len(members)} 位成员：", prefix="  ✅ ", duration=0.2, color=COLOR_GREEN)
    print()

    header = f"{'学号':<12} {'姓名':<10} {'性别':<6} {'联系电话':<16} {'所属学院':<16}"
    print(f"  {COLOR_BOLD}{COLOR_CYAN}{header}{COLOR_RESET}")
    print(f"  {COLOR_CYAN}{'-' * 64}{COLOR_RESET}")

    for m in members[:8]:
        row = f"{m.user_id:<12} {m.user_name:<10} {m.gender or '未知':<6} {m.phone or '未填':<16} {m.college_name:<16}"
        scramble_reveal(row, prefix="  ", duration=0.1, steps=3, color=COLOR_YELLOW)

    if len(members) > 8:
        print(f"\n  ... 还有 {len(members) - 8} 位同学已安全缓存")

    print()
    scramble_reveal("🎉 班级通讯录单元测试执行完毕！", prefix="  ", duration=0.2, color=COLOR_GREEN)


if __name__ == "__main__":
    main()
