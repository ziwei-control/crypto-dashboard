#!/usr/bin/env python3
"""
自动止盈止损监控系统
功能：
1. 监控 Binance 持仓
2. 检测价格触发止盈/止损
3. 自动执行卖出
4. 发送通知
"""

import os
import sys
import json
import time
import hmac
import hashlib
import requests
from datetime import datetime
from pathlib import Path

# 配置 - 从加密存储获取
def get_binance_keys():
    """从加密存储获取 Binance API Key"""
    password = os.getenv('ZIWEI_KEY_PASSWORD')
    if not password:
        raise ValueError("请设置 ZIWEI_KEY_PASSWORD 环境变量")
    
    try:
        import sys
        sys.path.insert(0, '/home/admin/Ziwei/scripts')
        from secure_key_storage import SecureKeyStorage
        
        storage = SecureKeyStorage()
        api_key = storage.get_key('BINANCE_API_KEY', 'binance')
        api_secret = storage.get_key('BINANCE_API_SECRET', 'binance')
        return api_key, api_secret
    except Exception as e:
        raise ValueError(f"无法获取 API Key: {e}")

API_KEY, API_SECRET = None, None  # 延迟加载
BASE_URL = "https://api.binance.com"

# 止盈止损配置
DEFAULT_STOP_LOSS = 0.03      # 止损 3%
DEFAULT_TAKE_PROFIT = 0.10    # 止盈 10%
CHECK_INTERVAL = 30           # 检查间隔（秒）

# 数据存储
DATA_DIR = Path("/home/admin/Ziwei/data/trading")
DATA_DIR.mkdir(parents=True, exist_ok=True)
POSITIONS_FILE = DATA_DIR / "active_positions.json"
TRADES_FILE = DATA_DIR / "trade_history.jsonl"

