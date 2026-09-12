"""
HNCU 加密与数据清洗模块
支持 AES-128-ECB PKCS7 加解密及畸变字符剥离
"""
import base64
import json
from typing import Any, Union
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from .constants import (
    DEFAULT_AES_KEY_B64,
    WEB_RSA_MODULUS,
    WEB_RSA_PRIVATE_EXPONENT,
    WEB_RSA_PUBLIC_EXPONENT,
)
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

    @staticmethod
    def rsa_encrypt(text: str) -> str:
        """使用统一身份认证平台默认 Web 公钥进行 Barrett RSA 加密"""
        return BarrettRSA.encrypt(text)

    @staticmethod
    def rsa_decrypt(hex_cipher: str) -> str:
        """使用统一身份认证平台默认 Web 私钥进行 Barrett RSA 解密"""
        return BarrettRSA.decrypt(hex_cipher)


class BarrettRSA:
    """
    统一身份认证 Web 端 Barrett RSA (BigInt) 加解密算法实现
    与联奕科技统一身份认证平台前端 mod178.js / Dave Shapiro BigInt-RSA 100% 字节对齐
    """

    @staticmethod
    def encrypt(
        text: str,
        pub_exp_hex: str = WEB_RSA_PUBLIC_EXPONENT,
        modulus_hex: str = WEB_RSA_MODULUS,
    ) -> str:
        """
        Barrett RSA 公钥加密
        :param text: 待加密明文 (如密码密文或 lyasp+timestamp)
        :param pub_exp_hex: 公钥指数 Hex 字符串
        :param modulus_hex: 公钥模数 Hex 字符串
        :return: 空格分隔的 16 进制密文字符串 (针对 1024 位模数通常为 256 位十六进制)
        """
        try:
            e = int(pub_exp_hex, 16)
            m = int(modulus_hex, 16)

            # 计算 v(m): 模数在 base 65536 下的最高非零 limb 索引
            temp_m = m
            m_limbs = []
            while temp_m > 0:
                m_limbs.append(temp_m & 0xFFFF)
                temp_m >>= 16
            v_m = len(m_limbs) - 1
            chunk_size = 2 * v_m  # 126 字节

            raw = [ord(c) for c in text]
            pad_len = (chunk_size - (len(raw) % chunk_size)) % chunk_size
            raw.extend([0] * pad_len)

            chunks_out = []
            for i in range(0, len(raw), chunk_size):
                chunk = raw[i : i + chunk_size]
                # 小端序打包 16-bit 整数: u.digits[a] = n[c++] + (n[c++] << 8)
                u = 0
                for a, idx in enumerate(range(0, len(chunk), 2)):
                    digit = chunk[idx] + (chunk[idx + 1] << 8)
                    u += digit * (1 << (16 * a))

                g = pow(u, e, m)

                # 将 g 拆解为 16-bit limb 并按大端序转换为 4 字符 hex 格式
                limbs = []
                temp_g = g
                while temp_g > 0:
                    limbs.append(temp_g & 0xFFFF)
                    temp_g >>= 16
                if not limbs:
                    limbs = [0]
                hex_str = "".join(f"{limb:04x}" for limb in reversed(limbs))
                chunks_out.append(hex_str)

            return " ".join(chunks_out)
        except Exception as err:
            raise CryptoError(f"Barrett RSA 加密失败: {err}") from err

    @staticmethod
    def decrypt(
        hex_cipher: str,
        priv_exp_hex: str = WEB_RSA_PRIVATE_EXPONENT,
        modulus_hex: str = WEB_RSA_MODULUS,
    ) -> str:
        """
        Barrett RSA 私钥解密
        :param hex_cipher: 空格分隔的 Hex 密文字符串
        :param priv_exp_hex: 私钥指数 Hex 字符串
        :param modulus_hex: 公钥模数 Hex 字符串
        :return: 解密后的明文字符串
        """
        try:
            d = int(priv_exp_hex, 16)
            m = int(modulus_hex, 16)

            chunks = hex_cipher.split(" ")
            res = []
            for c_str in chunks:
                g = int(c_str, 16)
                u = pow(g, d, m)

                temp_u = u
                bytes_list = []
                while temp_u > 0:
                    digit = temp_u & 0xFFFF
                    bytes_list.append(digit & 0xFF)
                    bytes_list.append((digit >> 8) & 0xFF)
                    temp_u >>= 16

                text_chunk = bytes(bytes_list).rstrip(b"\x00").decode("latin1")
                res.append(text_chunk)

            return "".join(res)
        except Exception as err:
            raise CryptoError(f"Barrett RSA 解密失败: {err}") from err

