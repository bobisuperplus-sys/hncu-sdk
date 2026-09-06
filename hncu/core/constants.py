"""
HNCU SDK 常量与配置定义模块
"""
from enum import Enum

# 基础 URL
BASE_URL_YDXY = "http://58.47.143.5"
BASE_URL_JWGLXT = "http://58.47.143.9:6038"
BASE_URL_RZPT = "https://rzpt.hncu.edu.cn"
BASE_URL_NEWS = "http://ydxy.hncu.edu.cn"

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
    """正方教务系统学期代码"""
    FIRST = "3"       # 第一学期 (秋季学期)
    SECOND = "12"     # 第二学期 (春季学期)
    ALL = ""          # 全学年
