"""
附件存储服务 - 管理邮件附件的存储和检索
"""
import os
import uuid
from datetime import datetime
from typing import Optional, Tuple
from app.config import settings


class AttachmentStorage:
    """附件存储服务"""
    
    def __init__(self, base_path: str = None):
        self.base_path = base_path or settings.ATTACHMENT_STORAGE_PATH
    
    def _get_date_path(self) -> str:
        """获取按日期分组的存储路径 (YYYY/MM/DD)"""
        now = datetime.now()
        return os.path.join(
            str(now.year),
            f"{now.month:02d}",
            f"{now.day:02d}"
        )
    
    def _generate_stored_filename(self, original_filename: str) -> str:
        """生成唯一的存储文件名"""
        ext = os.path.splitext(original_filename)[1]
        return f"{uuid.uuid4()}{ext}"
    
    def save(self, content: bytes, original_filename: str) -> Tuple[str, str, str]:
        """
        保存附件到存储
        
        Args:
            content: 文件内容
            original_filename: 原始文件名
            
        Returns:
            Tuple[stored_filename, file_path, relative_path]
            - stored_filename: 存储的文件名
            - file_path: 完整文件路径
            - relative_path: 相对于附件根目录的路径
        """
        # 生成日期目录路径
        date_path = self._get_date_path()
        full_dir_path = os.path.join(self.base_path, date_path)
        
        # 确保目录存在
        os.makedirs(full_dir_path, exist_ok=True)
        
        # 生成唯一文件名
        stored_filename = self._generate_stored_filename(original_filename)
        
        # 完整路径
        file_path = os.path.join(full_dir_path, stored_filename)
        relative_path = os.path.join(date_path, stored_filename)
        
        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return stored_filename, file_path, relative_path
    
    def get_file_path(self, relative_path: str) -> str:
        """根据相对路径获取完整文件路径"""
        return os.path.join(self.base_path, relative_path)
    
    def exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        return os.path.exists(file_path)
    
    def delete(self, file_path: str) -> bool:
        """删除附件文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    def get_storage_info(self) -> dict:
        """获取存储信息"""
        total_size = 0
        file_count = 0
        
        if os.path.exists(self.base_path):
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                        file_count += 1
                    except Exception:
                        pass
        
        return {
            "base_path": self.base_path,
            "total_files": file_count,
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }


# 全局实例
attachment_storage = AttachmentStorage()
