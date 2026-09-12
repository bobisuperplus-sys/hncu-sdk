"""
HNCU SDK 常量与配置定义模块
"""
from enum import Enum
from typing import Any

# 基础 URL
BASE_URL_YDXY = "http://58.47.143.5"
BASE_URL_JWGLXT = "http://58.47.143.9:6038"
BASE_URL_RZPT = "https://rzpt.hncu.edu.cn"
BASE_URL_NEWS = "http://ydxy.hncu.edu.cn"
BASE_URL_YWPT = "http://ywpt.hncu.edu.cn:4106"

# 默认请求凭据（移动客户端公共标识）
DEFAULT_ACCESS_TOKEN_HEADER = (
    "E+v0kWYgOCP1PqrsGKl9DGaQqTDs+XNwMHhil3Cgy9v1eGuXI53wb6LoQLiRWcXFHQndRGj6kubVrNH24ws031uwMeAtXqKcGEOHaVCFQ3Q="
)
DEFAULT_UNIQUE_CODE_HEADER = "71dde257-bb10-4549-bc2f-9f9655cae34d"

# User-Agent
USER_AGENT_APP = "Dalvik/2.1.0 (Linux; U; Android 12; 2206122SC Build/9895436.0)"
USER_AGENT_WEB = (
    "Mozilla/5.0 (Linux; Android 12; 2206122SC Build/V417IR; wv) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/95.0.4638.74 Safari/537.36;lyydxy"
)

# 默认 AES 密钥（Base64 字符串，对应 16 字节密钥）
DEFAULT_AES_KEY_B64 = "asO+FBJxb33SWsBCZu+MEg=="

# 统一身份认证 Web 端 (lyuapServer) RSA 加密配置
WEB_AUTH_TAG = "lyasp"
WEB_RSA_PUBLIC_EXPONENT = "010001"
WEB_RSA_MODULUS = (
    "00b5eeb166e069920e80bebd1fea4829d3d1f3216f2aabe79b6c47a3c18dcee5fd22c2e7ac519cab59198ece036dcf28"
    "9ea8201e2a0b9ded307f8fb704136eaeb670286f5ad44e691005ba9ea5af04ada5367cd724b5a26fdb5120cc95b64316"
    "04bd219c6b7d83a6f8f24b43918ea988a76f93c333aa5a20991493d4eb1117e7b1"
)
WEB_RSA_PRIVATE_EXPONENT = (
    "413798867d69babed22e0dd3d4031c635f3e9dbca0fa50a32974a0e230787b7f7ba78caefbee828a051c690357a8cc31"
    "dba8efc738b4db22e887571ef1ec5a5a55b6d866f6a67527f6a7d78a127c9f687008bb540228b50aa2d1ca5a4ff71107"
    "234f936b611ac46432a26da9c302eaa7180820df70593353b3f8c0247fe97a45"
)



class NewsCategory(Enum):
    """校园新闻与通知分类枚举"""
    NOTICE = 0        # 通知公告
    MEETING = 1       # 会议安排
    ACADEMIC = 2      # 教务通知
    STUDENT = 3       # 学工通知
    NEWS = 4          # 城院新闻
    MEDIA = 5         # 媒体城院


# 新闻分类参数映射 (contentID, myContentId)
NEWS_CATEGORY_PARAMS = {
    NewsCategory.NOTICE: {"contentID": "1545760554", "myContentId": "215813", "name": "通知公告"},
    NewsCategory.MEETING: {"contentID": "1545760554", "myContentId": "215814", "name": "会议安排"},
    NewsCategory.ACADEMIC: {"contentID": "1271583702", "myContentId": "126004", "name": "教务通知"},
    NewsCategory.STUDENT: {"contentID": "991888080",  "myContentId": "126548", "name": "学工通知"},
    NewsCategory.NEWS: {"contentID": "1545760554", "myContentId": "215812", "name": "城院新闻"},
    NewsCategory.MEDIA: {"contentID": "1545760554", "myContentId": "215815", "name": "媒体城院"},
}


class Term(Enum):
    """正方教务系统学期代码枚举与智能归一化"""
    FIRST = "3"       # 第 1 学期 (上学期 / 秋季学期)
    SECOND = "12"     # 第 2 学期 (下学期 / 春季学期)
    THIRD = "16"      # 第 3 学期 (暑假实习 / 短学期)
    ALL = ""          # 全学年全部学期

    @classmethod
    def normalize(cls, val: Any) -> str:
        """
        智能归一化学期输入参数，转化为正方教务系统底层的真实 xqm 代码。
        支持入参：
        - 第 1 学期: Term.FIRST, 1, "1", 3, "3", "上", "秋", "first" -> "3"
        - 第 2 学期: Term.SECOND, 2, "2", 12, "12", "下", "春", "second" -> "12"
        - 第 3 学期: Term.THIRD, 16, "16", "短", "暑", "实习", "third" -> "16"
        - 全部学期: Term.ALL, None, "", 0, "0", "all", "全部" -> ""
        """
        if val is None:
            return ""
        if isinstance(val, Term):
            return val.value
        s = str(val).strip().lower()
        if s in ("", "0", "all", "全部"):
            return ""
        if s in ("1", "first", "上", "秋"):
            return cls.FIRST.value
        if s in ("2", "12", "second", "下", "春"):
            return cls.SECOND.value
        if s in ("16", "third", "短", "暑", "实习", "暑假实习"):
            return cls.THIRD.value
        if s == "3":
            # 正方教务系统原生代码 3 代表第 1 学期 (上学期)
            return cls.FIRST.value
        return s

    @classmethod
    def get_display_name(cls, val: Any) -> str:
        """
        获取学期的人性化展示名称 (如: 第 1 学期, 第 2 学期, 第 3 学期 (暑假实习))
        """
        xqm = cls.normalize(val)
        if xqm == cls.FIRST.value:
            return "第 1 学期"
        elif xqm == cls.SECOND.value:
            return "第 2 学期"
        elif xqm == cls.THIRD.value:
            return "第 3 学期 (暑假实习)"
        elif not xqm:
            return "全部学期"
        return f"学期({xqm})"

