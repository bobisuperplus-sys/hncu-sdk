"""
教学评价 (EvaluationService) 与深度自习室检索 (ClassroomService) 单元测试
"""
import unittest
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hncu import (
    HncuClient,
    EvaluationSummary,
    EvaluationCourseItem,
    EvaluationService,
    EmptyClassroomItem,
    Term,
)


class TestEvaluationModels(unittest.TestCase):
    """测试教学评价数据模型解析与属性"""

    def test_summary_parsing(self):
        raw = {
            "bcgs": 0,
            "tjgs": 12,
            "wpgs": 0,
            "pjtsxx": "恭喜！您本学期的所有课程均已评教完毕！",
        }
        summary = EvaluationSummary.from_dict(raw)
        self.assertEqual(summary.saved_count, 0)
        self.assertEqual(summary.submitted_count, 12)
        self.assertEqual(summary.unrated_count, 0)
        self.assertTrue(summary.is_all_completed)
        self.assertIn("恭喜", summary.prompt_message)

    def test_summary_not_completed(self):
        raw = {
            "bcgs": 1,
            "tjgs": 5,
            "wpgs": 2,
            "pjtsxx": "尚有课程未完成评价",
        }
        summary = EvaluationSummary.from_dict(raw)
        self.assertFalse(summary.is_all_completed)
        self.assertEqual(summary.unrated_count, 2)
        self.assertEqual(summary.saved_count, 1)

    def test_course_item_parsing(self):
        raw = {
            "jxb_id": "JXB123456",
            "kch_id": "KC789",
            "jgh_id": "T001",
            "jzgmc": "王老师",
            "kcmc": "软件工程导论",
            "jxbmc": "2024软工1班",
            "xsdm": "01",
            "xsmc": "理论",
            "tjzt": "1",
            "tjztmc": "提交",
            "pjmbmcb_id": "MB999",
            "sfcjlrjs": "1",
            "jgmc": "信息与电子工程学院",
            "bfzpf": "98.5",
        }
        item = EvaluationCourseItem.from_dict(raw)
        self.assertEqual(item.teaching_class_id, "JXB123456")
        self.assertEqual(item.course_name, "软件工程导论")
        self.assertEqual(item.teacher_name, "王老师")
        self.assertEqual(item.score, "98.5")
        self.assertTrue(item.is_submitted)
        self.assertFalse(item.is_unrated)
        self.assertFalse(item.is_saved)


class TestEvaluationPayloadParser(unittest.TestCase):
    """测试评价表单指标解析与请求体组装"""

    def setUp(self):
        self.client = HncuClient()
        self.service = self.client.evaluation

    def test_parse_evaluation_payload(self):
        course = EvaluationCourseItem.from_dict({
            "jxb_id": "JXB_DEMO_01",
            "kch_id": "KCH_DEMO_01",
            "jgh_id": "JGH_DEMO_01",
            "jzgmc": "李教授",
            "kcmc": "操作系统",
            "xsdm": "01",
            "tjzt": "-1",
            "pjmbmcb_id": "MB_ORIGINAL",
            "sfcjlrjs": "1",
        })

        mock_html = """
        <div class="panel-pjdx" data-pjmbmcb_id="MB_FROM_DOM" data-pjmbmc="本科教学评价" data-ztpjbl="100" data-xspfb_id="PFB_100">
          <table class="table table-xspj" data-pjzbxm_id="ZB_PARENT_01">
            <tbody>
              <tr class="tr-xspj" data-pjzbxm_id="ZB_CHILD_01" data-pfdjdmb_id="DJ_EXCELLENT_GUID" data-zsmbmcb_id="ZS_01">
                <td>教学态度</td>
              </tr>
              <tr class="tr-xspj" data-pjzbxm_id="ZB_CHILD_02" data-pfdjdmb_id="DJ_EXCELLENT_GUID" data-zsmbmcb_id="ZS_01">
                <td>教学内容</td>
              </tr>
            </tbody>
          </table>
        </div>
        """

        payload = self.service.parse_evaluation_payload(course, mock_html, comment="备课充分，讲课生动！")

        self.assertEqual(payload["jxb_id"], "JXB_DEMO_01")
        self.assertEqual(payload["kch_id"], "KCH_DEMO_01")
        self.assertEqual(payload["jgh_id"], "JGH_DEMO_01")
        self.assertEqual(payload["modelList[0].pjmbmcb_id"], "MB_FROM_DOM")
        self.assertEqual(payload["modelList[0].xspfb_id"], "PFB_100")
        self.assertEqual(payload["modelList[0].pjzt"], "1")
        # 验证指标与子指标
        self.assertEqual(payload["modelList[0].xspjList[0].pjzbxm_id"], "ZB_PARENT_01")
        self.assertEqual(payload["modelList[0].xspjList[0].childXspjList[0].pjzbxm_id"], "ZB_CHILD_01")
        self.assertEqual(payload["modelList[0].xspjList[0].childXspjList[0].pfdjdmb_id"], "DJ_EXCELLENT_GUID")
        self.assertEqual(payload["modelList[0].xspjList[0].childXspjList[1].pjzbxm_id"], "ZB_CHILD_02")


class TestStudyRoomService(unittest.TestCase):
    """测试空闲自习室与考研教室深度检索"""

    def setUp(self):
        self.client = HncuClient()

    def test_query_study_rooms_parameter_mapping(self):
        """测试时段预设转换与最低座位数过滤"""
        mock_rooms = [
            EmptyClassroomItem.from_dict({"cdid": "1", "cdmc": "1-101", "jxlmc": "一教", "zws": 40}),
            EmptyClassroomItem.from_dict({"cdid": "2", "cdmc": "1-102", "jxlmc": "一教", "zws": 120}),
            EmptyClassroomItem.from_dict({"cdid": "3", "cdmc": "1-103", "jxlmc": "一教", "zws": 80}),
        ]

        # Mock 底层 query 方法
        with patch.object(self.client.classrooms, "query", return_value=mock_rooms) as mock_query:
            results = self.client.query_study_rooms(
                period="all_day",
                building="1教",
                min_seats=60,
                week=2,
                day_of_week=3,
                year=2026,
            )

            # 验证 query 调用参数：all_day 映射为 (1, 10)，1教 映射为 "1"
            mock_query.assert_called_once_with(
                year=2026,
                term=Term.FIRST,
                week=2,
                day_of_week=3,
                section_start=1,
                section_end=10,
                building="1",
                room_name="",
                page=1,
                page_size=50,
            )

            # 验证 min_seats 过滤：40 座被剔除，保留 120 座与 80 座
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0].room_name, "1-102")
            self.assertEqual(results[1].room_name, "1-103")

    def test_query_study_rooms_period_presets(self):
        """测试各种自习时段预设映射"""
        presets = [
            ("morning", 1, 4),
            ("afternoon", 5, 8),
            ("evening", 9, 10),
            ("daytime", 1, 8),
        ]
        for period_name, expected_start, expected_end in presets:
            with patch.object(self.client.classrooms, "query", return_value=[]) as mock_query:
                self.client.query_study_rooms(period=period_name)
                args, kwargs = mock_query.call_args
                self.assertEqual(kwargs["section_start"], expected_start)
                self.assertEqual(kwargs["section_end"], expected_end)


if __name__ == "__main__":
    unittest.main()
