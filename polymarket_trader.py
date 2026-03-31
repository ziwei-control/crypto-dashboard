#!/usr/bin/env python3
"""
=============================================================================
🔧 Polymarket 真实交易配置器
=============================================================================

Polymarket 需要：
1. Polygon 钱包私钥（用于签名交易）
2. USDC 余额（用于下注）

配置步骤：
1. 创建/导入 Polygon 钱包
2. 充值 USDC 到 Polygon 网络
3. 获取 API Key（可选，用于订单簿）

=============================================================================
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# 配置路径
BASE_DIR = Path("/home/admin/Ziwei")
CONFIG_DIR = BASE_DIR / "config"
SECURE_DIR = Path.home() / ".ziwei" / "secure"

class PolymarketTrader:
    """Polymarket 真实交易"""
    
    def __init__(self):
        self.config_file = CONFIG_DIR / "trading_config.json"
        self.keys_file = SECURE_DIR / "polymarket_keys.json"
        
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {"platforms": {"polymarket": {}}}
    
    def save_config(self):
        """保存配置"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def check_wallet_balance(self, address: str) -> Dict:
        """检查 Polygon 钱包 USDC 余额"""
        try:
            # Polygon USDC 合约地址
            usdc_address = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
            
            # 使用 Polygon RPC 查询余额
            rpc_url = "https://polygon-rpc.com"
            
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_call",
                "params": [{
                    "to": usdc_address,
                    "data": f"0x70a08231000000000000000000000000{address[2:]}"
                }, "latest"]
            }
            
            resp = requests.post(rpc_url, json=payload, timeout=10)
            result = resp.json()
            
            if 'result' in result:
                # 解析余额（USDC 6位小数）
                balance_hex = result['result']
                balance = int(balance_hex, 16) / 1e6
                return {"balance": balance, "currency": "USDC"}
            else:
                return {"error": result.get('error', 'Unknown error')}
                
        except Exception as e:
            return {"error": str(e)}
    
    def setup_wallet(self, private_key: str) -> Dict:
        """配置钱包"""
        from eth_account import Account
        
        try:
            account = Account.from_key(private_key)
            address = account.address
            
            # 检查余额
            balance_info = self.check_wallet_balance(address)
            
            result = {
                "status": "success",
                "address": address,
                "balance": balance_info.get('balance', 0),
                "message": f"钱包配置成功: {address}"
            }
            
            if balance_info.get('balance', 0) < 10:
                result['warning'] = f"USDC余额不足 ({balance_info.get('balance', 0):.2f})，建议充值至少10 USDC"
            
            return result
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def place_order(self, market_id: str, outcome: str, amount: float) -> Dict:
        """下单"""
        if not self.config.get('platforms', {}).get('polymarket', {}).get('enabled'):
            return {"status": "error", "message": "Polymarket交易未启用"}
        
        # TODO: 实现真实下单逻辑
        # 需要 py_clob_client 库
        
        return {
            "status": "simulated",
            "market_id": market_id,
            "outcome": outcome,
            "amount": amount,
            "message": "模拟下单成功（真实交易需要配置私钥）"
        }
    
    def get_markets(self) -> list:
        """获取市场列表"""
        try:
            resp = requests.get(
                "https://gamma-api.polymarket.com/markets?limit=20&active=true",
                timeout=10
            )
            return resp.json()
        except Exception as e:
            print(f"获取市场失败: {e}")
            return []


def main():
    print("="*60)
    print("🔧 Polymarket 真实交易配置")
    print("="*60)
    
    trader = PolymarketTrader()
    
    print("\n📋 配置步骤：")
    print("1. 准备 Polygon 钱包私钥")
    print("2. 充值 USDC 到 Polygon 网络")
    print("3. 运行配置命令")
    
    print("\n💰 推荐充值金额：")
    print("- 测试：10-50 USDC")
    print("- 正式：100-500 USDC")
    
    print("\n⚠️ 重要提醒：")
    print("- 私钥只存在本地，绝不上传服务器")
    print("- 建议使用专用钱包，不要用主钱包")
    print("- 只投入你能承受损失的资金")
    
    print("\n📝 配置命令：")
    print('```')
    print('python3 polymarket_trader.py --setup')
    print('python3 polymarket_trader.py --check-balance <地址>')
    print('python3 polymarket_trader.py --enable')
    print('```')


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Polymarket交易配置")
    parser.add_argument("--setup", action="store_true", help="配置钱包")
    parser.add_argument("--check-balance", type=str, help="检查钱包余额")
    parser.add_argument("--enable", action="store_true", help="启用交易")
    parser.add_argument("--disable", action="store_true", help="禁用交易")
    parser.add_argument("--markets", action="store_true", help="获取市场列表")
    
    args = parser.parse_args()
    
    trader = PolymarketTrader()
    
    if args.check_balance:
        print(f"\n检查地址: {args.check_balance}")
        result = trader.check_wallet_balance(args.check_balance)
        print(f"余额: {result}")
    
    elif args.enable:
        trader.config['platforms']['polymarket']['enabled'] = True
        trader.config['trading_enabled'] = True
        trader.config['dry_run'] = False
        trader.save_config()
        print("\n✅ Polymarket交易已启用")
    
    elif args.disable:
        trader.config['platforms']['polymarket']['enabled'] = False
        trader.config['trading_enabled'] = False
        trader.config['dry_run'] = True
        trader.save_config()
        print("\n⏸️ Polymarket交易已禁用")
    
    elif args.markets:
        print("\n📊 热门市场：")
        markets = trader.get_markets()
        for m in markets[:10]:
            print(f"  • {m.get('question', '')[:50]}...")
    
    else:
        main()