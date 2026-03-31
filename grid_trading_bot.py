#!/usr/bin/env python3
"""
网格交易机器人
自动在价格区间内低买高卖
"""

import hashlib
import hmac
import requests
import time
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
import sys
sys.path.insert(0, '/home/admin/Ziwei/scripts')
from secure_key_storage import SecureKeyStorage

class GridTradingBot:
    def __init__(self, symbol: str, grid_count: int = 10, 
                 upper_price: float = None, lower_price: float = None,
                 total_investment: float = 10):
        """
        初始化网格交易
        
        Args:
            symbol: 交易对，如 'SOLUSDT'
            grid_count: 网格数量
            upper_price: 上限价格
            lower_price: 下限价格
            total_investment: 总投资金额(USDT)
        """
        self.symbol = symbol
        self.grid_count = grid_count
        self.total_investment = total_investment
        
        # 获取API密钥
        storage = SecureKeyStorage()
        self.api_key = storage.get_key('BINANCE_API_KEY', 'binance')
        self.api_secret = storage.get_key('BINANCE_API_SECRET', 'binance')
        
        self.base_url = "https://api.binance.com"
        
        # 获取当前价格
        self.current_price = self._get_price()
        
        # 设置价格区间（默认当前价格±5%）
        if upper_price is None:
            self.upper_price = self.current_price * 1.05
        else:
            self.upper_price = upper_price
            
        if lower_price is None:
            self.lower_price = self.current_price * 0.95
        else:
            self.lower_price = lower_price
        
        # 计算网格
        self.grid_size = (self.upper_price - self.lower_price) / grid_count
        self.order_amount = total_investment / grid_count
        
        # 状态文件
        self.state_file = Path(f"/home/admin/Ziwei/data/grid_{symbol}.json")
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📊 网格交易配置:")
        print(f"  交易对: {symbol}")
        print(f"  当前价格: ${self.current_price:.4f}")
        print(f"  价格区间: ${self.lower_price:.4f} - ${self.upper_price:.4f}")
        print(f"  网格数量: {grid_count}")
        print(f"  网格间距: ${self.grid_size:.4f} ({self.grid_size/self.current_price*100:.2f}%)")
        print(f"  每格金额: ${self.order_amount:.2f}")
        print(f"  总投资: ${total_investment:.2f}")
        
    def _get_price(self) -> float:
        """获取当前价格"""
        resp = requests.get(f"{self.base_url}/api/v3/ticker/price?symbol={self.symbol}")
        return float(resp.json()['price'])
    
    def _sign_request(self, params: dict) -> dict:
        """签名请求"""
        params['timestamp'] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode(), 
            query_string.encode(), 
            hashlib.sha256
        ).hexdigest()
        params['signature'] = signature
        return params
    
    def _request(self, method: str, endpoint: str, params: dict = None, signed: bool = True):
        """发送请求"""
        url = f"{self.base_url}{endpoint}"
        headers = {'X-MBX-APIKEY': self.api_key}
        
        if signed and params:
            params = self._sign_request(params)
        
        if method == 'GET':
            resp = requests.get(url, params=params, headers=headers)
        else:
            resp = requests.post(url, params=params, headers=headers)
        
        return resp.json()
    
    def get_balance(self, asset: str) -> float:
        """获取余额"""
        data = self._request('GET', '/api/v3/account')
        for balance in data.get('balances', []):
            if balance['asset'] == asset:
                return float(balance['free'])
        return 0
    
    def place_order(self, side: str, quantity: float, price: float = None, order_type: str = 'LIMIT'):
        """下单"""
        params = {
            'symbol': self.symbol,
            'side': side,
            'type': order_type,
        }
        
        if order_type == 'LIMIT':
            params['timeInForce'] = 'GTC'
            params['quantity'] = quantity
            params['price'] = f"{price:.4f}"
        else:
            params['quantity'] = quantity
        
        print(f"  📝 下单: {side} {quantity:.6f} @ ${price:.4f if price else 0}")
        return self._request('POST', '/api/v3/order', params)
    
    def get_open_orders(self):
        """获取未成交订单"""
        return self._request('GET', '/api/v3/openOrders', {'symbol': self.symbol})
    
    def cancel_all_orders(self):
        """取消所有订单"""
        return self._request('DELETE', '/api/v3/openOrders', {'symbol': self.symbol})
    
    def calculate_grid_levels(self):
        """计算网格价格水平"""
        levels = []
        for i in range(self.grid_count + 1):
            price = self.lower_price + (i * self.grid_size)
            levels.append(round(price, 4))
        return levels
    
    def start(self, dry_run: bool = True):
        """启动网格交易"""
        print(f"\n🚀 启动网格交易 {'(模拟)' if dry_run else '(实盘)'}")
        
        # 获取余额
        base_asset = self.symbol.replace('USDT', '')
        usdt_balance = self.get_balance('USDT')
        base_balance = self.get_balance(base_asset)
        
        print(f"\n💰 当前余额:")
        print(f"  USDT: ${usdt_balance:.2f}")
        print(f"  {base_asset}: {base_balance:.6f} (≈${base_balance * self.current_price:.2f})")
        
        if not dry_run:
            # 取消所有现有订单
            print("\n🗑️ 取消现有订单...")
            self.cancel_all_orders()
        
        # 计算网格
        levels = self.calculate_grid_levels()
        print(f"\n📊 网格价格水平:")
        for i, price in enumerate(levels):
            marker = " ← 当前" if abs(price - self.current_price) < self.grid_size/2 else ""
            print(f"  {i+1}. ${price:.4f}{marker}")
        
        # 下网格订单
        print(f"\n📝 下网格订单...")
        orders_placed = 0
        
        for i, price in enumerate(levels):
            if price < self.current_price:
                # 低于当前价，挂买单
                side = 'BUY'
                quantity = self.order_amount / price
            else:
                # 高于当前价，挂卖单
                side = 'SELL'
                quantity = self.order_amount / self.current_price
            
            if dry_run:
                print(f"  [模拟] {side} {quantity:.6f} @ ${price:.4f}")
                orders_placed += 1
            else:
                result = self.place_order(side, quantity, price)
                if 'orderId' in result:
                    orders_placed += 1
                    print(f"  ✅ 订单已下: {result['orderId']}")
                else:
                    print(f"  ❌ 下单失败: {result}")
        
        print(f"\n✅ 已下 {orders_placed} 个网格订单")
        
        # 保存状态
        state = {
            'symbol': self.symbol,
            'grid_count': self.grid_count,
            'upper_price': self.upper_price,
            'lower_price': self.lower_price,
            'total_investment': self.total_investment,
            'started_at': datetime.now().isoformat(),
            'orders_placed': orders_placed,
            'dry_run': dry_run
        }
        self.state_file.write_text(json.dumps(state, indent=2))
        
        return orders_placed
    
    def monitor(self):
        """监控网格状态"""
        print(f"\n📊 网格状态监控")
        print("=" * 50)
        
        # 获取当前价格
        current_price = self._get_price()
        print(f"当前价格: ${current_price:.4f}")
        
        # 获取未成交订单
        orders = self.get_open_orders()
        print(f"未成交订单: {len(orders)}")
        
        # 分析订单分布
        buy_orders = [o for o in orders if o['side'] == 'BUY']
        sell_orders = [o for o in orders if o['side'] == 'SELL']
        print(f"  买单: {len(buy_orders)}")
        print(f"  卖单: {len(sell_orders)}")
        
        # 计算预估收益
        if buy_orders:
            avg_buy = sum(float(o['price']) for o in buy_orders) / len(buy_orders)
            print(f"  平均买入价: ${avg_buy:.4f}")
        if sell_orders:
            avg_sell = sum(float(o['price']) for o in sell_orders) / len(sell_orders)
            print(f"  平均卖出价: ${avg_sell:.4f}")
        
        return orders

