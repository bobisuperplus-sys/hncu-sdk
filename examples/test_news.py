#!/usr/bin/env python3
"""
测试单元：校园公开新闻资讯与教务通知公告 (免登录)
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hncu import HncuClient, NewsCategory
from terminal_fx import print_banner, scramble_reveal, COLOR_GREEN, COLOR_CYAN, COLOR_YELLOW, COLOR_BOLD, COLOR_RESET


def main():
    print_banner("校园资讯测试单元", "公开接口 - 6 大分类官方新闻与教务通知 (免登录)")

    client = HncuClient()

    scramble_reveal("正在请求校园教务通知最新列表 (Page 1, 5 条)...", prefix="  📢 ", duration=0.25, color=COLOR_YELLOW)
    news = client.get_news(category=NewsCategory.ACADEMIC, page=1, page_size=5)

    scramble_reveal(f"获取成功！抓取到 {len(news)} 条最新官方通知：", prefix="  ✅ ", duration=0.2, color=COLOR_GREEN)
    print()

    for idx, item in enumerate(news, 1):
        prefix_tag = f"  [{item.date}] "
        scramble_reveal(item.title, prefix=f"  {COLOR_BOLD}{COLOR_CYAN}[{item.date}]{COLOR_RESET} ", duration=0.15, steps=5, color=COLOR_YELLOW)
        print(f"      {COLOR_CYAN}🔗 {item.url}{COLOR_RESET}")

    print()
    scramble_reveal("🎉 校园资讯单元测试执行完毕！", prefix="  ", duration=0.2, color=COLOR_GREEN)


if __name__ == "__main__":
    main()
