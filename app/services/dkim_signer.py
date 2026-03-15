"""
DKIM签名模块
自动检查和生成DKIM密钥对，为邮件添加DKIM签名
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
        
        print(f"[DKIM] 初始化完成")
    
    def get_public_key_dns_record(self) -> str:
        """
        获取DNS TXT记录内容（用于配置DKIM）
        
        Returns:
            DNS TXT记录值
        """
        if not self._public_key:
            raise RuntimeError("DKIM签名器未初始化")
        
        # 获取公钥的DER编码
        public_der = self._public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Base64编码
        pubkey_b64 = base64.b64encode(public_der).decode('ascii')
        
        # 构建DNS TXT记录
        # 格式: v=DKIM1; k=rsa; p=<public_key_base64>
        dns_record = f"v=DKIM1; k=rsa; p={pubkey_b64}"
        
        return dns_record
    
    def _canonicalize_headers(self, headers: list, message: EmailMessage) -> str:
        """
        规范化邮件头
        
        Args:
            headers: 需要签名的头字段列表
            message: 邮件消息对象
            
        Returns:
            规范化后的头字符串
        """
        canonicalized = []
        for header in headers:
            value = message.get(header, "")
            if value:
                # 简单规范化：移除多余空白，保留原始值
                canonicalized.append(f"{header}: {value}")
        return "\r\n".join(canonicalized) + "\r\n"
    
    def _canonicalize_body(self, body: str) -> str:
        """
        规范化邮件正文
        
        Args:
            body: 邮件正文
            
        Returns:
            规范化后的正文
        """
        # 简单规范化：确保行尾为CRLF，移除尾部空行
        body = body.replace("\r\n", "\n").replace("\n", "\r\n")
        # 移除尾部空白行
        while body.endswith("\r\n\r\n"):
            body = body[:-2]
        return body
    
    def sign_email(self, message: EmailMessage) -> EmailMessage:
        """
        为邮件添加DKIM签名
        
        Args:
            message: 邮件消息对象
            
        Returns:
            添加了DKIM签名的邮件消息对象
        """
        if not self._private_key:
            raise RuntimeError("DKIM签名器未初始化，请先调用initialize()")
        
        # 获取签名时间戳
        now = datetime.utcnow()
        timestamp = int(now.timestamp())
        
        # 需要签名的头字段
        signed_headers = ["From", "To", "Subject", "Date", "Message-ID"]
        
        # 构建规范化的头字符串
        canonicalized_headers = ""
        for header in signed_headers:
            value = message.get(header, "")
            if value:
                canonicalized_headers += f"{header}: {value}\r\n"
        
        # 获取邮件正文
        body = message.get_content()
        if isinstance(body, str):
            canonicalized_body = self._canonicalize_body(body)
        else:
            canonicalized_body = ""
        
        # 计算正文哈希
        import hashlib
        body_hash = hashlib.sha256(canonicalized_body.encode('utf-8')).digest()
        body_hash_b64 = base64.b64encode(body_hash).decode('ascii')
        
        # 构建DKIM签名头内容
        domain = settings.MAIL_DOMAIN
        selector = self.DKIM_SELECTOR
        
        # 构建签名字符串
        # DKIM-Signature头格式
        dkim_header_base = (
            f"v=1; a=rsa-sha256; c=relaxed/simple; d={domain}; s={selector}; "
            f"t={timestamp}; bh={body_hash_b64}; "
            f"h={':'.join(signed_headers)}; b="
        )
        
        # 构建待签名数据
        sign_data = canonicalized_headers + f"dkim-signature:{dkim_header_base}"
        
        # 使用私钥签名
        signature = self._private_key.sign(
            sign_data.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        # Base64编码签名
        signature_b64 = base64.b64encode(signature).decode('ascii')
        
        # 完整的DKIM签名头
        dkim_signature = dkim_header_base + signature_b64
        
        # 添加DKIM签名头
        message["DKIM-Signature"] = dkim_signature
        
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
