#!/usr/bin/env python3
import os
from pathlib import Path

class SecureKeyStorage:
    """简化的密钥存储（仅用于演示）"""

    def __init__(self, storage_dir=None):
        self.storage_dir = Path(storage_dir or os.path.expanduser("~/.ziwei/keys"))
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def get_key(self, key_name, category='default'):
        """从环境变量或文件中获取密钥"""
        # 优先从环境变量读取
        env_key = f"{category.upper()}_{key_name}"
        env_value = os.getenv(env_key)

        if env_value:
            return env_value

        # 从文件读取
        key_file = self.storage_dir / category / f"{key_name}.enc"
        if key_file.exists():
            with open(key_file, 'r') as f:
                return f.read().strip()

        return None

    def store_key(self, key_name, key_value, category='default'):
        """存储密钥到文件"""
        category_dir = self.storage_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)

        key_file = category_dir / f"{key_name}.enc"
        with open(key_file, 'w') as f:
            f.write(key_value)

        return str(key_file)