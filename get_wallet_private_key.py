#!/usr/bin/env python3
"""
安全私钥获取工具
规则：只有输入正确密码才能获得私钥，没有其他方式
"""

import sys
import os
sys.path.insert(0, '/home/admin/Ziwei/scripts')

def get_private_key():
    """获取私钥 - 必须输入密码"""
    print("=" * 60)
    print("🔐 安全私钥获取")
    print("=" * 60)
    print()
    print("⚠️  只有输入正确的解密密码才能获得私钥")
    print("⚠️  没有其他任何方式")
    print()
    
    # 必须手动输入密码，不接受环境变量
    password = input("请输入解密密码: ")
    
    if not password:
        print("❌ 密码不能为空")
        return
    
    # 验证密码
    from secure_wallet_storage import SecureWalletStorage
    
    try:
        storage = SecureWalletStorage(
            encryption_password=password,
            storage_path="/home/admin/Ziwei/data/secure/solana_wallets.json"
        )
        
        # 列出可用钱包
        wallets = storage.list_wallets()
        if not wallets:
            print("❌ 没有找到钱包")
            return
        
        print()
        print("可用钱包:")
        for i, w in enumerate(wallets, 1):
            print(f"  {i}. {w['name']} ({w['blockchain']})")
        
        print()
        choice = input("选择钱包编号 (1-{0}): ".format(len(wallets)))
        
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(wallets):
                print("❌ 无效选择")
                return
            
            wallet_name = wallets[idx]['name']
            
            # 解密并显示私钥
            wallet = storage.get_wallet(wallet_name)
            
            print()
            print("=" * 60)
            print(f"🔑 钱包: {wallet_name}")
            print("=" * 60)
            print()
            print("私钥 (Base58):")
            print(wallet['private_key'])
            print()
            print("⚠️  请安全保存，不要泄露给任何人")
            print("=" * 60)
            
        except ValueError:
            print("❌ 请输入数字")
            
    except Exception as e:
        print()
        print("❌ 密码错误或解密失败")
        print("   只有正确的密码才能获得私钥")

if __name__ == "__main__":
    get_private_key()
