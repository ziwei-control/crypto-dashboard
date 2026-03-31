#!/usr/bin/env python3
# =============================================================================
# 钱包迁移工具 - 从明文迁移到加密存储
# 功能：安全迁移现有钱包，删除明文配置
# =============================================================================

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加脚本目录到路径
sys.path.insert(0, '/home/admin/Ziwei/scripts')

try:
    from secure_wallet_storage import SecureWalletStorage, KeyEncryptor
except ImportError as e:
    print(f"❌ 导入失败：{e}")
    print("请确保 secure_wallet_storage.py 在同一目录")
    sys.exit(1)

# =============================================================================
# 配置
# =============================================================================

ZIWEI_DIR = Path("/home/admin/Ziwei")
TRADING_BOT_DIR = ZIWEI_DIR / "projects" / "x402-trading-bot"
DATA_DIR = ZIWEI_DIR / "data"

# 可能包含私钥的文件
POSSIBLE_WALLET_FILES = [
    TRADING_BOT_DIR / ".env",
    TRADING_BOT_DIR / ".env.backup",
    DATA_DIR / "wallets.json",
    DATA_DIR / "wallet_latest.json",
    DATA_DIR / "wallet_quick.json",
    DATA_DIR / "wallet_cache.json",
]

# 备份目录
BACKUP_DIR = ZIWEI_DIR / "backup" / "wallets" / datetime.now().strftime('%Y%m%d_%H%M%S')


# =============================================================================
# 工具函数
# =============================================================================

