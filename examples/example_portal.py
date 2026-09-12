"""
HNCU SDK 示例：智慧门户与一卡通数据查询 (v0.4.0)

本示例展示如何通过 Web 端统一身份认证获取凭证，或直接使用已有令牌查询个人综合档案与一卡通实时余额。
"""
from hncu import HncuClient


def main():
    client = HncuClient()

    # 方式 1: 直接使用已有 Web 令牌 (适用于从浏览器 Cookie / Storage 拿到的凭据)
    token = "YOUR_AUTHORIZATION_JWT_TOKEN"
    client.portal.set_token(token)

    # 方式 2: 通过 Web 验证码自动登录获取
    # client.auth.send_web_sms_code(username="2021000000")
    # code = input("请输入收到的短信验证码: ")
    # client.auth.login_web(username="2021000000", password="YOUR_PASSWORD", sms_code=code)

    try:
        # 1. 查询一卡通基础信息
        ecard = client.portal.get_ecard_info()
        print("=== 一卡通信息 ===")
        print(f"卡余额: {ecard.balance} 元")
        print(f"挂失状态: {ecard.loss_status}")
        print(f"冻结状态: {ecard.freeze_status}")

        # 2. 查询门户个人详细综合档案
        profile = client.portal.get_profile()
        print("\n=== 个人综合档案 ===")
        print(f"姓名: {profile.user_name}")
        print(f"学号: {profile.user_id}")
        print(f"所属学院: {profile.department}")
        print(f"身份证号: {profile.id_card_masked}")
        print(f"性别: {profile.gender}")
        print(f"最近登录IP: {profile.login_ip}")
        print(f"最近登录时间: {profile.login_time}")
        print(f"是否包含一寸高清照片: {bool(profile.photo_base64)}")

    except Exception as e:
        print(f"查询失败: {e}")


if __name__ == "__main__":
    main()
