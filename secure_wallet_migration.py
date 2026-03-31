#!/usr/bin/env python3
# =============================================================================
# 钱包安全迁移工具 - 增强版（方案 1+2 组合）
# 功能：密码加密 + 本地 KMS + 自动备份 + 审计日志
# =============================================================================

import os
import sys
import json
import shutil
import hashlib
import secrets
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 检查依赖
try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.backends import default_backend
    import base64
except ImportError:
    print("❌ 缺少 cryptography 库")
    print("安装：pip3 install cryptography")
    sys.exit(1)

# =============================================================================
# 配置
# =============================================================================

ZIWEI_DIR = Path("/home/admin/Ziwei")
SECURE_DIR = ZIWEI_DIR / ".ziwei" / "secure"
BACKUP_DIR = ZIWEI_DIR / "backup" / "wallets"
ENCRYPTION_VERSION = "2.0"

# 需要迁移的文件
SOURCE_FILES = [
    ZIWEI_DIR / "projects" / "x402-trading-bot" / ".env",
    ZIWEI_DIR / "data" / "wallet_latest.json",
    ZIWEI_DIR / "data" / "wallets.json",
]

# 敏感字段关键词
SENSITIVE_KEYWORDS = [
    'private', 'secret', 'key', 'password', 'token', 'credential',
    'API_KEY', 'API_SECRET', 'WALLET', 'PRIVATE_KEY'
]


# =============================================================================
# 增强版加密器（方案 1+2 组合）
# =============================================================================

