#!/usr/bin/env python3
# =============================================================================
# 安全钱包使用示例 - 集成到交易机器人
# =============================================================================

import os
import sys

# 添加脚本目录
sys.path.insert(0, '/home/admin/Ziwei/scripts')

from secure_wallet_migration import SecureWalletStorage

# =============================================================================
# 配置
# =============================================================================

# 从环境变量获取主密码
MASTER_PASSWORD = os.getenv('WALLET_MASTER_PASSWORD')

if not MASTER_PASSWORD:
    print("❌ 错误：请设置 WALLET_MASTER_PASSWORD 环境变量")
    print("   export WALLET_MASTER_PASSWORD='你的主密码'")
    sys.exit(1)

# 创建安全存储
storage = SecureWalletStorage(
    master_password=MASTER_PASSWORD,
    storage_path='/home/admin/Ziwei/.ziwei/secure/wallets.json'
)

# =============================================================================
# 使用示例
# =============================================================================

def get_api_credentials():
    """获取 API 凭证（用于交易机器人）"""
    try:
        # 获取币安 API 密钥
        api_key_wallet = storage.get_wallet('env_API_KEY')
        api_secret_wallet = storage.get_wallet('env_API_SECRET')
        
        return {
            'api_key': api_key_wallet['private_key'],
            'api_secret': api_secret_wallet['private_key'],
            'exchange': 'binance'
        }
    except KeyError as e:
        print(f"⚠️  未找到 API 凭证：{e}")
        return None

def get_wallet_private_key(blockchain: str = "ETH"):
    """获取钱包私钥"""
    try:
        # 列出所有钱包
        wallets = storage.list_wallets()
        
        # 查找指定区块链的钱包
        for wallet in wallets:
            if wallet['blockchain'] == blockchain:
                return storage.get_wallet(wallet['name'])
        
        print(f"⚠️  未找到 {blockchain} 钱包")
        return None
    except Exception as e:
        print(f"❌ 获取私钥失败：{e}")
        return None

def list_all_wallets():
    """列出所有钱包（不显示私钥）"""
    print("\n📋 钱包列表:")
    print("-" * 60)
    
    wallets = storage.list_wallets()
    
    if not wallets:
        print("  暂无钱包")
        return
    
    for wallet in wallets:
        print(f"  名称：{wallet['name']}")
        print(f"  区块链：{wallet['blockchain']}")
        print(f"  创建时间：{wallet['created_at'][:19]}")
        print(f"  最后使用：{wallet['last_used'][:19] if wallet['last_used'] else '从未使用'}")
        print(f"  访问次数：{wallet['access_count']}")
        print("-" * 60)

# =============================================================================
# 主函数
# =============================================================================

def main():
    """主函数"""
    print("\n🔐 紫微智控 - 安全钱包使用示例\n")
    
    # 列出所有钱包
    list_all_wallets()
    
    # 获取 API 凭证
    print("\n🔑 获取 API 凭证...")
    credentials = get_api_credentials()
    
    if credentials:
        print(f"  交易所：{credentials['exchange']}")
        print(f"  API Key: {credentials['api_key'][:20]}...")
        print(f"  API Secret: {credentials['api_secret'][:20]}...")
    
    # 获取钱包私钥
    print("\n🔑 获取 ETH 钱包私钥...")
    eth_wallet = get_wallet_private_key("ETH")
    
    if eth_wallet:
        print(f"  名称：{eth_wallet['name']}")
        print(f"  私钥：{eth_wallet['private_key'][:20]}...")
    
    print("\n✅ 示例完成")
    print("\n📚 集成到交易机器人:")
    print("  1. 导入 SecureWalletStorage")
    print("  2. 使用 get_wallet() 获取私钥")
    print("  3. 不要将私钥写入日志")
    print("  4. 用完后立即从内存删除")

if __name__ == "__main__":
    main()
