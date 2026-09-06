#!/usr/bin/env python3
"""
测试单元：移动校园校历与学期时间信息
通过 test_auth 模块引入共享登录会话
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from test_auth import get_authenticated_client
from terminal_fx import print_banner, print_status_item, scramble_reveal, COLOR_GREEN, COLOR_YELLOW


def main():
    print_banner("校历测试单元", "移动校园 - 当前学年学期校历与起止时间")

    client = get_authenticated_client(auto_sso=False)

    scramble_reveal("正在拉取最新学期与校历排期...", prefix="  📅 ", duration=0.25, color=COLOR_YELLOW)
    info = client.get_term_info()

    scramble_reveal("校历日程信息解析成功：", prefix="  ✅ ", duration=0.2, color=COLOR_GREEN)
    print()

    print_status_item("学年", info.get("xn", "未知"), icon="📆")
    print_status_item("学期编号", f"第 {info.get('xq', '未知')} 学期", icon="🔢")
    print_status_item("开学日期", info.get("ksrq", "未知"), icon="🏁")
    print_status_item("结束日期", info.get("jsrq", "未知"), icon="🛑")
    print_status_item("校历序列号", info.get("xlh", "未知"), icon="🆔")

    print()
    scramble_reveal("🎉 校历日程单元测试执行完毕！", prefix="  ", duration=0.2, color=COLOR_GREEN)


if __name__ == "__main__":
    main()