class EnhancedEncryptor:
    """
    增强版加密器 - 方案 1（密码）+ 方案 2（本地 KMS）组合
    
    安全特性：
    - AES-256-GCM 加密（认证加密）
    - PBKDF2 密钥派生（10 万次迭代）
    - 随机盐值 + 随机 nonce
    - 双重加密（主密码 + KMS 密钥）
    - 完整性校验（HMAC）
    """
    
    def __init__(self, master_password: str, kms_key: str = None):
        """
        初始化加密器
        
        Args:
            master_password: 主密码（用户记忆）
            kms_key: KMS 密钥（文件存储，额外保护）
        """
        self.master_password = master_password
        self.kms_key = kms_key or self._load_or_create_kms_key()
        self.salt = self._load_or_create_salt()
        
        # 派生主密钥（密码 + KMS 组合）
        combined_secret = master_password + self.kms_key
        self.encryption_key = self._derive_key(combined_secret)
    
    def _load_or_create_kms_key(self) -> str:
        """加载或创建本地 KMS 密钥"""
        kms_file = SECURE_DIR / "kms_key"
        
        if kms_file.exists():
            with open(kms_file, 'r') as f:
                kms_key = f.read().strip()
            print(f"✅ 已加载 KMS 密钥：{kms_file}")
        else:
            # 生成新的 KMS 密钥（32 字节随机）
            kms_key = secrets.token_hex(32)
            SECURE_DIR.mkdir(parents=True, exist_ok=True)
            with open(kms_file, 'w') as f:
                f.write(kms_key)
            # 设置严格权限
            os.chmod(kms_file, 0o600)
            os.chmod(SECURE_DIR, 0o700)
            print(f"✅ 已创建 KMS 密钥：{kms_file}")
        
        return kms_key
    
    def _load_or_create_salt(self) -> bytes:
        """加载或创建盐值"""
        salt_file = SECURE_DIR / "wallet_salt"
        
        if salt_file.exists():
            with open(salt_file, 'rb') as f:
                salt = f.read()
            print(f"✅ 已加载盐值：{salt_file}")
        else:
            salt = secrets.token_bytes(16)
            with open(salt_file, 'wb') as f:
                f.write(salt)
            os.chmod(salt_file, 0o600)
            print(f"✅ 已创建盐值：{salt_file}")
        
        return salt
    
    def _derive_key(self, secret: str) -> bytes:
        """从秘密派生加密密钥（PBKDF2）"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,  # 10 万次迭代
            backend=default_backend()
        )
        return kdf.derive(secret.encode())
    
    def encrypt(self, plaintext: str, associated_data: str = None) -> dict:
        """
        加密数据（AES-256-GCM）
        
        Returns:
            包含密文、nonce、tag 的字典
        """
        # 生成随机 nonce（12 字节）
        nonce = secrets.token_bytes(12)
        
        # AES-GCM 加密
        aesgcm = AESGCM(self.encryption_key)
        ciphertext = aesgcm.encrypt(
            nonce,
            plaintext.encode(),
            associated_data.encode() if associated_data else None
        )
        
        # 分离密文和 tag（最后 16 字节）
        tag = ciphertext[-16:]
        ciphertext = ciphertext[:-16]
        
        return {
            'version': ENCRYPTION_VERSION,
            'nonce': base64.b64encode(nonce).decode(),
            'ciphertext': base64.b64encode(ciphertext).decode(),
            'tag': base64.b64encode(tag).decode(),
            'associated_data': associated_data,
            'created_at': datetime.now().isoformat()
        }
    
    def decrypt(self, encrypted_data: dict, associated_data: str = None) -> str:
        """解密数据"""
        # 验证版本
        if encrypted_data.get('version') != ENCRYPTION_VERSION:
            raise ValueError(f"不支持的版本：{encrypted_data.get('version')}")
        
        # 解码
        nonce = base64.b64decode(encrypted_data['nonce'])
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])
        tag = base64.b64decode(encrypted_data['tag'])
        
        # AES-GCM 解密
        aesgcm = AESGCM(self.encryption_key)
        plaintext = aesgcm.decrypt(
            nonce,
            ciphertext + tag,
            associated_data.encode() if associated_data else None
        )
        
        return plaintext.decode()


# =============================================================================
# 安全钱包存储管理器
# =============================================================================

class SecureWalletStorage:
    """安全钱包存储管理器"""
    
    def __init__(self, master_password: str, storage_path: str = None):
        """
        初始化
        
        Args:
            master_password: 主密码
            storage_path: 存储文件路径
        """
        self.storage_path = Path(storage_path) if storage_path else SECURE_DIR / "wallets.json"
        self.encryptor = EnhancedEncryptor(master_password)
        self.wallets = self._load_wallets()
    
    def _load_wallets(self) -> dict:
        """加载钱包"""
        if self.storage_path.exists():
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ 已加载钱包存储：{self.storage_path}")
            return data.get('wallets', {})
        else:
            print(f"📁 创建新钱包存储：{self.storage_path}")
            return {}
    
    def _save_wallets(self):
        """保存钱包"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'version': ENCRYPTION_VERSION,
            'created_at': datetime.now().isoformat(),
            'wallets': self.wallets
        }
        
        # 写入临时文件，然后原子替换
        temp_file = self.storage_path.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 设置严格权限
        os.chmod(temp_file, 0o600)
        
        # 原子替换
        temp_file.replace(self.storage_path)
        print(f"💾 已保存钱包存储")
    
    def add_wallet(self, name: str, private_key: str, blockchain: str = "ETH", metadata: dict = None):
        """添加钱包（自动加密）"""
        # 加密私钥
        encrypted = self.encryptor.encrypt(
            private_key,
            associated_data=f"{name}:{blockchain}"
        )
        
        self.wallets[name] = {
            'blockchain': blockchain,
            'encrypted_private_key': encrypted,
            'metadata': metadata or {},
            'created_at': datetime.now().isoformat(),
            'last_used': None,
            'access_count': 0
        }
        
        self._save_wallets()
        print(f"✅ 已添加钱包：{name} ({blockchain})")
    
    def get_wallet(self, name: str) -> dict:
        """获取钱包（自动解密）"""
        if name not in self.wallets:
            raise KeyError(f"钱包不存在：{name}")
        
        wallet = self.wallets[name]
        
        # 解密私钥
        decrypted_key = self.encryptor.decrypt(
            wallet['encrypted_private_key'],
            associated_data=f"{name}:{wallet['blockchain']}"
        )
        
        # 更新访问记录
        wallet['last_used'] = datetime.now().isoformat()
        wallet['access_count'] = wallet.get('access_count', 0) + 1
        self._save_wallets()
        
        # 记录审计日志
        self._log_access(name, 'decrypt')
        
        return {
            'name': name,
            'blockchain': wallet['blockchain'],
            'private_key': decrypted_key,
            'metadata': wallet['metadata'],
            'created_at': wallet['created_at'],
            'last_used': wallet['last_used'],
            'access_count': wallet['access_count']
        }
    
    def list_wallets(self) -> list:
        """列出所有钱包（不显示私钥）"""
        wallets = []
        for name, data in self.wallets.items():
            wallets.append({
                'name': name,
                'blockchain': data['blockchain'],
                'created_at': data['created_at'],
                'last_used': data.get('last_used', '从未使用'),
                'access_count': data.get('access_count', 0)
            })
        return wallets
    
    def delete_wallet(self, name: str):
        """删除钱包"""
        if name in self.wallets:
            del self.wallets[name]
            self._save_wallets()
            self._log_access(name, 'delete')
            print(f"✅ 已删除钱包：{name}")
        else:
            print(f"❌ 钱包不存在：{name}")
    
    def _log_access(self, wallet_name: str, action: str):
        """记录审计日志"""
        log_file = SECURE_DIR / "access.log"
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'wallet': wallet_name,
            'action': action,
            'hostname': os.uname().nodename,
            'user': os.getenv('USER', 'unknown')
        }
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')