def print_header(text):
    """打印标题"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")


def print_success(text):
    """打印成功消息"""
    print(f"✅ {text}")


def print_warning(text):
    """打印警告消息"""
    print(f"⚠️  {text}")


def print_error(text):
    """打印错误消息"""
    print(f"❌ {text}")


def get_encryption_password():
    """获取加密密码"""
    # 方法 1：环境变量
    password = os.getenv("WALLET_ENCRYPTION_PASSWORD")
    if password:
        return password
    
    # 方法 2：用户输入
    print("🔐 请输入加密密码（用于保护私钥）:")
    print("   要求：至少 16 位，包含大小写、数字、符号")
    print("   警告：忘记密码 = 永久丢失资金！\n")
    
    while True:
        password = input("密码：")
        if len(password) < 16:
            print_warning("密码太短，至少 16 位")
            continue
        
        confirm = input("确认密码：")
        if password != confirm:
            print_warning("密码不匹配，请重试")
            continue
        
        # 保存到环境变量（本次会话）
        os.environ["WALLET_ENCRYPTION_PASSWORD"] = password
        return password


def scan_wallet_files():
    """扫描可能包含私钥的文件"""
    print_header("步骤 1: 扫描钱包文件")
    
    found_files = []
    for file_path in POSSIBLE_WALLET_FILES:
        if file_path.exists():
            print_success(f"找到：{file_path}")
            found_files.append(file_path)
        else:
            print(f"  不存在：{file_path}")
    
    if not found_files:
        print_warning("未找到钱包文件")
    
    return found_files


def extract_private_keys(file_path: Path) -> dict:
    """从文件中提取私钥"""
    print(f"\n📄 分析：{file_path}")
    
    private_keys = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 如果是 JSON 文件
        if file_path.suffix == '.json':
            data = json.loads(content)
            
            # 递归查找私钥
            def find_keys(obj, path=""):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if 'private' in k.lower() or 'key' in k.lower() or 'secret' in k.lower():
                            if isinstance(v, str) and (v.startswith('0x') or len(v) >= 32):
                                private_keys[f"{path}.{k}"] = v
                                print(f"  🔑 找到私钥：{path}.{k}")
                        find_keys(v, f"{path}.{k}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        find_keys(item, f"{path}[{i}]")
            
            find_keys(data)
        
        # 如果是.env 文件
        elif file_path.name.startswith('.env'):
            for line in content.split('\n'):
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    
                    if any(kw in key.lower() for kw in ['private', 'key', 'secret', 'wallet']):
                        if value and (value.startswith('0x') or len(value) >= 32):
                            private_keys[key] = value
                            print(f"  🔑 找到私钥：{key}")
        
        return private_keys
    
    except Exception as e:
        print_error(f"读取失败：{e}")
        return {}


def create_encrypted_storage(private_keys: dict, password: str):
    """创建加密钱包存储"""
    print_header("步骤 2: 创建加密存储")
    
    try:
        # 创建存储
        storage = SecureWalletStorage(
            storage_path=str(ZIWEI_DIR / "data" / "secure_wallets.json"),
            encryption_password=password
        )
        
        # 添加钱包
        added_count = 0
        for name, private_key in private_keys.items():
            try:
                # 清理名称
                clean_name = name.replace('.', '_').replace('[', '_').replace(']', '')
                
                # 判断区块链
                blockchain = "ETH"
                if 'btc' in name.lower() or 'bitcoin' in name.lower():
                    blockchain = "BTC"
                elif 'xrp' in name.lower():
                    blockchain = "XRP"
                
                # 添加钱包
                storage.add_wallet(
                    name=clean_name,
                    private_key=private_key,
                    blockchain=blockchain
                )
                added_count += 1
            
            except Exception as e:
                print_warning(f"添加失败 {name}: {e}")
        
        print_success(f"已添加 {added_count} 个钱包到加密存储")
        return storage
    
    except Exception as e:
        print_error(f"创建存储失败：{e}")
        return None


def backup_original_files(files: list):
    """备份原始文件"""
    print_header("步骤 3: 备份原始文件")
    
    # 创建备份目录
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    backup_count = 0
    for file_path in files:
        try:
            # 复制文件
            import shutil
            backup_path = BACKUP_DIR / file_path.name
            shutil.copy2(file_path, backup_path)
            print_success(f"备份：{file_path.name} → {backup_path}")
            backup_count += 1
        
        except Exception as e:
            print_error(f"备份失败 {file_path}: {e}")
    
    print_success(f"已备份 {backup_count} 个文件到：{BACKUP_DIR}")


def sanitize_files(files: list):
    """清理文件中的敏感信息"""
    print_header("步骤 4: 清理敏感信息")
    
    print_warning("此操作将删除文件中的私钥！")
    confirm = input("确认继续？(yes/no): ")
    
    if confirm.lower() != 'yes':
        print_warning("跳过清理步骤")
        return
    
    sanitized_count = 0
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 替换私钥
            import re
            
            # 替换 0x 开头的私钥
            content = re.sub(
                r'(PRIVATE_KEY|WALLET_KEY|SECRET)=["\']?0x[0-9a-fA-F]{64}["\']?',
                r'\1=REMOVED_FOR_SECURITY',
                content
            )
            
            # 替换其他长密钥
            content = re.sub(
                r'(PRIVATE_KEY|WALLET_KEY|SECRET)=["\']?[A-Za-z0-9+/=]{32,}["\']?',
                r'\1=REMOVED_FOR_SECURITY',
                content
            )
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print_success(f"清理：{file_path}")
                sanitized_count += 1
            else:
                print(f"  无需清理：{file_path}")
        
        except Exception as e:
            print_error(f"清理失败 {file_path}: {e}")
    
    print_success(f"已清理 {sanitized_count} 个文件")


def verify_migration(storage: SecureWalletStorage):
    """验证迁移结果"""
    print_header("步骤 5: 验证迁移")
    
    try:
        # 列出钱包
        wallets = storage.list_wallets()
        
        if not wallets:
            print_error("钱包列表为空！")
            return False
        
        print_success(f"加密存储包含 {len(wallets)} 个钱包:")
        for wallet in wallets:
            print(f"  - {wallet['name']} ({wallet['blockchain']})")
        
        # 测试解密
        print("\n🧪 测试解密...")
        test_wallet = wallets[0]
        decrypted = storage.get_wallet(test_wallet['name'])
        
        if decrypted['private_key']:
            print_success(f"解密成功：{test_wallet['name']}")
            print(f"  私钥：{decrypted['private_key'][:20]}...")
            return True
        else:
            print_error("解密失败")
            return False
    
    except Exception as e:
        print_error(f"验证失败：{e}")
        return False


def print_security_tips():
    """打印安全提示"""
    print_header("🔐 安全提示")
    
    tips = """
