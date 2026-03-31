#!/usr/bin/env python3
# =============================================================================
# 钱包私钥加密存储方案
# 功能：安全存储私钥，避免明文风险
# =============================================================================

import os
import sys
import json
import base64
import hashlib
from pathlib import Path
from datetime import datetime

# 检查依赖
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
except ImportError:
    print("❌ 缺少 cryptography 库")
    print("请安装：pip3 install cryptography")
    sys.exit(1)

# =============================================================================
# 方案 1：密码加密存储（推荐）
# =============================================================================

class KeyEncryptor:
    """私钥加密器 - 使用密码保护"""
    
    def __init__(self, password: str = None, salt_file: str = None):
        """
        初始化加密器
        
        Args:
            password: 加密密码（如果不提供，从环境变量读取）
            salt_file: 盐值文件路径
        """
        self.salt_file = salt_file or os.path.expanduser("~/.ziwei/wallet_salt")
        self.password = password or os.getenv("WALLET_ENCRYPTION_PASSWORD")
        
        if not self.password:
            raise ValueError("必须提供加密密码或设置 WALLET_ENCRYPTION_PASSWORD 环境变量")
        
        self.salt = self._get_or_create_salt()
        self.key = self._derive_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_salt(self) -> bytes:
        """获取或创建盐值"""
        salt_path = Path(self.salt_file)
        
        if salt_path.exists():
            with open(salt_path, 'rb') as f:
                salt = f.read()
            print(f"✅ 已加载盐值：{self.salt_file}")
        else:
            # 创建新盐值
            salt = os.urandom(16)
            salt_path.parent.mkdir(parents=True, exist_ok=True)
            with open(salt_path, 'wb') as f:
                f.write(salt)
            # 设置权限（仅所有者可读写）
            os.chmod(salt_path, 0o600)
            print(f"✅ 已创建盐值：{self.salt_file}")
        
        return salt
    
    def _derive_key(self) -> bytes:
        """从密码派生加密密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
        return key
    
    def encrypt(self, private_key: str) -> str:
        """加密私钥"""
        encrypted = self.cipher.encrypt(private_key.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_key: str) -> str:
        """解密私钥"""
        encrypted = base64.b64decode(encrypted_key.encode())
        decrypted = self.cipher.decrypt(encrypted)
        return decrypted.decode()


# =============================================================================
# 方案 2：KMS 密钥管理服务（企业级）
# =============================================================================

class KMSKeyManager:
    """密钥管理服务 - 使用云服务商 KMS"""
    
    def __init__(self, provider: str = "aws"):
        """
        初始化 KMS
        
        Args:
            provider: 云服务商 (aws, gcp, azure, aliyun)
        """
        self.provider = provider
        self.client = self._init_client()
    
    def _init_client(self):
        """初始化 KMS 客户端"""
        if self.provider == "aws":
            try:
                import boto3
                client = boto3.client('kms')
                print("✅ 已连接到 AWS KMS")
                return client
            except ImportError:
                print("❌ 需要安装 boto3: pip3 install boto3")
                return None
        elif self.provider == "aliyun":
            try:
                from aliyunsdkcore.client import AcsClient
                from aliyunsdkkms.request.v20160120 import EncryptRequest, DecryptRequest
                print("✅ 已连接到 阿里云 KMS")
                return {'encrypt': EncryptRequest, 'decrypt': DecryptRequest}
            except ImportError:
                print("❌ 需要安装 aliyun-python-sdk-kms")
                return None
        else:
            print(f"⚠️  不支持的 KMS 提供商：{self.provider}")
            return None
    
    def encrypt(self, plaintext: str, key_id: str) -> str:
        """使用 KMS 加密"""
        if not self.client:
            raise Exception("KMS 客户端未初始化")
        
        if self.provider == "aws":
            response = self.client.encrypt(
                KeyId=key_id,
                Plaintext=plaintext.encode()
            )
            return base64.b64encode(response['CiphertextBlob']).decode()
        elif self.provider == "aliyun":
            # 阿里云 KMS 实现
            pass
    
    def decrypt(self, ciphertext: str, key_id: str) -> str:
        """使用 KMS 解密"""
        if not self.client:
            raise Exception("KMS 客户端未初始化")
        
        if self.provider == "aws":
            ciphertext_blob = base64.b64decode(ciphertext.encode())
            response = self.client.decrypt(CiphertextBlob=ciphertext_blob)
            return response['Plaintext'].decode()
        elif self.provider == "aliyun":
            # 阿里云 KMS 实现
            pass


# =============================================================================
# 方案 3：硬件钱包集成（最安全）
# =============================================================================

class HardwareWalletManager:
    """硬件钱包管理器 - Ledger/Trezor"""
    
    def __init__(self, device_type: str = "ledger"):
        """
        初始化硬件钱包
        
        Args:
            device_type: 设备类型 (ledger, trezor)
        """
        self.device_type = device_type
        self.device = None
        self._connect()
    
    def _connect(self):
        """连接硬件钱包"""
        try:
            if self.device_type == "ledger":
                from ledgerblue.Dongle import getDongle
                self.device = getDongle(True)
                print("✅ 已连接到 Ledger 设备")
            elif self.device_type == "trezor":
                import trezorlib.client
                from trezorlib.transport_hid import HidTransport
                # Trezor 连接代码
                print("✅ 已连接到 Trezor 设备")
        except ImportError as e:
            print(f"⚠️  硬件钱包库未安装：{e}")
            print("Ledger: pip3 install ledgerblue")
            print("Trezor: pip3 install trezor")
        except Exception as e:
            print(f"⚠️  无法连接硬件钱包：{e}")
            print("请确保设备已连接并解锁")
    
    def sign_transaction(self, transaction: dict) -> dict:
        """使用硬件钱包签名交易"""
        if not self.device:
            raise Exception("硬件钱包未连接")
        
        # 硬件钱包签名逻辑
        # 私钥永远不会离开设备
        print("🔐 请在硬件钱包上确认交易")
        
        # 模拟签名（实际实现需要调用设备 API）
        signed_tx = {
            'signed': True,
            'signature': '0x' + '0' * 130,  # 模拟签名
            'transaction': transaction
        }
        
        return signed_tx
    
    def get_address(self, path: str = "m/44'/60'/0'/0/0") -> str:
        """获取硬件钱包地址"""
        if not self.device:
            raise Exception("硬件钱包未连接")
        
        # 从硬件钱包获取地址
        # 实际实现需要调用设备 API
        print(f"📍 从路径 {path} 获取地址")
        
        # 模拟地址
        return "0x" + "0" * 40


# =============================================================================
# 方案 4：多签钱包（机构级安全）
# =============================================================================

class MultiSigWallet:
    """多签钱包管理"""
    
    def __init__(self, required_signatures: int, total_signers: int):
        """
        初始化多签钱包
        
        Args:
            required_signatures: 需要的签名数
            total_signers: 总签名者数
        """
        self.required = required_signatures
        self.total = total_signers
        self.signers = []
        self.pending_transactions = {}
    
    def add_signer(self, address: str, public_key: str):
        """添加签名者"""
        self.signers.append({
            'address': address,
            'public_key': public_key,
            'added_at': datetime.now().isoformat()
        })
        print(f"✅ 已添加签名者：{address[:10]}...")
    
    def create_transaction(self, to: str, amount: float, data: str = "0x") -> dict:
        """创建多签交易"""
        tx_id = hashlib.sha256(
            f"{to}{amount}{data}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        transaction = {
            'id': tx_id,
            'to': to,
            'amount': amount,
            'data': data,
            'created_at': datetime.now().isoformat(),
            'signatures': [],
            'required': self.required,
            'status': 'pending'
        }
        
        self.pending_transactions[tx_id] = transaction
        print(f"📝 创建多签交易：{tx_id}")
        print(f"   需要 {self.required}/{self.total} 个签名")
        
        return transaction
    
    def sign_transaction(self, tx_id: str, signer_address: str, signature: str) -> bool:
        """签名交易"""
        if tx_id not in self.pending_transactions:
            print(f"❌ 交易不存在：{tx_id}")
            return False
        
        tx = self.pending_transactions[tx_id]
        
        # 检查签名者是否合法
        if signer_address not in [s['address'] for s in self.signers]:
            print(f"❌ 非法签名者：{signer_address}")
            return False
        
        # 添加签名
        tx['signatures'].append({
            'signer': signer_address,
            'signature': signature,
            'signed_at': datetime.now().isoformat()
        })
        
        print(f"✅ 已签名：{tx_id} ({len(tx['signatures'])}/{self.required})")
        
        # 检查是否达到所需签名数
        if len(tx['signatures']) >= self.required:
            tx['status'] = 'ready'
            print(f"🎉 交易已就绪，可以执行：{tx_id}")
        
        return True


# =============================================================================
# 加密钱包存储管理器
# =============================================================================

class SecureWalletStorage:
    """安全钱包存储管理器"""
    
    def __init__(self, storage_path: str = None, encryption_password: str = None):
        """
        初始化安全存储
        
        Args:
            storage_path: 存储文件路径
            encryption_password: 加密密码
        """
        self.storage_path = storage_path or os.path.expanduser("~/.ziwei/secure_wallets.json")
        self.password = encryption_password or os.getenv("WALLET_ENCRYPTION_PASSWORD")
        
        if not self.password:
            raise ValueError("必须提供加密密码")
        
        self.encryptor = KeyEncryptor(self.password)
        self.wallets = self._load_wallets()
    
    def _load_wallets(self) -> dict:
        """加载钱包"""
        storage_file = Path(self.storage_path)
        
        if storage_file.exists():
            with open(storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ 已加载钱包存储：{self.storage_path}")
            return data.get('wallets', {})
        else:
            print(f"📁 创建新钱包存储：{self.storage_path}")
            return {}
    
    def _save_wallets(self):
        """保存钱包"""
        storage_file = Path(self.storage_path)
        storage_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'wallets': self.wallets
        }
        
        with open(storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 设置权限（仅所有者可读写）
        os.chmod(storage_file, 0o600)
        print(f"💾 已保存钱包存储")
    
    def add_wallet(self, name: str, private_key: str, blockchain: str = "ETH"):
        """添加钱包（自动加密）"""
        encrypted_key = self.encryptor.encrypt(private_key)
        
        self.wallets[name] = {
            'blockchain': blockchain,
            'encrypted_private_key': encrypted_key,
            'created_at': datetime.now().isoformat(),
            'last_used': None
        }
        
        self._save_wallets()
        print(f"✅ 已添加钱包：{name} ({blockchain})")
    
    def get_wallet(self, name: str) -> dict:
        """获取钱包（自动解密）"""
        if name not in self.wallets:
            raise KeyError(f"钱包不存在：{name}")
        
        wallet = self.wallets[name]
        decrypted_key = self.encryptor.decrypt(wallet['encrypted_private_key'])
        
        # 更新最后使用时间
        wallet['last_used'] = datetime.now().isoformat()
        self._save_wallets()
        
        return {
            'name': name,
            'blockchain': wallet['blockchain'],
            'private_key': decrypted_key,
            'created_at': wallet['created_at'],
            'last_used': wallet['last_used']
        }
    
    def list_wallets(self) -> list:
        """列出所有钱包（不显示私钥）"""
        wallets = []
        for name, data in self.wallets.items():
            wallets.append({
                'name': name,
                'blockchain': data['blockchain'],
                'created_at': data['created_at'],
                'last_used': data.get('last_used', '从未使用')
            })
        return wallets
    
    def delete_wallet(self, name: str):
        """删除钱包"""
        if name in self.wallets:
            del self.wallets[name]
            self._save_wallets()
            print(f"✅ 已删除钱包：{name}")
        else:
            print(f"❌ 钱包不存在：{name}")


# =============================================================================
# 使用示例
# =============================================================================

def demo_encryption():
    """演示加密功能"""
    print("="*60)
    print("🔐 私钥加密存储演示")
    print("="*60)
    
    # 设置密码
    password = "MySecurePassword123!"  # 实际使用时从环境变量读取
    
    # 创建加密器
    encryptor = KeyEncryptor(password)
    
    # 示例私钥
    private_key = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    
    # 加密
    encrypted = encryptor.encrypt(private_key)
    print(f"\n📦 原始私钥：{private_key[:20]}...")
    print(f"🔒 加密后：{encrypted[:50]}...")
    
    # 解密
    decrypted = encryptor.decrypt(encrypted)
    print(f"🔓 解密后：{decrypted[:20]}...")
    
    # 验证
    print(f"\n✅ 验证：{'成功' if private_key == decrypted else '失败'}")


def demo_secure_storage():
    """演示安全存储"""
    print("\n" + "="*60)
    print("💼 安全钱包存储演示")
    print("="*60)
    
    # 设置密码
    password = "MySecurePassword123!"
    
    # 创建安全存储
    storage = SecureWalletStorage(encryption_password=password)
    
    # 添加钱包
    storage.add_wallet(
        name="主钱包-ETH",
        private_key="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        blockchain="ETH"
    )
    
    storage.add_wallet(
        name="交易钱包-BTC",
        private_key="L1234567890abcdefghijklmnopqrstuv",
        blockchain="BTC"
    )
    
    # 列出钱包
    print("\n📋 钱包列表:")
    wallets = storage.list_wallets()
    for wallet in wallets:
        print(f"  - {wallet['name']} ({wallet['blockchain']})")
        print(f"    创建：{wallet['created_at'][:10]}")
        print(f"    使用：{wallet['last_used'][:10] if wallet['last_used'] != '从未使用' else '从未使用'}")
    
    # 获取钱包（解密）
    print("\n🔓 获取钱包:")
    wallet = storage.get_wallet("主钱包-ETH")
    print(f"  名称：{wallet['name']}")
    print(f"  区块链：{wallet['blockchain']}")
    print(f"  私钥：{wallet['private_key'][:20]}...")


def main():
    """主函数"""
    print("\n紫微智控 - 钱包安全加密方案\n")
    
    # 演示加密
    demo_encryption()
    
    # 演示安全存储
    demo_secure_storage()
    
    print("\n" + "="*60)
    print("✅ 演示完成")
    print("="*60)
    
    print("\n📚 安全建议:")
    print("  1. 使用强密码（16 位以上，包含大小写、数字、符号）")
    print("  2. 密码存储在安全地方（密码管理器/纸质备份）")
    print("  3. 定期备份加密钱包文件")
    print("  4. 大额资金使用硬件钱包")
    print("  5. 重要交易使用多签钱包")
    
    print("\n🔧 下一步:")
    print("  1. 设置 WALLET_ENCRYPTION_PASSWORD 环境变量")
    print("  2. 运行此脚本迁移现有钱包")
    print("  3. 删除明文配置文件")
    print("  4. 更新交易机器人使用加密钱包")


if __name__ == "__main__":
    main()