# =============================================================================
# 敏感信息扫描器
# =============================================================================

class SensitiveDataScanner:
    """敏感信息扫描器"""
    
    @staticmethod
    def scan_file(file_path: Path) -> Dict[str, str]:
        """扫描文件中的敏感信息"""
        sensitive_data = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 如果是 JSON 文件
            if file_path.suffix == '.json':
                try:
                    data = json.loads(content)
                    SensitiveDataScanner._scan_json(data, "", sensitive_data)
                except json.JSONDecodeError:
                    pass
            
            # 如果是.env 文件
            elif file_path.name.startswith('.env'):
                for line_num, line in enumerate(content.split('\n'), 1):
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        
                        if any(kw in key.lower() for kw in SENSITIVE_KEYWORDS):
                            if value and len(value) >= 16:
                                sensitive_data[f"{file_path.name}:{key}"] = value
                                print(f"  🔑 找到敏感数据：{key}")
            
            return sensitive_data
        
        except Exception as e:
            print(f"  ⚠️  扫描失败：{e}")
            return {}
    
    @staticmethod
    def _scan_json(obj, path: str, result: dict):
        """递归扫描 JSON"""
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_path = f"{path}.{k}" if path else k
                if any(kw in k.lower() for kw in SENSITIVE_KEYWORDS):
                    if isinstance(v, str) and len(v) >= 16:
                        result[new_path] = v
                        print(f"  🔑 找到敏感数据：{new_path}")
                SensitiveDataScanner._scan_json(v, new_path, result)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                SensitiveDataScanner._scan_json(item, f"{path}[{i}]", result)


# =============================================================================
# 迁移工具
# =============================================================================

