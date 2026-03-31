#!/usr/bin/env python3
# =============================================================================
# 💰 Binance 余额查询 - 使用加密密钥
# =============================================================================

import sys
sys.path.insert(0, '/home/admin/Ziwei/scripts')

import requests
import hmac
import hashlib
import time
import os
from secure_key_storage import SecureKeyStorage

def get_binance_balance():
    """获取 Binance 真实余额"""
    try:
        # 获取加密密钥
        storage = SecureKeyStorage()
        
        api_key = storage.get_key("BINANCE_API_KEY", "binance")
        api_secret = storage.get_key("BINANCE_API_SECRET", "binance")
        
        if not api_key or not api_secret:
            return {
                'success': False,
                'error': 'API密钥未配置',
                'message': '请设置ZIWEI_KEY_PASSWORD环境变量'
            }
        
        # 准备请求
        timestamp = int(time.time() * 1000)
        
        # 生成签名
        params = f'timestamp={timestamp}'
        signature = hmac.new(
            api_secret.encode('utf-8'),
            params.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # 请求余额
        url = 'https://api.binance.com/api/v3/account'
        headers = {
            'X-MBX-APIKEY': api_key
        }
        params = {
            'timestamp': timestamp,
            'signature': signature
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            balances = {}
            total_usdt = 0
            
            # 获取价格（用于计算USDT价值）
            try:
                price_url = 'https://api.binance.com/api/v3/ticker/price'
                price_response = requests.get(price_url, timeout=10)
                prices = {p['symbol']: float(p['price']) for p in price_response.json()}
            except:
                prices = {}
            
            for balance in data.get('balances', []):
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0:
                    # 计算 USDT 价值
                    if asset == 'USDT':
                        usd_value = total
                    elif f"{asset}USDT" in prices:
                        usd_value = total * prices[f"{asset}USDT"]
                    elif asset in ['BTC', 'ETH', 'BNB']:
                        # 使用预估价格
                        if asset == 'BTC':
                            usd_value = total * 85000  # 预估价格
                        elif asset == 'ETH':
                            usd_value = total * 2200
                        elif asset == 'BNB':
                            usd_value = total * 600
                        else:
                            usd_value = 0
                    else:
                        usd_value = 0
                    
                    balances[asset] = {
                        'free': free,
                        'locked': locked,
                        'total': total,
                        'usd_value': usd_value
                    }
                    total_usdt += usd_value
            
            return {
                'success': True,
                'balances': balances,
                'total_usdt': total_usdt,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            return {
                'success': False,
                'error': f'API错误：{response.status_code}',
                'message': response.text
            }
    
    except Exception as e:
        return {
            'success': False,
            'error': '查询失败',
            'message': str(e)
        }


if __name__ == '__main__':
    result = get_binance_balance()
    
    if result['success']:
        print("=" * 70)
        print("💰 Binance 真实钱包余额")
        print("=" * 70)
        print(f"查询时间：{result['timestamp']}")
        print()
        
        if result['balances']:
            for asset, data in result['balances'].items():
                print(f"{asset}:")
                print(f"  可用：{data['free']:.8f}")
                print(f"  冻结：{data['locked']:.8f}")
                print(f"  总计：{data['total']:.8f}")
                print(f"  估值：${data['usd_value']:.2f} USD")
                print()
            
            print("-" * 70)
            print(f"💎 总资产估值：${result['total_usdt']:.2f} USD")
            print("=" * 70)
        else:
            print("⚠️ 钱包余额为空")
    else:
        print(f"❌ 查询失败：{result['error']}")
        print(f"详情：{result['message']}")