class AutoStopLoss:
    def __init__(self):
        self.positions = self.load_positions()
    
    def load_positions(self):
        """加载持仓数据"""
        if POSITIONS_FILE.exists():
            with open(POSITIONS_FILE) as f:
                return json.load(f)
        return {}
    
    def save_positions(self):
        """保存持仓数据"""
        with open(POSITIONS_FILE, 'w') as f:
            json.dump(self.positions, f, indent=2, ensure_ascii=False)
    
    def sign_request(self, params):
        """签名请求"""
        query_string = '&'.join(f"{k}={v}" for k, v in params.items())
        signature = hmac.new(
            API_SECRET.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return query_string + f"&signature={signature}"
    
    def api_request(self, method, endpoint, params=None, signed=False):
        """API 请求"""
        url = f"{BASE_URL}{endpoint}"
        headers = {"X-MBX-APIKEY": API_KEY}
        
        if params is None:
            params = {}
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['recvWindow'] = 5000
            query = self.sign_request(params)
            url = f"{url}?{query}"
        else:
            if params:
                url = f"{url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        
        try:
            if method == "GET":
                resp = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                resp = requests.post(url, headers=headers, timeout=10)
            else:
                return None
            
            return resp.json()
        except Exception as e:
            print(f"API 错误: {e}")
            return None
    
    def get_current_price(self, symbol):
        """获取当前价格"""
        data = self.api_request("GET", "/api/v3/ticker/price", {"symbol": f"{symbol}USDT"})
        if data and 'price' in data:
            return float(data['price'])
        return None
    
    def get_balance(self, asset):
        """获取余额"""
        data = self.api_request("GET", "/api/v3/account", signed=True)
        if data and 'balances' in data:
            for b in data['balances']:
                if b['asset'] == asset:
                    return float(b['free']) + float(b['locked'])
        return 0
    
    def place_sell_order(self, symbol, quantity):
        """下卖单"""
        print(f"\n🔥 执行卖出: {symbol} x {quantity}")
        
        params = {
            "symbol": f"{symbol}USDT",
            "side": "SELL",
            "type": "MARKET",
            "quantity": quantity,
        }
        
        result = self.api_request("POST", "/api/v3/order", params, signed=True)
        
        if result and 'orderId' in result:
            print(f"✅ 卖出成功: {result['orderId']}")
            return result
        else:
            print(f"❌ 卖出失败: {result}")
            return None
    
    def add_position(self, symbol, entry_price, quantity, stop_loss=None, take_profit=None):
        """添加持仓监控"""
        stop_loss = stop_loss or (entry_price * (1 - DEFAULT_STOP_LOSS))
        take_profit = take_profit or (entry_price * (1 + DEFAULT_TAKE_PROFIT))
        
        self.positions[symbol] = {
            'entry_price': entry_price,
            'quantity': quantity,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'added_at': datetime.now().isoformat(),
            'status': 'active',
        }
        
        self.save_positions()
        
        print(f"""
📊 添加持仓监控:
   币种: {symbol}
   入场价: ${entry_price:.6f}
   数量: {quantity}
   止损价: ${stop_loss:.6f} (-{(stop_loss/entry_price-1)*100:.1f}%)
   止盈价: ${take_profit:.6f} (+{(take_profit/entry_price-1)*100:.1f}%)
""")
    
    def remove_position(self, symbol):
        """移除持仓监控"""
        if symbol in self.positions:
            del self.positions[symbol]
            self.save_positions()
    
    def check_positions(self):
        """检查所有持仓"""
        print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} 检查持仓...")
        
        for symbol, pos in list(self.positions.items()):
            if pos['status'] != 'active':
                continue
            
            current_price = self.get_current_price(symbol)
            if not current_price:
                continue
            
            entry = pos['entry_price']
            stop_loss = pos['stop_loss']
            take_profit = pos['take_profit']
            quantity = pos['quantity']
            
            pnl_pct = (current_price / entry - 1) * 100
            
            print(f"  {symbol}: ${current_price:.6f} | PnL: {pnl_pct:+.2f}% | 止损: ${stop_loss:.6f} | 止盈: ${take_profit:.6f}")
            
            # 检查止损
            if current_price <= stop_loss:
                print(f"\n🚨 触发止损! {symbol}")
                result = self.place_sell_order(symbol, quantity)
                
                if result:
                    pos['status'] = 'stopped_out'
                    pos['exit_price'] = current_price
                    pos['exit_time'] = datetime.now().isoformat()
                    pos['exit_reason'] = 'stop_loss'
                    self.save_positions()
                    self.log_trade(pos, 'STOP_LOSS')
            
            # 检查止盈
            elif current_price >= take_profit:
                print(f"\n🎉 触发止盈! {symbol}")
                result = self.place_sell_order(symbol, quantity)
                
                if result:
                    pos['status'] = 'took_profit'
                    pos['exit_price'] = current_price
                    pos['exit_time'] = datetime.now().isoformat()
                    pos['exit_reason'] = 'take_profit'
                    self.save_positions()
                    self.log_trade(pos, 'TAKE_PROFIT')
    
    def log_trade(self, position, reason):
        """记录交易"""
        trade = {
            'time': datetime.now().isoformat(),
            'symbol': position.get('symbol', ''),
            'entry_price': position['entry_price'],
            'exit_price': position.get('exit_price', 0),
            'quantity': position['quantity'],
            'reason': reason,
            'pnl_pct': (position.get('exit_price', 0) / position['entry_price'] - 1) * 100,
        }
        
        with open(TRADES_FILE, 'a') as f:
            f.write(json.dumps(trade, ensure_ascii=False) + '\n')
    
    def run(self):
        """运行监控"""
        print("=" * 60)
        print("🛡️ 自动止盈止损监控系统启动")
        print("=" * 60)
        print(f"检查间隔: {CHECK_INTERVAL}秒")
        print(f"默认止损: {DEFAULT_STOP_LOSS*100}%")
        print(f"默认止盈: {DEFAULT_TAKE_PROFIT*100}%")
        print(f"监控持仓: {len(self.positions)} 个")
        
        while True:
            try:
                self.check_positions()
                time.sleep(CHECK_INTERVAL)
            except KeyboardInterrupt:
                print("\n👋 停止监控")
                break
            except Exception as e:
                print(f"错误: {e}")
                time.sleep(5)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="自动止盈止损系统")
    parser.add_argument("--run", action="store_true", help="启动监控")
    parser.add_argument("--add", nargs=4, metavar=("SYMBOL", "PRICE", "QTY", "STOP_LOSS"), help="添加持仓")
    parser.add_argument("--remove", metavar="SYMBOL", help="移除持仓")
    parser.add_argument("--list", action="store_true", help="列出持仓")
    parser.add_argument("--status", action="store_true", help="查看状态")
    
    args = parser.parse_args()
    
    system = AutoStopLoss()
    
    if args.run:
        system.run()
    
    elif args.add:
        symbol, price, qty, stop_loss = args.add
        system.add_position(
            symbol.upper(),
            float(price),
            float(qty),
            float(stop_loss) if stop_loss != "0" else None
        )
    
    elif args.remove:
        system.remove_position(args.remove.upper())
        print(f"✅ 已移除 {args.remove}")
    
    elif args.list:
        if system.positions:
            print("\n📊 当前监控持仓:")
            for sym, pos in system.positions.items():
                print(f"  {sym}: {pos['quantity']} @ ${pos['entry_price']:.6f}")
        else:
            print("\n暂无监控持仓")
    
    elif args.status:
        print(f"\n监控持仓: {len(system.positions)} 个")
        for sym, pos in system.positions.items():
            current_price = system.get_current_price(sym)
            if current_price:
                pnl = (current_price / pos['entry_price'] - 1) * 100
                status = pos['status']
                print(f"  {sym}: ${current_price:.6f} ({pnl:+.2f}%) [{status}]")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()