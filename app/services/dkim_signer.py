"""
DKIM签名模块
使用dkimpy库为邮件添加DKIM签名
"""
import os
import asyncio
from pathlib import Path
from datetime import datetime
from email.message import EmailMessage
from typing import Optional, Tuple

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import base64

import dkim

from app.config import settings


class DKIMSigner:
    """DKIM签名器"""
    
    # DKIM配置
    DKIM_SELECTOR = "default"  # DKIM选择器
    DKIM_KEY_SIZE = 2048  # RSA密钥长度（至少2048位）
    
    # 密钥文件名
    PRIVATE_KEY_FILE = "dkim_private.pem"
    PUBLIC_KEY_FILE = "dkim_public.pem"
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        初始化DKIM签名器
        
        Args:
            base_dir: 密钥文件存储目录，默认为当前工作目录
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self._private_key = None
        self._public_key = None
        self._private_key_bytes = None
        
    @property
    def private_key_path(self) -> Path:
        """私钥文件路径"""
        return self.base_dir / self.PRIVATE_KEY_FILE
    
    @property
    def public_key_path(self) -> Path:
        """公钥文件路径"""
        return self.base_dir / self.PUBLIC_KEY_FILE
    
    def _generate_key_pair(self) -> Tuple[object, object]:
        """
        生成RSA密钥对（2048位）
        
        Returns:
            (private_key, public_key) 元组
        """
        print(f"[DKIM] 正在生成 {self.DKIM_KEY_SIZE} 位 RSA密钥对...")
        
        # 生成私钥
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.DKIM_KEY_SIZE,
            backend=default_backend()
        )
        
        # 获取公钥
        public_key = private_key.public_key()
        
        print(f"[DKIM] RSA密钥对生成完成")
        return private_key, public_key
    
    def _save_keys(self, private_key: object, public_key: object) -> None:
        """
        保存密钥对到文件
        
        Args:
            private_key: 私钥对象
            public_key: 公钥对象
        """
        # 保存私钥（PEM格式，不加密）
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        self.private_key_path.write_bytes(private_pem)
        # 设置私钥文件权限为仅所有者可读写
        os.chmod(self.private_key_path, 0o600)
        print(f"[DKIM] 私钥已保存: {self.private_key_path}")
        
        # 保存公钥（PEM格式）
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.public_key_path.write_bytes(public_pem)
        print(f"[DKIM] 公钥已保存: {self.public_key_path}")
    
    def _load_keys(self) -> Tuple[object, object]:
        """
        从文件加载密钥对
        
        Returns:
            (private_key, public_key) 元组
        """
        print(f"[DKIM] 加载现有密钥对...")
        
        # 加载私钥
        private_pem = self.private_key_path.read_bytes()
        self._private_key_bytes = private_pem  # 保存原始字节用于dkimpy
        private_key = serialization.load_pem_private_key(
            private_pem,
            password=None,
            backend=default_backend()
        )
        
        # 加载公钥
        public_pem = self.public_key_path.read_bytes()
        public_key = serialization.load_pem_public_key(
            public_pem,
            backend=default_backend()
        )
        
        # 验证密钥长度
        key_size = private_key.key_size
        if key_size < 1024:
            print(f"[DKIM] 警告: 密钥长度 {key_size} 位过短，建议使用至少2048位")
        elif key_size < 2048:
            print(f"[DKIM] 警告: 密钥长度 {key_size} 位，建议升级到2048位")
        else:
            print(f"[DKIM] 密钥加载成功，长度: {key_size} 位")
        
        return private_key, public_key
    
    def initialize(self) -> None:
        """
        初始化DKIM签名器
        检查密钥文件是否存在，不存在则自动生成
        """
        print(f"[DKIM] 初始化DKIM签名器，工作目录: {self.base_dir}")
        
        private_exists = self.private_key_path.exists()
        public_exists = self.public_key_path.exists()
        
        if private_exists and public_exists:
            # 密钥文件都存在，加载它们
            self._private_key, self._public_key = self._load_keys()
        elif private_exists and not public_exists:
            # 只有私钥，从私钥提取公钥
            print(f"[DKIM] 公钥文件不存在，从私钥提取公钥...")
            private_pem = self.private_key_path.read_bytes()
            self._private_key_bytes = private_pem
            self._private_key = serialization.load_pem_private_key(
                private_pem,
                password=None,
                backend=default_backend()
            )
            self._public_key = self._private_key.public_key()
            self._save_keys(self._private_key, self._public_key)
        elif not private_exists and public_exists:
            # 只有公钥，无法签名，重新生成
            print(f"[DKIM] 私钥文件不存在，重新生成密钥对...")
            self._private_key, self._public_key = self._generate_key_pair()
            self._save_keys(self._private_key, self._public_key)
        else:
            # 都不存在，生成新的密钥对
            print(f"[DKIM] 密钥文件不存在，生成新密钥对...")
            self._private_key, self._public_key = self._generate_key_pair()
            self._save_keys(self._private_key, self._public_key)
        
        # 确保私钥字节已保存
        if self._private_key_bytes is None:
            self._private_key_bytes = self.private_key_path.read_bytes()
        
        print(f"[DKIM] 初始化完成")
    
    def get_public_key_dns_record(self) -> str:
        """
        获取DNS TXT记录内容（用于配置DKIM）
        
        注意：DKIM DNS记录需要使用PKCS#1格式的公钥（仅模数和指数），
        而不是SubjectPublicKeyInfo格式。
        
        Returns:
            DNS TXT记录值
        """
        if not self._public_key:
            raise RuntimeError("DKIM签名器未初始化")
        
        # 获取公钥数值
        public_numbers = self._public_key.public_numbers()
        n = public_numbers.n  # 模数
        e = public_numbers.e  # 公开指数
        
        # 编码为DER格式的RSAPublicKey (PKCS#1)
        # RSAPublicKey ::= SEQUENCE { modulus INTEGER, publicExponent INTEGER }
        from cryptography.hazmat.primitives.serialization import Encoding
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
        
        # 使用cryptography库直接获取PKCS#1格式的DER编码
        # 我们需要手动构建DER序列
        def int_to_bytes(n: int) -> bytes:
            """将整数转换为字节（大端序）"""
            if n == 0:
                return b'\x00'
            byte_len = (n.bit_length() + 7) // 8
            result = n.to_bytes(byte_len, 'big')
            # 如果最高位是1，需要添加前导零（DER整数编码要求）
            if result[0] & 0x80:
                result = b'\x00' + result
            return result
        
        def encode_der_integer(n: int) -> bytes:
            """编码DER整数"""
            value = int_to_bytes(n)
            return encode_der_tlv(0x02, value)
        
        def encode_der_tlv(tag: int, value: bytes) -> bytes:
            """编码DER TLV"""
            length = len(value)
            if length < 128:
                length_bytes = bytes([length])
            elif length < 256:
                length_bytes = bytes([0x81, length])
            else:
                length_bytes = bytes([0x82, (length >> 8) & 0xff, length & 0xff])
            return bytes([tag]) + length_bytes + value
        
        # 构建RSAPublicKey SEQUENCE
        modulus_der = encode_der_integer(n)
        exponent_der = encode_der_integer(e)
        sequence_content = modulus_der + exponent_der
        rsa_public_key_der = encode_der_tlv(0x30, sequence_content)
        
        # Base64编码
        pubkey_b64 = base64.b64encode(rsa_public_key_der).decode('ascii')
        
        # 构建DNS TXT记录
        # 格式: v=DKIM1; k=rsa; p=<public_key_base64>
        dns_record = f"v=DKIM1; k=rsa; p={pubkey_b64}"
        
        return dns_record
    
    def sign_email(self, message: EmailMessage) -> EmailMessage:
        """
        为邮件添加DKIM签名（使用dkimpy库）
        
        Args:
            message: 邮件消息对象
            
        Returns:
            添加了DKIM签名的邮件消息对象
        """
        if not self._private_key_bytes:
            raise RuntimeError("DKIM签名器未初始化，请先调用initialize()")
        
        # 获取域名和选择器
        domain = settings.MAIL_DOMAIN
        selector = self.DKIM_SELECTOR
        
        # 将邮件转换为字节
        # 使用 as_bytes() 获取原始邮件内容
        message_bytes = message.as_bytes()
        
        # 使用dkimpy进行签名
        # include_headers 指定要签名的头字段
        include_headers = [b'from', b'to', b'subject', b'date', b'message-id']
        
        sig = dkim.sign(
            message=message_bytes,
            selector=selector.encode('ascii'),
            domain=domain.encode('ascii'),
            privkey=self._private_key_bytes,
            include_headers=include_headers
        )
        
        # dkim.sign 返回的是完整的 DKIM-Signature 头行（包含 CRLF）
        # 格式: b'DKIM-Signature: v=1; ...\r\n'
        sig_line = sig.decode('ascii').strip()
        
        # 提取头名和值
        if sig_line.startswith('DKIM-Signature:'):
            sig_value = sig_line[len('DKIM-Signature:'):].strip()
        else:
            sig_value = sig_line
        
        # 删除已存在的DKIM-Signature头（如果有）
        if 'DKIM-Signature' in message:
            del message['DKIM-Signature']
        
        # 直接添加到_headers列表，避免MIME编码
        message._headers.append(('DKIM-Signature', sig_value))
        
        print(f"[DKIM] 已为邮件添加DKIM签名 (域名: {domain}, 选择器: {selector})")
        
        return message
    
    def is_initialized(self) -> bool:
        """检查签名器是否已初始化"""
        return self._private_key is not None


# 全局实例（延迟初始化）
_dkim_signer: Optional[DKIMSigner] = None


def get_dkim_signer() -> DKIMSigner:
    """
    获取DKIM签名器实例（单例模式）
    
    Returns:
        DKIMSigner实例
    """
    global _dkim_signer
    if _dkim_signer is None:
        _dkim_signer = DKIMSigner()
        _dkim_signer.initialize()
    return _dkim_signer


def init_dkim_signer(base_dir: Optional[Path] = None) -> DKIMSigner:
    """
    初始化DKIM签名器
    
    Args:
        base_dir: 密钥文件存储目录
        
    Returns:
        DKIMSigner实例
    """
    global _dkim_signer
    _dkim_signer = DKIMSigner(base_dir)
    _dkim_signer.initialize()
    return _dkim_signer