1. 密码管理
   ✅ 密码已保存到环境变量（本次会话）
   ✅ 建议将密码保存到密码管理器（1Password/Bitwarden）
   ✅ 或打印纸质备份，存放在保险箱
   ❌ 不要告诉任何人你的密码
   ❌ 不要使用相同密码

2. 备份策略
   ✅ 加密钱包文件：~/.ziwei/secure_wallets.json
   ✅ 盐值文件：~/.ziwei/wallet_salt
   ✅ 备份位置：{backup_dir}
   ✅ 建议：3-2-1 备份原则（3 份，2 种介质，1 份异地）

3. 文件权限
   ✅ 已设置 600 权限（仅所有者可读写）
   ✅ 定期检查权限

4. 下一步
   ✅ 更新交易机器人使用加密钱包
   ✅ 删除其他明文备份
   ✅ 定期轮换密码
   ✅ 考虑使用硬件钱包（大额资金）

5. 紧急恢复
   如果忘记密码：
   ❌ 无法恢复私钥
   ❌ 无法访问资金
   ✅ 所以一定要备份密码！
    """.format(backup_dir=BACKUP_DIR)
    
    print(tips)


# =============================================================================
# 主函数
# =============================================================================

def main():
    """主函数"""
    print_header("🔐 紫微智控 - 钱包安全迁移工具")
    
    print("此工具将帮助您：")
    print("  1. 扫描所有包含私钥的文件")
    print("  2. 创建加密钱包存储")
    print("  3. 备份原始文件")
    print("  4. 清理敏感信息")
    print("  5. 验证迁移结果")
    print("\n⚠️  警告：此操作不可逆！请确保已备份！\n")
    
    confirm = input("确认继续？(yes/no): ")
    if confirm.lower() != 'yes':
        print_warning("已取消")
        return
    
    # 步骤 1: 获取密码
    print_header("准备步骤：设置加密密码")
    password = get_encryption_password()
    print_success("密码已设置")
    
    # 步骤 2: 扫描文件
    wallet_files = scan_wallet_files()
    if not wallet_files:
        print_error("未找到钱包文件，无法迁移")
        return
    
    # 步骤 3: 提取私钥
    print_header("提取私钥")
    all_private_keys = {}
    for file_path in wallet_files:
        keys = extract_private_keys(file_path)
        all_private_keys.update(keys)
    
    if not all_private_keys:
        print_error("未找到私钥")
        return
    
    print_success(f"共找到 {len(all_private_keys)} 个私钥")
    
    # 步骤 4: 创建加密存储
    storage = create_encrypted_storage(all_private_keys, password)
    if not storage:
        print_error("创建加密存储失败")
        return
    
    # 步骤 5: 备份原始文件
    backup_original_files(wallet_files)
    
    # 步骤 6: 清理敏感信息
    sanitize_files(wallet_files)
    
    # 步骤 7: 验证迁移
    if not verify_migration(storage):
        print_error("迁移验证失败！")
        print_warning("请检查备份文件")
        return
    
    # 步骤 8: 打印安全提示
    print_security_tips()
    
    # 完成
    print_header("🎉 迁移完成！")
    print_success("所有钱包已安全迁移到加密存储")
    print(f"\n📁 加密钱包文件：{ZIWEI_DIR / 'data' / 'secure_wallets.json'}")
    print(f"📁 备份文件：{BACKUP_DIR}")
    print(f"🔐 盐值文件：{ZIWEI_DIR / '.ziwei' / 'wallet_salt'}")
    
    print("\n✅ 下一步:")
    print("  1. 验证交易机器人能正常访问加密钱包")
    print("  2. 删除不必要的备份文件")
    print("  3. 设置定期备份")
    print("  4. 考虑使用硬件钱包（如果资金量大）")


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