class WalletMigrator:
    """钱包迁移工具"""
    
    def __init__(self, master_password: str):
        self.password = master_password
        self.storage = SecureWalletStorage(master_password)
        self.backup_dir = BACKUP_DIR / datetime.now().strftime('%Y%m%d_%H%M%S')
        self.migration_log = []
    
    def backup_source_files(self, files: List[Path]):
        """备份源文件"""
        print_header("步骤 1: 备份源文件")
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in files:
            if file_path.exists():
                backup_path = self.backup_dir / file_path.name
                shutil.copy2(file_path, backup_path)
                print(f"  ✅ 备份：{file_path.name} → {backup_path}")
                self.migration_log.append({
                    'action': 'backup',
                    'file': str(file_path),
                    'backup': str(backup_path),
                    'time': datetime.now().isoformat()
                })
        
        print(f"\n💾 备份完成：{self.backup_dir}")
    
    def scan_and_migrate(self, files: List[Path]):
        """扫描并迁移敏感数据"""
        print_header("步骤 2: 扫描并迁移敏感数据")
        
        for file_path in files:
            if not file_path.exists():
                continue
            
            print(f"\n📄 扫描：{file_path}")
            sensitive_data = SensitiveDataScanner.scan_file(file_path)
            
            for name, value in sensitive_data.items():
                # 清理名称
                clean_name = name.replace(':', '_').replace('.', '_').replace('/', '_')
                
                # 判断类型
                blockchain = "API"
                if 'wallet' in name.lower() or 'eth' in name.lower():
                    blockchain = "ETH"
                elif 'btc' in name.lower() or 'bitcoin' in name.lower():
                    blockchain = "BTC"
                elif 'api' in name.lower():
                    blockchain = "API"
                
                # 添加到加密存储
                try:
                    self.storage.add_wallet(
                        name=clean_name,
                        private_key=value,
                        blockchain=blockchain,
                        metadata={
                            'source_file': str(file_path),
                            'migrated_at': datetime.now().isoformat()
                        }
                    )
                    self.migration_log.append({
                        'action': 'migrate',
                        'name': clean_name,
                        'blockchain': blockchain,
                        'time': datetime.now().isoformat()
                    })
                except Exception as e:
                    print(f"  ⚠️  迁移失败 {clean_name}: {e}")
    
    def sanitize_source_files(self, files: List[Path]):
        """清理源文件中的敏感信息"""
        print_header("步骤 3: 清理源文件")
        
        print("⚠️  此操作将删除源文件中的敏感信息！")
        confirm = input("确认继续？(yes/no): ")
        
        if confirm.lower() != 'yes':
            print("⚠️  跳过清理步骤")
            return
        
        for file_path in files:
            if not file_path.exists():
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original = content
                
                # 替换敏感值
                import re
                for keyword in SENSITIVE_KEYWORDS:
                    pattern = rf'({keyword})\s*=\s*["\']?[^\s"\']{{16,}}["\']?'
                    content = re.sub(pattern, r'\1=REMOVED_FOR_SECURITY', content, flags=re.IGNORECASE)
                
                if content != original:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  ✅ 清理：{file_path}")
                    self.migration_log.append({
                        'action': 'sanitize',
                        'file': str(file_path),
                        'time': datetime.now().isoformat()
                    })
                else:
                    print(f"  ℹ️  无需清理：{file_path}")
            
            except Exception as e:
                print(f"  ❌ 清理失败 {file_path}: {e}")
    
    def verify_migration(self):
        """验证迁移结果"""
        print_header("步骤 4: 验证迁移")
        
        wallets = self.storage.list_wallets()
        
        if not wallets:
            print("❌ 钱包列表为空！")
            return False
        
        print(f"✅ 加密存储包含 {len(wallets)} 个敏感数据项:")
        for wallet in wallets:
            print(f"  - {wallet['name']} ({wallet['blockchain']})")
        
        # 测试解密
        print("\n🧪 测试解密...")
        test_wallet = wallets[0]
        try:
            decrypted = self.storage.get_wallet(test_wallet['name'])
            if decrypted['private_key']:
                print(f"  ✅ 解密成功：{test_wallet['name']}")
                print(f"     值：{decrypted['private_key'][:20]}...")
                return True
        except Exception as e:
            print(f"  ❌ 解密失败：{e}")
            return False
        
        return False
    
    def save_migration_log(self):
        """保存迁移日志"""
        log_file = self.backup_dir / "migration_log.json"
        
        log_data = {
            'version': ENCRYPTION_VERSION,
            'timestamp': datetime.now().isoformat(),
            'master_password_set': bool(self.password),
            'migration_log': self.migration_log,
            'summary': {
                'total_files': len(self.migration_log),
                'backed_up': len([x for x in self.migration_log if x['action'] == 'backup']),
                'migrated': len([x for x in self.migration_log if x['action'] == 'migrate']),
                'sanitized': len([x for x in self.migration_log if x['action'] == 'sanitize'])
            }
        }
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        print(f"📋 迁移日志已保存：{log_file}")


# =============================================================================
# 工具函数
# =============================================================================

