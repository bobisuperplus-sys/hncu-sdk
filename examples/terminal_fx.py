"""
终端炫酷动态字符解码与 ASCII Art Banner 特效模块 (Terminal ScrambleText FX)
包含：
1. 终端大文字 ASCII Art Banner (HNCU SDK) 与霓虹青蓝渐变渲染
2. 灵感来源于 Anime.js scrambleText 特效的逐字乱码闪烁解码揭示
3. 优雅的现代化 CLI 圆角信息卡片排版
4. 支持 ANSI 真彩/高亮，非交互终端自动平滑降级
"""
import sys
import time
import random
from typing import Optional

# ANSI 终端颜色代码
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_DIM = "\033[2m"
COLOR_GREEN = "\033[92m"
COLOR_CYAN = "\033[96m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE = "\033[94m"
COLOR_MAGENTA = "\033[95m"
COLOR_WHITE = "\033[97m"

# 霓虹青蓝渐变色阶 (Neon Cyan -> Deep Sky Blue)
GRADIENT_CYAN_BLUE = [
    "\033[38;5;51m",   # 亮霓虹青
    "\033[38;5;45m",   # 蔚蓝
    "\033[38;5;39m",   # 深天蓝
    "\033[38;5;33m",   # 道奇蓝
    "\033[38;5;27m",   # 纯蓝
]

# HNCU SDK 大字 ASCII Art (Slant 现代动感风格)
HNCU_SDK_ASCII = [
    r"    __  ___   ______  __  __      _____ ____  __ __",
    r"   / / / / | / / ____/ / / /     / ___// __ \/ //_/",
    r"  / /_/ /  |/ / /   / / / /      \__ \/ / / / ,<   ",
    r" / __  / /|  / /___/ /_/ /      ___/ / /_/ / /| |  ",
    r"/_/ /_/_/ |_/\____/\____/      /____/_____/_/ |_|  ",
]

# 乱码字符池 (混合几何符号、ASCII控制字符、数字与黑客代码)
SCRAMBLE_CHARS = "!<>-_\\/[]{}—=+*^?#_010123456789ABCDEF$#@%&"


def is_interactive() -> bool:
    """判断是否处于交互式终端环境中"""
    return sys.stdout.isatty()


def scramble_reveal(
    target_text: str,
    prefix: str = "",
    duration: float = 0.3,
    steps: int = 8,
    color: str = COLOR_CYAN,
    final_color: str = COLOR_WHITE,
    end_newline: bool = True,
):
    """
    终端字符乱码渐变揭示动画 (Anime.js ScrambleText Effect)
    
    :param target_text: 最终要展示的真实文本
    :param prefix: 行首前缀 (如 "   👤 姓名: ")，不参与乱码
    :param duration: 动画持续总时长 (秒)
    :param steps: 动画刷新帧数
    :param color: 乱码流动时的动态颜色
    :param final_color: 最终定格字符的颜色
    :param end_newline: 动画结束后是否换行
    """
    if not is_interactive():
        # 非交互终端 (如管道重定向、CI/CD) 直接打印最终文本
        print(f"{prefix}{target_text}")
        return

    text_len = len(target_text)
    if text_len == 0:
        if end_newline:
            print()
        return

    sleep_per_frame = max(0.01, duration / steps)

    for step in range(steps + 1):
        # 计算当前已解密固定的字符索引范围
        reveal_ratio = step / steps
        revealed_count = int(text_len * reveal_ratio)

        revealed_part = target_text[:revealed_count]
        scrambled_chars = []
        for i in range(revealed_count, text_len):
            char = target_text[i]
            if char.isspace():
                scrambled_chars.append(char)
            else:
                scrambled_chars.append(random.choice(SCRAMBLE_CHARS))
        scrambled_part = "".join(scrambled_chars)

        # 终端回车刷新当前行
        output = (
            f"\r{prefix}"
            f"{final_color}{COLOR_BOLD}{revealed_part}{COLOR_RESET}"
            f"{color}{scrambled_part}{COLOR_RESET}"
        )
        sys.stdout.write(output)
        sys.stdout.flush()
        if step < steps:
            time.sleep(sleep_per_frame)

    # 最终完整字符呈现
    sys.stdout.write(f"\r{prefix}{final_color}{target_text}{COLOR_RESET}")
    if end_newline:
        sys.stdout.write("\n")
    sys.stdout.flush()


def print_banner(title: str, subtitle: Optional[str] = None):
    """
    打印带 ASCII Art 大文字、霓虹渐变色彩与 ScrambleText 动效的主测试横幅
    """
    card_cyan = "\033[38;5;44m"
    line_width = 62

    print()
    # 1. 打印 HNCU SDK 大字 ASCII Art (附带霓虹渐变与平滑展开)
    for i, art_line in enumerate(HNCU_SDK_ASCII):
        c = GRADIENT_CYAN_BLUE[i % len(GRADIENT_CYAN_BLUE)]
        print(f"  {COLOR_BOLD}{c}{art_line}{COLOR_RESET}")
        if is_interactive():
            time.sleep(0.015)

    # 2. 打印副标与版本标识
    print(f"  {COLOR_DIM}:: Hunan City University Python SDK ::{COLOR_RESET}        \033[38;5;214m(v1.0.0){COLOR_RESET}\n")

    # 3. 打印现代化测试模块圆角信息卡片
    top_line = f"  {card_cyan}╭{'─' * line_width}{COLOR_RESET}"
    bot_line = f"  {card_cyan}╰{'─' * line_width}{COLOR_RESET}"

    print(top_line)
    scramble_reveal(
        f"【测试单元】{title}",
        prefix=f"  {card_cyan}│{COLOR_RESET}  ",
        duration=0.3,
        steps=8,
        color=COLOR_MAGENTA,
        final_color=f"{COLOR_BOLD}{COLOR_GREEN}",
    )
    if subtitle:
        scramble_reveal(
            f">> {subtitle}",
            prefix=f"  {card_cyan}│{COLOR_RESET}   ",
            duration=0.22,
            steps=6,
            color=COLOR_DIM,
            final_color=COLOR_YELLOW,
        )
    print(bot_line)
    print()


def print_status_item(label: str, value: str, icon: str = "•"):
    """
    格式化打印单项数据属性，伴随字符揭示
    """
    prefix = f"  {COLOR_CYAN}{icon}{COLOR_RESET} {COLOR_BOLD}{label}:{COLOR_RESET} "
    scramble_reveal(
        str(value),
        prefix=prefix,
        duration=0.18,
        steps=6,
        color=COLOR_YELLOW,
        final_color=COLOR_WHITE,
    )
