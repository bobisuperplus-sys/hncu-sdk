"""
智慧门户与一卡通 Service 单元测试
"""
import unittest
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hncu import HncuClient, PortalService, PortalProfile, ECardInfo
from hncu.core.exceptions import SessionExpiredError, BusinessLogicError


class TestPortalService(unittest.TestCase):

    def setUp(self):
        self.client = HncuClient()

    def test_unauthenticated_raises_error(self):
        """未设置 token 时直接调用应抛出 SessionExpiredError"""
        with self.assertRaises(SessionExpiredError):
            self.client.portal.get_ecard_info()

    def test_ecard_model_parsing(self):
        """测试一卡通模型解析"""
        raw_data = {"KAYE": 12.5, "SFGS": "正常", "SFDJ": "正常"}
        info = ECardInfo.from_dict(raw_data)
        self.assertEqual(info.balance, 12.5)
        self.assertEqual(info.loss_status, "正常")
        self.assertEqual(info.freeze_status, "正常")

    def test_portal_profile_parsing_and_masking(self):
        """测试门户个人信息模型解析与脱敏"""
        raw_data = {
            "SCREENNAME": "2021000000",
            "USERNAME": "张三",
            "ORGNAME": "信息与电子工程学院",
            "PERSONCARD": "430523200001011234",
            "XB": "男",
            "DLIP": "127.0.0.1",
            "CJSJ": "2026-09-12 12:00:00",
            "ZP": "base64photo"
        }
        profile = PortalProfile.from_dict(raw_data)
        self.assertEqual(profile.user_id, "2021000000")
        self.assertEqual(profile.user_name, "张三")
        self.assertEqual(profile.department, "信息与电子工程学院")
        self.assertEqual(profile.gender, "男")
        self.assertEqual(profile.id_card_masked, "430523********1234")


if __name__ == "__main__":
    unittest.main()
