#!/usr/bin/env python3
"""
测试单元：移动校园登录与正方教务 CAS SSO 单点登录
同时向外部测试单元导出 `get_authenticated_client()` 工具函数
"""
import sys
import os
import getpass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hncu import HncuClient, LoginFailedError, SsoConnectError
from terminal_fx import print_banner, print_status_item, scramble_reveal, COLOR_GREEN, COLOR_YELLOW, COLOR_CYAN

_CACHED_CLIENT = None


def get_authenticated_client(auto_sso: bool = True) -> HncuClient:
    """
    获取已成功认证并打通 SSO 的 HncuClient 实例
    优先读取环境变量 HNCU_USER / HNCU_PASS，否则提示输入
    """
    global _CACHED_CLIENT
    if _CACHED_CLIENT and _CACHED_CLIENT.profile:
        if auto_sso and not _CACHED_CLIENT.is_sso_connected:
            _CACHED_CLIENT.sso_connect()
        return _CACHED_CLIENT

    user_id = os.getenv("HNCU_USER")
    password = os.getenv("HNCU_PASS")

    if not user_id:
        if sys.stdin.isatty():
            user_id = input("请输入学号/工号: ").strip()
        else:
            raise ValueError("非交互环境下必须提供 HNCU_USER 环境变量")

    if not password:
        if sys.stdin.isatty():
            password = getpass.getpass("请输入密码: ").strip()
        else:
            raise ValueError("非交互环境下必须提供 HNCU_PASS 环境变量")

    client = HncuClient()
    scramble_reveal("正在建立双层加密认证通道并打通 CAS SSO...", prefix="  ⚡ ", duration=0.25, steps=8, color=COLOR_YELLOW)
    client.login(user_id=user_id, password=password, auto_sso=auto_sso)
    _CACHED_CLIENT = client
    return client


def main():
    print_banner("认证测试单元", "验证移动校园统一登录与正方教务单点登录")

    try:
        client = get_authenticated_client(auto_sso=True)
        profile = client.profile
        scramble_reveal("认证链路成功打通！已解密用户信息：", prefix="\n  ✅ ", duration=0.2, color=COLOR_GREEN)
        print()
        print_status_item("姓名", profile.user_name, icon="👤")
        print_status_item("学号", profile.user_id, icon="🆔")
        print_status_item("学院", profile.department, icon="🏛️")
        print_status_item("专业", profile.profession_name, icon="🎓")
        print_status_item("班级", f"{profile.class_name} (ID: {profile.class_id})", icon="🏫")
        print_status_item("年级", profile.grade, icon="📅")
        print_status_item("SSO 状态", "已激活 (JSESSIONID 就绪)", icon="🔑")
    except (LoginFailedError, SsoConnectError) as e:
        print(f"\n❌ 认证失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