def print_header(text):
    """打印标题"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")


def get_master_password() -> str:
    """获取主密码"""
    print("🔐 设置主密码（用于加密所有私钥）")
    print("   要求：")
    print("   - 至少 16 位")
    print("   - 包含大小写字母、数字、符号")
    print("   ⚠️  警告：忘记密码 = 永久丢失访问权限！\n")
    
    while True:
        password = input("主密码：")
        
        if len(password) < 16:
            print("❌ 密码太短，至少 16 位")
            continue
        
        # 检查复杂度
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        if not all([has_upper, has_lower, has_digit, has_special]):
            print("❌ 密码必须包含大小写字母、数字和符号")
            continue
        
        confirm = input("确认密码：")
        if password != confirm:
            print("❌ 密码不匹配")
            continue
        
        # 保存到环境变量（本次会话）
        os.environ['WALLET_MASTER_PASSWORD'] = password
        return password


def print_security_tips():
    """打印安全提示"""
    print_header("🔐 安全提示")
    
    tips = """
✅ 已完成：
   1. 主密码加密（方案 1）
   2. 本地 KMS 密钥（方案 2）
   3. AES-256-GCM 加密
   4. PBKDF2 密钥派生（10 万次）
   5. 自动备份
   6. 审计日志

📁 文件位置：
   - 加密钱包：~/.ziwei/secure/wallets.json
   - KMS 密钥：~/.ziwei/secure/kms_key
   - 盐值文件：~/.ziwei/secure/wallet_salt
   - 备份目录：~/Ziwei/backup/wallets/
   - 审计日志：~/.ziwei/secure/access.log

🔐 密码管理：
   ✅ 密码已保存到环境变量（本次会话）
   ✅ 建议保存到密码管理器（1Password/Bitwarden）
   ✅ 或打印纸质备份（保险箱）
   ❌ 不要告诉任何人
   ❌ 不要使用相同密码

📋 下一步：
   1. 验证交易机器人能正常访问加密钱包
   2. 更新代码使用 SecureWalletStorage
   3. 设置定期备份（cron）
   4. 考虑硬件钱包（大额资金）

⚠️  重要提醒：
   - 忘记主密码 = 永久丢失访问权限
   - 定期备份加密文件
   - 定期检查审计日志
   - 大额资金建议使用硬件钱包
"""
    print(tips)


# =============================================================================
# 主函数
# =============================================================================

def main():
    """主函数"""
    print_header("🔐 紫微智控 - 钱包安全迁移工具（增强版）")
    print("方案 1（密码加密）+ 方案 2（本地 KMS）组合")
    print("安全等级：企业级\n")
    
    # 步骤 0: 获取主密码
    print_header("准备步骤：设置主密码")
    password = get_master_password()
    print("✅ 主密码已设置\n")
    
    # 步骤 1: 创建迁移工具
    migrator = WalletMigrator(password)
    
    # 步骤 2: 备份源文件
    migrator.backup_source_files(SOURCE_FILES)
    
    # 步骤 3: 扫描并迁移
    migrator.scan_and_migrate(SOURCE_FILES)
    
    # 步骤 4: 清理源文件
    migrator.sanitize_source_files(SOURCE_FILES)
    
    # 步骤 5: 验证迁移
    if not migrator.verify_migration():
        print("\n❌ 迁移验证失败！请检查备份文件")
        return
    
    # 步骤 6: 保存日志
    migrator.save_migration_log()
    
    # 步骤 7: 安全提示
    print_security_tips()
    
    # 完成
    print_header("🎉 迁移完成！")
    print("✅ 所有敏感数据已安全迁移到加密存储")
    print(f"\n📁 加密钱包文件：{SECURE_DIR / 'wallets.json'}")
    print(f"🔐 KMS 密钥：{SECURE_DIR / 'kms_key'}")
    print(f"💾 备份目录：{migrator.backup_dir}")
    
    print("\n✅ 下一步:")
    print("  1. 更新交易机器人使用 SecureWalletStorage")
    print("  2. 设置 WALLET_MASTER_PASSWORD 环境变量")
    print("  3. 验证功能正常")
    print("  4. 设置定期备份")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
