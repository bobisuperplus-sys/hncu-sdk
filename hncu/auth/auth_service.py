"""
HNCU 认证与单点登录服务模块
负责移动校园端身份认证与正方教务系统 CAS SSO 会话打通
"""
import json
import time
from typing import Optional, Dict, Any
from urllib.parse import quote
import requests

from ..core.constants import (
    BASE_URL_JWGLXT,
    BASE_URL_RZPT,
    BASE_URL_YDXY,
    BASE_URL_YWPT,
    DEFAULT_ACCESS_TOKEN_HEADER,
    USER_AGENT_WEB,
    WEB_AUTH_TAG,
)
from ..core.crypto import HncuCrypto
from ..core.exceptions import (
    CryptoError,
    HncuException,
    LoginFailedError,
    NetworkError,
    SessionExpiredError,
    SsoConnectError,
)
from ..core.models import StudentProfile
from ..core.session import HncuSession


class AuthService:
    """
    统一身份认证与单点登录服务
    """

    def __init__(self, hncu_session: HncuSession, crypto: HncuCrypto):
        self.hncu_session = hncu_session
        self.session = hncu_session.session
        self.crypto = crypto
        self.profile: Optional[StudentProfile] = None
        self.is_sso_connected: bool = False

    def login(
        self,
        user_id: str,
        password: str,
        auto_sso: bool = True,
    ) -> StudentProfile:
        """
        登录移动校园并（可选）自动打通正方教务系统单点登录

        :param user_id: 学号/工号
        :param password: 密码
        :param auto_sso: 是否自动打通正方教务系统免密会话 (默认 True)
        :return: StudentProfile 用户身份信息对象
        """
        if not user_id or not password:
            raise LoginFailedError("用户名或密码不能为空")

        payload = {"userId": user_id, "passw": password, "deviceType": "1"}
        try:
            encrypted_data = self.crypto.encrypt(json.dumps(payload, separators=(",", ":")))
        except CryptoError as e:
            raise LoginFailedError(f"加密登录凭据异常: {e}") from e

        url = f"{BASE_URL_YDXY}/mobileapi_ydxy/open/auth/login"
        headers = {
            "Access-Token": DEFAULT_ACCESS_TOKEN_HEADER,
            "Content-Type": "text/plain",
            "Host": "58.47.143.5",
        }

        try:
            resp = self.session.post(
                url,
                data=encrypted_data.encode("utf-8"),
                headers=headers,
                timeout=self.hncu_session.timeout,
            )
            resp.raise_for_status()
            res_json = resp.json()
        except requests.RequestException as e:
            raise NetworkError(f"登录网络请求失败: {e}") from e
        except json.JSONDecodeError as e:
            raise LoginFailedError(f"服务端返回了非预期格式: {resp.text[:200]}") from e

        code = str(res_json.get("code", "-1"))
        if code != "0":
            msg = res_json.get("msg", "登录失败")
            raise LoginFailedError(msg, code=int(code) if code.isdigit() else -1)

        # 解密业务数据包
        encrypted_resp_data = res_json.get("data", "")
        if not encrypted_resp_data:
            raise LoginFailedError("服务端返回数据包为空")

        try:
            decrypted_text = self.crypto.decrypt(encrypted_resp_data)
            user_data = self.crypto.extract_and_parse_json(decrypted_text, expect_array=False)
        except CryptoError as e:
            raise LoginFailedError(f"解析登录后用户信息失败: {e}") from e

        self.profile = StudentProfile.from_dict(user_data)

        # 构造带有时戳的动态 Access-Token 请求头
        access_token_dict = {
            "clientVersion": "3.2.0",
            "sessionKey": self.profile.session_key,
            "userId": self.profile.user_id,
            "userType": "1",
            "xxdm": "HNCU",
            "currentTime": str(int(time.time() * 1000)),
        }
        try:
            new_token = self.crypto.encrypt(
                json.dumps(access_token_dict, separators=(",", ":"))
            )
            self.session.headers["Access-Token"] = new_token
        except CryptoError as e:
            raise LoginFailedError(f"生成 Access-Token 失败: {e}") from e

        if auto_sso:
            self.sso_connect()

        return self.profile

    def sso_connect(self) -> bool:
        """
        通过移动校园会话自动打通正方教务系统免密单点登录 (CAS SSO)
        """
        if not self.profile:
            raise SessionExpiredError("尚未登录移动校园，无法建立教务系统单点登录")

        try:
            # 步骤 1: 访问 springboard 触发重定向链，自动捕获 CASTGC 与 route
            springboard_url = (
                f"{BASE_URL_YDXY}/mobileapi_ydxy/api/lapp/springboard?yyid=common_wechat_exam"
            )
            headers_step1 = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "User-Agent": USER_AGENT_WEB,
            }
            self.session.get(
                springboard_url,
                headers=headers_step1,
                allow_redirects=True,
                timeout=self.hncu_session.timeout,
            )

            # 安全从 Cookie 中寻找 CASTGC
            castgc = self.hncu_session.get_cookie("CASTGC", domain_pattern="rzpt.hncu.edu.cn")
            if not castgc:
                raise SsoConnectError("未能从认证平台获取到 CASTGC 凭据")

            # 步骤 2: 用 CASTGC 兑换 ST Ticket 票据
            ticket_url = f"{BASE_URL_RZPT}/lyuapServer/v1/tickets/{castgc}"
            service_target = (
                "http://58.47.143.9:6038/sso/lyiotlogin"
                "?url=cjcx%2Fcjcx_cxDgXscj.html%3Fgnmkdm%3DN305005%26layout%3Ddefault"
            )
            headers_web = {
                "User-Agent": USER_AGENT_WEB,
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
            }
            resp_ticket = self.session.post(
                ticket_url,
                data={"service": service_target},
                headers=headers_web,
                timeout=self.hncu_session.timeout,
                verify=self.hncu_session.verify_ssl,
            )
            ticket = resp_ticket.text.strip()
            if not ticket or "<html" in ticket.lower():
                raise SsoConnectError(f"获取票据(Ticket)失败: {resp_ticket.text[:100]}")

            # 步骤 3: 用 Ticket 兑换教务系统 JSESSIONID
            login_with_ticket_url = f"{service_target}&ticket={ticket}"
            self.session.get(
                login_with_ticket_url,
                headers=headers_web,
                allow_redirects=True,
                timeout=self.hncu_session.timeout,
            )

            # 检查是否成功获得了针对教务系统的 JSESSIONID
            jsessionid = self.hncu_session.get_cookie("JSESSIONID", domain_pattern="58.47.143.9")
            self.is_sso_connected = bool(jsessionid)
            return self.is_sso_connected

        except requests.RequestException as e:
            raise NetworkError(f"单点登录连接超时或网络异常: {e}") from e

    def ensure_app_login(self):
        """确保已登录移动校园"""
        if not self.profile:
            raise SessionExpiredError("尚未登录，请先调用 client.login(user_id, password)")

    def ensure_sso(self):
        """确保正方教务 SSO 已建立"""
        self.ensure_app_login()
        if not self.is_sso_connected:
            self.sso_connect()

    def send_web_sms_code(self, username: str) -> bool:
        """
        发送统一身份认证平台 Web 端登录短信验证码

        :param username: 学号 / 工号 (例如: "2021000000")
        :return: bool 是否成功触发短信下发
        """
        if not username:
            raise LoginFailedError("用户名/学号不能为空")

        ts = str(int(time.time() * 1000))
        sign_token = self.crypto.rsa_encrypt(f"{WEB_AUTH_TAG}{ts}")

        url = f"{BASE_URL_RZPT}/lyuapServer/login/mobile/generateCode"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=utf-8",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": USER_AGENT_WEB,
            "token": sign_token,
            "loginUserToken": sign_token,
        }
        payload = {"username": username, "module": "2"}

        try:
            resp = self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.hncu_session.timeout,
                verify=self.hncu_session.verify_ssl,
            )
            resp.raise_for_status()
            res_json = resp.json()
        except requests.RequestException as e:
            raise NetworkError(f"发送验证码网络请求失败: {e}") from e
        except json.JSONDecodeError as e:
            raise LoginFailedError(f"服务端返回了非预期响应: {resp.text[:200]}") from e

        meta = res_json.get("meta", {})
        if not meta.get("success", False):
            msg = meta.get("message", "发送短信验证码失败")
            raise LoginFailedError(msg, code=meta.get("statusCode", -1))

        return True

    def login_web(
        self,
        username: str,
        password: str,
        sms_code: str,
        service: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        通过 Web 统一身份认证平台 (CAS SSO) 使用账号、密码与短信验证码登录

        :param username: 学号 / 工号
        :param password: 明文密码
        :param sms_code: 手机收到的 6 位短信验证码
        :param service: 授权目标服务 URL (默认指向服务门户: http://ywpt.hncu.edu.cn:4106/shiro-cas)
        :return: 认证凭据字典 (包含 ticket, castgc, authorization, jsessionid 等)
        """
        if not username or not password:
            raise LoginFailedError("用户名或密码不能为空")
        if not sms_code:
            raise LoginFailedError("短信验证码不能为空")

        target_service = service or f"{BASE_URL_YWPT}/shiro-cas"
        encrypted_pwd = self.crypto.rsa_encrypt(password)

        ticket_url = f"{BASE_URL_RZPT}/lyuapServer/v1/tickets"
        headers = {
            "User-Agent": USER_AGENT_WEB,
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
        }
        form_data = {
            "username": username,
            "password": encrypted_pwd,
            "service": target_service,
            "loginType": "",
            "smsCode": sms_code.strip(),
        }

        try:
            resp = self.session.post(
                ticket_url,
                data=form_data,
                headers=headers,
                timeout=self.hncu_session.timeout,
                verify=self.hncu_session.verify_ssl,
            )
            resp.raise_for_status()
            res_json = resp.json()
        except requests.RequestException as e:
            raise NetworkError(f"Web 登录认证请求失败: {e}") from e
        except json.JSONDecodeError as e:
            raise LoginFailedError(f"服务端返回了非预期响应: {resp.text[:200]}") from e

        # 检测业务层返回错误
        data_obj = res_json.get("data")
        if isinstance(data_obj, dict) and data_obj.get("code"):
            err_code = str(data_obj.get("code"))
            err_map = {
                "FALSE": "账号或密码错误，请检查",
                "CODEFALSE": "短信验证码错误或已过期",
                "PASSERROR": "密码错误",
                "USERLOCK": "账号已被锁定，请稍后再试",
                "NOUSER": "用户不存在",
            }
            msg = err_map.get(err_code, f"认证失败: {err_code}")
            raise LoginFailedError(msg)

        # 提取票据 (ticket 或 tgt)
        ticket = res_json.get("ticket")
        if not ticket and isinstance(data_obj, dict):
            ticket = data_obj.get("ticket")
        if not ticket:
            ticket = res_json.get("tgt")

        castgc = self.hncu_session.get_cookie("CASTGC", domain_pattern="rzpt.hncu.edu.cn")

        # 携带 Ticket 访问 target_service 完成 CAS 验证与会话建立
        final_url = None
        if ticket:
            sep = "&" if ("?" in target_service) else "?"
            validate_url = f"{target_service}{sep}ticket={ticket}"
            try:
                resp_val = self.session.get(
                    validate_url,
                    headers={"User-Agent": USER_AGENT_WEB},
                    allow_redirects=True,
                    timeout=self.hncu_session.timeout,
                    verify=self.hncu_session.verify_ssl,
                )
                final_url = resp_val.url
            except requests.RequestException:
                pass

        auth_jwt = self.hncu_session.get_cookie("Authorization", domain_pattern="ywpt.hncu.edu.cn")
        jsessionid = self.hncu_session.get_cookie("JSESSIONID")

        result = {
            "username": username,
            "ticket": ticket,
            "castgc": castgc,
            "service": target_service,
            "authorization": auth_jwt,
            "jsessionid": jsessionid,
            "final_url": final_url,
        }
        self.web_auth_data = result
        return result

