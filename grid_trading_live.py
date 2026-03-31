#!/usr/bin/env python3
"""
网格交易机器人 - 实盘版本
自动在Binance下单
"""

import hashlib
import hmac
import requests
import time
import json
import os
from urllib.parse import urlencode
from datetime import datetime

class GridTraderLive:
    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.api_key = None
        self.api_secret = None
        self.symbol = "ORDIUSDT"
        
    def load_keys(self):
        import sys
        sys.path.insert(0, '/home/admin/Ziwei/scripts')
        from secure_key_storage import SecureKeyStorage
        storage = SecureKeyStorage()
        self.api_key = storage.get_key('BINANCE_API_KEY', 'binance')
        self.api_secret = storage.get_key('BINANCE_API_SECRET', 'binance')
        
    def sign(self, params):
        query_string = urlencode(params)
        signature = hmac.new(self.api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        return signature
    
    def request(self, method, endpoint, params=None):
        if params is None:
            params = {}
        params['timestamp'] = int(time.time() * 1000)
        params['signature'] = self.sign(params)
        headers = {'X-MBX-APIKEY': self.api_key}
        
        url = f"{self.base_url}{endpoint}"
        if method == 'GET':
            resp = requests.get(url, params=params, headers=headers, timeout=10)
        else:
            resp = requests.post(url, params=params, headers=headers, timeout=10)
        return resp.json()
    
    def get_price(self):
        resp = requests.get(f"{self.base_url}/api/v3/ticker/price?symbol={self.symbol}")
        return float(resp.json()['price'])
    
    def get_balance(self, asset):
        data = self.request('GET', '/api/v3/account')
        for b in data.get('balances', []):
            if b['asset'] == asset:
                return float(b['free'])
        return 0
    
    def place_order(self, side, quantity, price):
        """下限价单"""
        params = {
            'symbol': self.symbol,
            'side': side,
            'type': 'LIMIT',
            'timeInForce': 'GTC',
            'quantity': quantity,
            'price': price
        }
        return self.request('POST', '/api/v3/order', params)
    
    def place_grid_orders(self):
        """放置网格订单"""
        print("="*60)
        print(f"📊 ORDI 网格交易 - 实盘下单")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        self.load_keys()
        
        # 获取当前状态
        current_price = self.get_price()
        ordi_balance = self.get_balance('ORDI')
        usdt_balance = self.get_balance('USDT')
        
        print(f"\n当前价格: ${current_price:.4f}")
        print(f"ORDI余额: {ordi_balance:.4f}")
        print(f"USDT余额: ${usdt_balance:.2f}")
        
        # 计算网格
        grid_range = 0.08  # 8%
        grid_count = 5     # 5层（减少订单数）
        
        upper = current_price * (1 + grid_range)
        lower = current_price * (1 - grid_range)
        step = (upper - lower) / grid_count
        
        print(f"\n网格范围: ${lower:.4f} - ${upper:.4f}")
        
        # 计算每格数量
        sell_qty = round(ordi_balance / 3, 2)  # 分3批卖
        buy_qty = round(usdt_balance / 3 / current_price, 2)  # 分3批买
        
        print(f"\n卖出数量: {sell_qty} ORDI/格")
        print(f"买入数量: {buy_qty} ORDI/格")
        
        # 放置卖单（高于当前价）
        print("\n📈 放置卖单...")
        sell_prices = []
        for i in range(1, 4):
            price = round(current_price * (1 + 0.02 * i), 4)
            sell_prices.append(price)
            print(f"  卖单 {i}: {sell_qty} ORDI @ ${price}")
        
        # 放置买单（低于当前价）
        print("\n📉 放置买单...")
        buy_prices = []
        for i in range(1, 4):
            price = round(current_price * (1 - 0.02 * i), 4)
            buy_prices.append(price)
            print(f"  买单 {i}: {buy_qty} ORDI @ ${price}")
        
        # 询问确认
        print("\n" + "="*60)
        print("⚠️  即将下单，请确认:")
        print(f"   - 卖出 {sell_qty*3} ORDI")
        print(f"   - 用 ${usdt_balance:.2f} USDT 买入")
        print("="*60)
        
        return {
            'sell_qty': sell_qty,
            'buy_qty': buy_qty,
            'sell_prices': sell_prices,
            'buy_prices': buy_prices
        }

if __name__ == '__main__':
    os.environ['ZIWEI_KEY_PASSWORD'] = 'mimajiushimima'
    
    trader = GridTraderLive()
    result = trader.place_grid_orders()
    
    print("\n✅ 计算完成!")
    print("⚠️  实际下单请运行: python3 grid_trading_live.py --confirm")
