#!/usr/bin/env python3
"""
测试单元：AES-128-ECB 加解密闭环与控制字符清洗 (离线测试)
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hncu import HncuCrypto
from terminal_fx import print_banner, print_status_item, scramble_reveal, COLOR_GREEN, COLOR_YELLOW, COLOR_MAGENTA


def main():
    print_banner("底层加密测试单元", "AES-128-ECB PKCS7 加解密与畸变字符清洗")

    crypto = HncuCrypto()

    # 1. 普通明文加解密
    raw_text = '{"userName":"2021000000","action":"queryGrade"}'
    scramble_reveal(f"原始明文字符串: {raw_text}", prefix="  [1/3] ", duration=0.2, color=COLOR_YELLOW)
    
    encrypted_b64 = crypto.encrypt(raw_text)
    scramble_reveal(f"密文 (Base64): {encrypted_b64}", prefix="        ", duration=0.25, color=COLOR_MAGENTA)
    
    decrypted_text = crypto.decrypt(encrypted_b64)
    scramble_reveal(f"解密验证还原: {decrypted_text}", prefix="        ", duration=0.2, color=COLOR_GREEN)
    assert raw_text == decrypted_text, "加解密还原不一致！"
    print_status_item("基础加解密断言", "通过 (100% 字节对齐)", icon="✅")

    # 2. 模拟教务端尾部控制字符 (\\u0004 等)
    print()
    polluted_text = '{"code":"0","data":"ok"}\x04\x04\x04\x04'
    scramble_reveal("测试包含尾部控制字符 (\\u0004) 的数据包清洗:", prefix="  [2/3] ", duration=0.2, color=COLOR_YELLOW)
    parsed_obj = crypto.extract_and_parse_json(polluted_text)
    print_status_item("脏字符剥离解析", f"成功解析为字典 -> {parsed_obj}", icon="✅")
    assert parsed_obj == {"code": "0", "data": "ok"}

    # 3. 模拟数组数据清洗
    print()
    array_text = '\x00\x00[{"id": 1, "name": "高等数学"}, {"id": 2, "name": "大学物理"}]\x04'
    scramble_reveal("测试首尾均含控制字符的数组成员清洗:", prefix="  [3/3] ", duration=0.2, color=COLOR_YELLOW)
    parsed_arr = crypto.extract_and_parse_json(array_text, expect_array=True)
    print_status_item("数组安全提取", f"成功解析为数组 (长度: {len(parsed_arr)})", icon="✅")
    assert len(parsed_arr) == 2

    print()
    scramble_reveal("🎉 底层加解密引擎与数据清洗全部测试通过！", prefix="  ", duration=0.3, color=COLOR_GREEN)


if __name__ == "__main__":
    main()
