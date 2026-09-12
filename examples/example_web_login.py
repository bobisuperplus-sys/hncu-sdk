#!/usr/bin/env python3
"""
示例脚本：统一身份认证平台 Web 端短信登录与 CAS SSO 单点登录演示
支持纯 Python 免浏览器环境获取短信验证码、提交登录并打通门户与教务系统
"""
import getpass
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hncu import HncuClient, LoginFailedError
from terminal_fx import (
    COLOR_CYAN,
    COLOR_GREEN,
    COLOR_RED,
    COLOR_YELLOW,
    print_banner,
    print_status_item,
    scramble_reveal,
)


def main():
    print_banner("Web 统一身份认证与 CAS SSO 测试", "基于 Barrett RSA 与短信双因子验证")

    client = HncuClient()

    user_id = os.getenv("HNCU_USER") or os.getenv("HNCU_USER_ID")
    password = os.getenv("HNCU_PASS") or os.getenv("HNCU_PASSWORD")

    if not user_id:
        if sys.stdin.isatty():
            user_id = input("请输入学号/工号: ").strip()
        else:
            print("错误: 非交互环境下需指定 HNCU_USER 环境变量")
            sys.exit(1)

    if not password:
        if sys.stdin.isatty():
            password = getpass.getpass("请输入密码: ").strip()
        else:
            print("错误: 非交互环境下需指定 HNCU_PASS 环境变量")
            sys.exit(1)

    # 步骤 1: 触发发送短信验证码
    scramble_reveal(
        f"正在请求统一认证平台向账号 [{user_id}] 绑定手机发送验证码...",
        prefix="  ⚡ ",
        duration=0.25,
        steps=8,
        color=COLOR_YELLOW,
    )
    try:
        client.send_web_sms(username=user_id)
        scramble_reveal("短信验证码已成功下发！请查收手机短信。", prefix="  ✅ ", duration=0.2, color=COLOR_GREEN)
    except LoginFailedError as e:
        print(f"  ❌ 发送验证码失败: {e}")
        sys.exit(1)

    # 步骤 2: 接收验证码
    sms_code = ""
    if sys.stdin.isatty():
        sms_code = input("\n请输入收到的 6 位短信验证码: ").strip()
    else:
        sms_code = os.getenv("HNCU_SMS_CODE", "").strip()

    if not sms_code:
        print("错误: 验证码不能为空")
        sys.exit(1)

    # 步骤 3: 提交 Web 登录
    scramble_reveal(
        "正在通过 Barrett RSA 加密提交登录并换取 CAS 票据...",
        prefix="\n  ⚡ ",
        duration=0.25,
        steps=8,
        color=COLOR_YELLOW,
    )
    try:
        auth_info = client.login_web(username=user_id, password=password, sms_code=sms_code)
        scramble_reveal("Web 门户登录成功！已成功打通 CAS 单点登录：", prefix="\n  ✅ ", duration=0.2, color=COLOR_GREEN)
        print()
        print_status_item("账号", auth_info.get("username"), icon="🆔")
        print_status_item("Ticket 票据", auth_info.get("ticket") or "已核销", icon="🎫")
        print_status_item("CASTGC", (auth_info.get("castgc") or "")[:20] + "...", icon="🔐")
        print_status_item("目标服务", auth_info.get("service"), icon="🌐")
        if auth_info.get("authorization"):
            print_status_item("门户 JWT Token", auth_info.get("authorization")[:25] + "...", icon="🔑")
        if auth_info.get("jsessionid"):
            print_status_item("JSESSIONID", auth_info.get("jsessionid"), icon="🍪")
        print()
    except LoginFailedError as e:
        print(f"\n  ❌ 登录失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
