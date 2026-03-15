"""
DKIM签名工具模块
自动管理DKIM密钥的生成和加载
"""
import os
import rsa
from pathlib import Path
from typing import Optional, Tuple


class DKIMKeyManager:
    """DKIM密钥管理器"""
    
    def __init__(self, 
                 selector: str = "default",
                 key_size: int = 2048,
                 private_key_path: str = "dkim_private.pem",
                 public_key_path: str = "dkim_public.pem"):
        """
        初始化DKIM密钥管理器
        
        Args:
            selector: DKIM选择器
            key_size: RSA密钥长度（至少2048位）
            private_key_path: 私钥文件路径（相对于当前工作目录）
            public_key_path: 公钥文件路径（相对于当前工作目录）
        """
        if key_size < 2048:
            raise ValueError(f"密钥长度必须至少2048位，当前为{key_size}位")
        
        self.selector = selector
        self.key_size = key_size
        self.private_key_path = Path(private_key_path)
        self.public_key_path = Path(public_key_path)
        self._private_key: Optional[rsa.PrivateKey] = None
        self._public_key: Optional[rsa.PublicKey] = None
        
        # 自动初始化密钥
        self._ensure_keys()
    
    def _ensure_keys(self) -> None:
        """确保密钥存在，不存在则自动生成"""
        if self.private_key_path.exists() and self.public_key_path.exists():
            print(f"[DKIM] 发现已存在密钥文件，正在加载...")
            self._load_keys()
        else:
            print(f"[DKIM] 密钥文件不存在，正在生成新的 {self.key_size} 位RSA密钥对...")
            self._generate_keys()
    
    def _generate_keys(self) -> None:
        """生成RSA密钥对"""
        # 生成密钥对
        (self._public_key, self._private_key) = rsa.newkeys(self.key_size)
        
        # 保存私钥
        with open(self.private_key_path, 'wb') as f:
            f.write(self._private_key.save_pkcs1())
        print(f"[DKIM] 私钥已保存到: {self.private_key_path.absolute()}")
        
        # 保存公钥
        with open(self.public_key_path, 'wb') as f:
            f.write(self._public_key.save_pkcs1())
        print(f"[DKIM] 公钥已保存到: {self.public_key_path.absolute()}")
        
        # 设置文件权限（仅所有者可读写）
        os.chmod(self.private_key_path, 0o600)
        os.chmod(self.public_key_path, 0o644)
        
        print(f"[DKIM] 密钥生成完成！")
        print(f"[DKIM] 请将以下TXT记录添加到DNS：")
        print(f"[DKIM] 记录名: {self.selector}._domainkey")
        print(f"[DKIM] 记录值: {self.get_dns_txt_record()}")
    
    def _load_keys(self) -> None:
        """加载已存在的密钥"""
        try:
            # 加载私钥
            with open(self.private_key_path, 'rb') as f:
                self._private_key = rsa.PrivateKey.load_pkcs1(f.read())
            
            # 加载公钥
            with open(self.public_key_path, 'rb') as f:
                self._public_key = rsa.PublicKey.load_pkcs1(f.read())
            
            # 验证密钥长度
            key_size = self._private_key.n.bit_length()
            if key_size < 1024:
                print(f"[DKIM] 警告: 当前密钥长度为{key_size}位，少于1024位，建议重新生成！")
            elif key_size < 2048:
                print(f"[DKIM] 警告: 当前密钥长度为{key_size}位，建议使用至少2048位的密钥！")
            else:
                print(f"[DKIM] 密钥加载成功，密钥长度: {key_size}位")
                
        except Exception as e:
            print(f"[DKIM] 密钥加载失败: {e}，将重新生成...")
            self._generate_keys()
    
    def get_private_key_pem(self) -> bytes:
        """获取PEM格式的私钥"""
        if not self._private_key:
            raise RuntimeError("私钥未初始化")
        return self._private_key.save_pkcs1()
    
    def get_public_key_pem(self) -> bytes:
        """获取PEM格式的公钥"""
        if not self._public_key:
            raise RuntimeError("公钥未初始化")
        return self._public_key.save_pkcs1()
    
    def get_dns_txt_record(self) -> str:
        """
        生成DNS TXT记录值
        
        Returns:
            DNS TXT记录值，格式为: v=DKIM1; k=rsa; p=公钥内容
        """
        if not self._public_key:
            raise RuntimeError("公钥未初始化")
        
        # 将公钥转换为base64格式
        import base64
        pubkey_der = self._public_key.save_pkcs1_der()
        pubkey_base64 = base64.b64encode(pubkey_der).decode('ascii')
        
        # 构造DKIM TXT记录
        return f"v=DKIM1; k=rsa; p={pubkey_base64}"
    
    @property
    def private_key(self) -> rsa.PrivateKey:
        """获取私钥"""
        if not self._private_key:
            raise RuntimeError("私钥未初始化")
        return self._private_key
    
    @property
    def public_key(self) -> rsa.PublicKey:
        """获取公钥"""
        if not self._public_key:
            raise RuntimeError("公钥未初始化")
        return self._public_key


# 全局DKIM密钥管理器实例
_dkim_manager: Optional[DKIMKeyManager] = None


def get_dkim_manager(selector: str = "default", 
                     key_size: int = 2048) -> DKIMKeyManager:
    """
    获取DKIM密钥管理器实例（单例模式）
    
    Args:
        selector: DKIM选择器
        key_size: RSA密钥长度
        
    Returns:
        DKIMKeyManager实例
    """
    global _dkim_manager
    if _dkim_manager is None:
        _dkim_manager = DKIMKeyManager(selector=selector, key_size=key_size)
    return _dkim_manager
