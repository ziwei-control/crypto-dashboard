#!/usr/bin/env python3
"""
网格交易机器人 - ORDI
自动低买高卖，吃波动收益
"""

import hashlib
import hmac
import requests
import time
import json
from urllib.parse import urlencode
from datetime import datetime

class GridTrader:
    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.api_key = None
        self.api_secret = None
        self.symbol = "ORDIUSDT"
        self.grid_count = 10  # 网格数量
        self.grid_range = 0.08  # 8%波动范围
        
    def load_keys(self):
        """加载API密钥"""
        import sys
        sys.path.insert(0, '/home/admin/Ziwei/scripts')
        from secure_key_storage import SecureKeyStorage
        storage = SecureKeyStorage()
        self.api_key = storage.get_key('BINANCE_API_KEY', 'binance')
        self.api_secret = storage.get_key('BINANCE_API_SECRET', 'binance')
        
    def get_price(self):
        """获取当前价格"""
        resp = requests.get(f"{self.base_url}/api/v3/ticker/price?symbol={self.symbol}")
        return float(resp.json()['price'])
    
    def get_balance(self, asset='ORDI'):
        """获取余额"""
        timestamp = int(time.time() * 1000)
        params = {'timestamp': timestamp}
        query_string = urlencode(params)
        signature = hmac.new(self.api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        params['signature'] = signature
        headers = {'X-MBX-APIKEY': self.api_key}
        
        resp = requests.get(f"{self.base_url}/api/v3/account", params=params, headers=headers)
        for balance in resp.json()['balances']:
            if balance['asset'] == asset:
                return float(balance['free'])
        return 0
    
    def place_order(self, side, quantity, price, order_type='LIMIT'):
        """下单"""
        timestamp = int(time.time() * 1000)
        params = {
            'symbol': self.symbol,
            'side': side,
            'type': order_type,
            'timeInForce': 'GTC',
            'quantity': quantity,
            'price': price,
            'timestamp': timestamp
        }
        query_string = urlencode(params)
        signature = hmac.new(self.api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        params['signature'] = signature
        headers = {'X-MBX-APIKEY': self.api_key}
        
        resp = requests.post(f"{self.base_url}/api/v3/order", params=params, headers=headers)
        return resp.json()
    
    def calculate_grids(self, current_price):
        """计算网格价格"""
        upper = current_price * (1 + self.grid_range)
        lower = current_price * (1 - self.grid_range)
        step = (upper - lower) / self.grid_count
        
        grids = []
        for i in range(self.grid_count + 1):
            price = lower + step * i
            grids.append(round(price, 4))
        return grids, upper, lower
    
    def run(self):
        """运行网格交易"""
        print("="*50)
        print(f"📊 ORDI 网格交易机器人")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)
        
        self.load_keys()
        current_price = self.get_price()
        ordi_balance = self.get_balance('ORDI')
        usdt_balance = self.get_balance('USDT')
        
        print(f"\n当前价格: ${current_price:.4f}")
        print(f"ORDI余额: {ordi_balance:.4f}")
        print(f"USDT余额: ${usdt_balance:.2f}")
        
        grids, upper, lower = self.calculate_grids(current_price)
        print(f"\n网格范围: ${lower:.4f} - ${upper:.4f}")
        print(f"网格数量: {self.grid_count}")
        print(f"网格间距: {((upper-lower)/self.grid_count/current_price*100):.2f}%")
        
        print("\n📐 网格价格:")
        for i, price in enumerate(grids):
            side = "卖出" if price > current_price else "买入"
            print(f"  {i+1:2d}. ${price:.4f} ({side})")
        
        # 计算每格数量
        total_value = ordi_balance * current_price + usdt_balance
        value_per_grid = total_value / (self.grid_count + 1)
        qty_per_grid = value_per_grid / current_price
        
        print(f"\n💰 每格资金: ${value_per_grid:.2f}")
        print(f"📊 每格数量: {qty_per_grid:.4f} ORDI")
        
        # 保存配置
        config = {
            'symbol': self.symbol,
            'current_price': current_price,
            'grid_range': [lower, upper],
            'grids': grids,
            'qty_per_grid': qty_per_grid,
            'created_at': datetime.now().isoformat()
        }
        
        with open('/home/admin/Ziwei/data/grid_trading_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n✅ 配置已保存到: /home/admin/Ziwei/data/grid_trading_config.json")
        return config

if __name__ == '__main__':
    import os
    os.environ['ZIWEI_KEY_PASSWORD'] = 'mimajiushimima'
    
    trader = GridTrader()
    config = trader.run()
    
    print("\n" + "="*50)
    print("⚠️  注意: 这是模拟计算，实际下单需要开启交易权限")
    print("如需自动交易，运行: python3 grid_trading.py --live")
    print("="*50)