def main():
    import argparse
    parser = argparse.ArgumentParser(description='网格交易机器人')
    parser.add_argument('--symbol', default='ORDIUSDT', help='交易对')
    parser.add_argument('--grids', type=int, default=10, help='网格数量')
    parser.add_argument('--investment', type=float, default=10, help='总投资金额(USDT)')
    parser.add_argument('--upper', type=float, help='价格上限')
    parser.add_argument('--lower', type=float, help='价格下限')
    parser.add_argument('--start', action='store_true', help='启动网格')
    parser.add_argument('--monitor', action='store_true', help='监控状态')
    parser.add_argument('--live', action='store_true', help='实盘模式(默认模拟)')
    
    args = parser.parse_args()
    
    bot = GridTradingBot(
        symbol=args.symbol,
        grid_count=args.grids,
        upper_price=args.upper,
        lower_price=args.lower,
        total_investment=args.investment
    )
    
    if args.start:
        bot.start(dry_run=not args.live)
    elif args.monitor:
        bot.monitor()
    else:
        print("\n使用方法:")
        print("  模拟启动: python3 grid_trading_bot.py --symbol ORDIUSDT --start")
        print("  实盘启动: python3 grid_trading_bot.py --symbol ORDIUSDT --start --live")
        print("  监控状态: python3 grid_trading_bot.py --symbol ORDIUSDT --monitor")

if __name__ == '__main__':
    main()
