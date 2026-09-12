"""
智慧校园综合服务门户与一卡通数据模型
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class ECardInfo:
    """一卡通基本信息"""
    balance: float              # 卡余额（元） (KAYE)
    loss_status: str            # 挂失状态 (SFGS, 例如 "正常", "已挂失")
    freeze_status: str          # 冻结状态 (SFDJ, 例如 "正常", "已冻结")
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ECardInfo":
        try:
            bal = float(d.get("KAYE", 0.0) or 0.0)
        except (ValueError, TypeError):
            bal = 0.0

        return cls(
            balance=bal,
            loss_status=str(d.get("SFGS", "正常")),
            freeze_status=str(d.get("SFDJ", "正常")),
            raw_data=d
        )


@dataclass
class PortalProfile:
    """智慧门户用户个人详细档案"""
    user_id: str                # 学号 / 工号 (SCREENNAME)
    user_name: str              # 真实姓名 (USERNAME)
    department: str             # 所属部门 / 学院 (ORGNAME)
    id_card: str                # 身份证号 (PERSONCARD)
    gender: str                 # 性别 (XB: 男 / 女)
    login_ip: str               # 最近登录 IP (DLIP)
    login_time: str             # 最近登录时间 (CJSJ)
    photo_base64: str           # 一寸高清证件照片 base64 编码 (ZP)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def id_card_masked(self) -> str:
        """脱敏后的身份证号 (如: 430523********7656)"""
        if len(self.id_card) >= 14:
            return f"{self.id_card[:6]}{'*' * (len(self.id_card) - 10)}{self.id_card[-4:]}"
        return self.id_card

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PortalProfile":
        return cls(
            user_id=str(d.get("SCREENNAME", "")),
            user_name=str(d.get("USERNAME", "")),
            department=str(d.get("ORGNAME", "")),
            id_card=str(d.get("PERSONCARD", "")),
            gender=str(d.get("XB", "")),
            login_ip=str(d.get("DLIP", "")),
            login_time=str(d.get("CJSJ", "")),
            photo_base64=str(d.get("ZP", "")),
            raw_data=d
        )
