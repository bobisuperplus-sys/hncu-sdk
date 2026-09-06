"""
校园资讯与通知服务
"""
from typing import List
import requests

from ..core.constants import BASE_URL_NEWS, NEWS_CATEGORY_PARAMS, USER_AGENT_WEB, NewsCategory
from ..core.exceptions import NetworkError
from ..core.models import NewsItem
from ..core.session import HncuSession


class NewsService:
    """校园公开新闻与通知公告服务"""

    def __init__(self, hncu_session: HncuSession):
        self.hncu_session = hncu_session
        self.session = hncu_session.session

    def get_news(
        self,
        category: NewsCategory = NewsCategory.NOTICE,
        page: int = 1,
        page_size: int = 10,
    ) -> List[NewsItem]:
        """
        获取校园新闻、会议、通知公告列表（公开接口，无需登录）

        :param category: 新闻分类枚举 (NewsCategory.NOTICE 等)
        :param page: 当前页码 (从 1 开始)
        :param page_size: 每页数量
        """
        cat_info = NEWS_CATEGORY_PARAMS.get(category, NEWS_CATEGORY_PARAMS[NewsCategory.NOTICE])
        cid = cat_info["contentID"]
        my_cid = cat_info["myContentId"]

        url = (
            f"{BASE_URL_NEWS}/thirdpart_ydxy/boda/news/list"
            f"?contentID={cid}&userID=&myOwner={cid}&myContentId={my_cid}"
            f"&currentPage={page}&pageSize={page_size}"
        )

        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "User-Agent": USER_AGENT_WEB,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{BASE_URL_NEWS}/thirdpart_ydxy/boda/news/index",
        }

        try:
            resp = self.session.get(url, headers=headers, timeout=self.hncu_session.timeout)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            raise NetworkError(f"校园新闻获取失败: {e}") from e

        news_items = []
        rows = data.get("data", []) or data.get("rows", []) or data.get("list", [])
        for row in rows:
            news_items.append(
                NewsItem(
                    title=row.get("title", ""),
                    date=row.get("publishDate", row.get("date", "")),
                    url=row.get("url", ""),
                    category=cat_info["name"],
                    raw_data=row,
                )
            )
        return news_items
