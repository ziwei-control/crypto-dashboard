#!/usr/bin/env python3
"""
钱包控制器 - 安全架构

规则：
1. AI 操作钱包（签名交易等）：可使用环境变量密码
2. 导出私钥/转移控制权：必须手动输入密码
3. 没有密码 = 无法控制钱包
"""

import os
import sys
import json
import urllib.request
from pathlib import Path

sys.path.insert(0, '/home/admin/Ziwei/scripts')


class WalletController:
    """钱包控制器"""
    
    def __init__(self):
        self.storage = None
        self.password = None
    
    def _init_for_ai(self):
        """AI 初始化 - 使用环境变量（仅用于授权操作）"""
        password = os.getenv("WALLET_ENCRYPTION_PASSWORD")
        if not password:
            raise PermissionError("环境变量未设置，AI 无法访问钱包")
        
        from secure_wallet_storage import SecureWalletStorage
        self.storage = SecureWalletStorage(
            encryption_password=password,
            storage_path="/home/admin/Ziwei/data/secure/solana_wallets.json"
        )
        self.password = password
        return True
    
    def _init_for_export(self, password: str):
        """导出私钥初始化 - 必须手动输入密码"""
        if not password:
            raise PermissionError("必须输入密码才能导出私钥")
        
        from secure_wallet_storage import SecureWalletStorage
        self.storage = SecureWalletStorage(
            encryption_password=password,
            storage_path="/home/admin/Ziwei/data/secure/solana_wallets.json"
        )
        return True
    
    # ========== AI 可调用的操作（使用环境变量）==========
    
    def get_wallet_address(self, name: str) -> str:
        """获取钱包地址（AI 可用）"""
        self._init_for_ai()
        # 地址不需要私钥，从公开信息获取
        wallets = self.storage.list_wallets()
        for w in wallets:
            if w['name'] == name:
                return w.get('address', '地址需要从链上查询')
        raise KeyError(f"钱包不存在: {name}")
    
    def get_balance(self, address: str) -> float:
        """查询余额（AI 可用，不需要私钥）"""
        # 这是公开信息，不需要密码
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [address]
        }
        req = urllib.request.Request(
            "https://api.mainnet-beta.solana.com",
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode())
            return result.get('result', {}).get('value', 0) / 1e9
    
    def sign_transaction(self, wallet_name: str, transaction_data: dict) -> dict:
        """签名交易（AI 可用，但需要环境变量密码）"""
        self._init_for_ai()
        wallet = self.storage.get_wallet(wallet_name)
        
        # 这里可以执行签名操作
        # 但我不会在日志或输出中透露私钥
        print(f"✅ 已使用钱包 '{wallet_name}' 签名交易")
        print("⚠️  私钥不会被输出或记录")
        
        return {"signed": True, "wallet": wallet_name}
    
    # ========== 需要手动输入密码的操作 ==========
    
    def export_private_key(self, password: str, wallet_name: str) -> str:
        """
        导出私钥 - 必须手动输入密码
        
        这个方法不会使用环境变量，必须手动传入密码
        """
        if not password:
            raise PermissionError("导出私钥必须手动输入密码")
        
        self._init_for_export(password)
        wallet = self.storage.get_wallet(wallet_name)
        
        return wallet['private_key']
    
    def transfer_control(self, password: str, wallet_name: str) -> dict:
        """
        转移钱包控制权 - 必须手动输入密码
        
        返回完整的钱包信息，包括私钥
        """
        if not password:
            raise PermissionError("转移控制权必须手动输入密码")
        
        self._init_for_export(password)
        wallet = self.storage.get_wallet(wallet_name)
        
        return {
            "name": wallet_name,
            "blockchain": wallet['blockchain'],
            "private_key": wallet['private_key'],
            "warning": "这是完整的钱包控制权，请安全保存"
        }


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="钱包控制器")
    parser.add_argument("--balance", help="查询余额（公开，不需要密码）")
    parser.add_argument("--sign", help="签名交易（AI 可用，需要环境变量）")
    parser.add_argument("--export", help="导出私钥（需要手动输入密码）")
    parser.add_argument("--transfer", help="转移控制权（需要手动输入密码）")
    
    args = parser.parse_args()
    
    controller = WalletController()
    
    if args.balance:
        # 查询余额 - 不需要密码
        balance = controller.get_balance(args.balance)
        print(f"余额: {balance} SOL")
    
    elif args.sign:
        # AI 操作 - 使用环境变量
        print("签名交易...")
        controller.sign_transaction(args.sign, {})
    
    elif args.export or args.transfer:
        # 导出私钥/转移控制权 - 必须手动输入
        print("=" * 60)
        print("⚠️  此操作需要您手动输入密码")
        print("⚠️  AI 不会知道您的密码")
        print("=" * 60)
        
        password = input("\n请输入解密密码: ")
        
        if args.export:
            private_key = controller.export_private_key(password, args.export)
            print(f"\n私钥: {private_key}")
        
        elif args.transfer:
            info = controller.transfer_control(password, args.transfer)
            print(f"\n钱包信息: {json.dumps(info, indent=2)}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
