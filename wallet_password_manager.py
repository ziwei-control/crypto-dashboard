#!/usr/bin/env python3
"""
钱包密码管理工具
用于安全地更改加密密码
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, '/home/admin/Ziwei/scripts')
from secure_wallet_storage import SecureWalletStorage

def change_password():
    """更改加密密码"""
    print("=" * 60)
    print("🔐 钱包密码更改工具")
    print("=" * 60)
    print()
    
    # 获取旧密码
    old_password = os.getenv("WALLET_ENCRYPTION_PASSWORD")
    if not old_password:
        old_password = input("请输入当前密码: ")
    
    # 获取新密码
    print()
    print("请输入新密码 (建议16位以上，包含大小写、数字、符号)")
    new_password = input("新密码: ")
    confirm = input("确认新密码: ")
    
    if new_password != confirm:
        print("❌ 两次密码不一致！")
        return
    
    if len(new_password) < 12:
        print("⚠️  密码太短，建议至少12位")
        proceed = input("继续吗？(y/n): ")
        if proceed.lower() != 'y':
            return
    
    # 加载钱包
    storage_path = "/home/admin/Ziwei/data/secure/solana_wallets.json"
    
    try:
        # 用旧密码解密
        old_storage = SecureWalletStorage(
            encryption_password=old_password,
            storage_path=storage_path
        )
        
        # 获取所有钱包
        wallets_data = {}
        for w in old_storage.list_wallets():
            wallet = old_storage.get_wallet(w['name'])
            wallets_data[w['name']] = {
                'private_key': wallet['private_key'],
                'blockchain': wallet['blockchain']
            }
        
        # 用新密码重新加密
        new_storage = SecureWalletStorage(
            encryption_password=new_password,
            storage_path=storage_path
        )
        
        for name, data in wallets_data.items():
            new_storage.add_wallet(name, data['private_key'], data['blockchain'])
        
        print()
        print("✅ 密码更改成功！")
        print()
        print("⚠️  请记住新密码，丢失将无法恢复钱包！")
        
        # 更新环境变量提示
        print()
        print("请更新环境变量:")
        print(f'  export WALLET_ENCRYPTION_PASSWORD="你的新密码"')
        print()
        print("并更新 ~/.bashrc 中的密码")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        print("可能是旧密码不正确")

if __name__ == "__main__":
    change_password()
