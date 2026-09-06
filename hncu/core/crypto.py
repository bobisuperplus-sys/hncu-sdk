"""
HNCU 加密与数据清洗模块
支持 AES-128-ECB PKCS7 加解密及畸变字符剥离
"""
import base64
import json
from typing import Any, Union
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from .constants import DEFAULT_AES_KEY_B64
from .exceptions import CryptoError


class HncuCrypto:
    """
    湖南城市学院专用 AES-128-ECB 加解密处理器
    """

    def __init__(self, base64_key: str = DEFAULT_AES_KEY_B64):
        try:
            self.key = base64.b64decode(base64_key)
            if len(self.key) != 16:
                raise ValueError(f"AES-128 密钥长度必须为 16 字节，当前为 {len(self.key)} 字节")
        except Exception as e:
            raise CryptoError(f"解析 Base64 密钥失败: {e}") from e

    def encrypt(self, raw_data: Union[str, bytes]) -> str:
        """
        使用 AES-128-ECB 加密原始数据，返回 Base64 字符串
        """
        try:
            if isinstance(raw_data, str):
                data_bytes = raw_data.encode("utf-8")
            else:
                data_bytes = raw_data

            cipher = AES.new(self.key, AES.MODE_ECB)
            padded = pad(data_bytes, AES.block_size, style="pkcs7")
            encrypted = cipher.encrypt(padded)
            return base64.b64encode(encrypted).decode("utf-8")
        except Exception as e:
            raise CryptoError(f"加密失败: {e}") from e

    def decrypt(self, encrypted_b64: str) -> str:
        """
        解密 Base64 字符串，返回 UTF-8 明文字符串
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_b64.strip())
            cipher = AES.new(self.key, AES.MODE_ECB)
            decrypted = cipher.decrypt(encrypted_bytes)
            try:
                unpadded = unpad(decrypted, AES.block_size, style="pkcs7")
            except ValueError:
                # 兼容服务端未规范 PKCS7 填充或末尾被截断的情况
                unpadded = decrypted.rstrip(b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10")

            return unpadded.decode("utf-8", errors="ignore")
        except Exception as e:
            raise CryptoError(f"解密失败: {e}") from e

    @staticmethod
    def extract_and_parse_json(text: str, expect_array: bool = False) -> Any:
        """
        清洗解密后字符串（剥离首尾多余的控制字符如 \\u0004 等），并反序列化为 JSON
        """
        start_char = "[" if expect_array else "{"
        end_char = "]" if expect_array else "}"

        start_idx = text.find(start_char)
        end_idx = text.rfind(end_char)

        if start_idx == -1 or end_idx == -1 or start_idx > end_idx:
            # 尝试直接解析
            try:
                return json.loads(text.strip())
            except Exception:
                raise CryptoError(f"无法在响应文本中定位有效的 JSON 数据片段: {text[:100]}...")

        clean_str = text[start_idx : end_idx + 1]
        try:
            return json.loads(clean_str)
        except json.JSONDecodeError as e:
            raise CryptoError(f"JSON 解析失败: {e}, 原清洗文本: {clean_str[:100]}...") from e
