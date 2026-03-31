#!/usr/bin/env python3
"""
持仓监控器
实时监控持仓，触发止盈止损提醒
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path

POSITION_FILE = Path("/home/admin/Ziwei/data/position.json")
BINANCE_API = "https://api.binance.com"

def get_current_price(symbol: str) -> float:
    """获取当前价格"""
    try:
        resp = requests.get(f"{BINANCE_API}/api/v3/ticker/price?symbol={symbol}USDT")
        if resp.status_code == 200:
            return float(resp.json()['price'])
    except:
        pass
    return 0.0

def load_position() -> dict:
    """加载持仓"""
    try:
        with open(POSITION_FILE) as f:
            return json.load(f)
    except:
        return None

def check_position():
    """检查持仓"""
    position = load_position()
    
    if not position:
        print("📍 无持仓")
        return
    
    symbol = position['symbol']
    quantity = position['quantity']
    entry_price = position['entry_price']
    take_profit = position['take_profit']
    stop_loss = position['stop_loss']
    
    current_price = get_current_price(symbol)
    
    if current_price <= 0:
        print("❌ 无法获取价格")
        return
    
    # 计算 PnL
    pnl_pct = (current_price / entry_price - 1) * 100
    pnl_usd = (current_price - entry_price) * quantity
    
    print("\n" + "=" * 70)
    print(f"📊 {symbol} 持仓监控")
    print("=" * 70)
    print(f"  入场价: ${entry_price:.2f}")
    print(f"  当前价: ${current_price:.2f}")
    print(f"  数量: {quantity:.6f}")
    print(f"  PnL: {pnl_pct:+.2f}% (${pnl_usd:+.2f})")
    print(f"\n  止盈: ${take_profit:.2f} (+{(take_profit/entry_price-1)*100:.0f}%)")
    print(f"  止损: ${stop_loss:.2f} ({(stop_loss/entry_price-1)*100:.0f}%)")
    
    # 检查止盈止损
    if current_price >= take_profit:
        print("\n" + "💰" * 35)
        print("💰 触发止盈！建议卖出锁定利润")
        print(f"💰 当前价格 ${current_price:.2f} >= 止盈价 ${take_profit:.2f}")
        print("💰" * 35)
    elif current_price <= stop_loss:
        print("\n" + "🚨" * 35)
        print("🚨 触发止损！建议立即卖出")
        print(f"🚨 当前价格 ${current_price:.2f} <= 止损价 ${stop_loss:.2f}")
        print("🚨" * 35)
    elif current_price <= entry_price * 0.97:
        print("\n⚠️ 接近止损线，请密切关注")
    elif current_price >= entry_price * 1.08:
        print("\n📈 接近止盈目标，准备卖出")
    
    print("=" * 70)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="持仓监控器")
    parser.add_argument("--watch", action="store_true", help="持续监控")
    parser.add_argument("--interval", type=int, default=60, help="监控间隔(秒)")
    
    args = parser.parse_args()
    
    if args.watch:
        print("🔄 开始持续监控...")
        while True:
            check_position()
            time.sleep(args.interval)
    else:
        check_position()

if __name__ == "__main__":
    main()