#!/usr/bin/env python3
"""
领先信号监控器 - 实时版
整合所有免费的领先信号

运行方式：python3 alpha_monitor.py
或后台运行：nohup python3 alpha_monitor.py > alpha_signals.log 2>&1 &
"""

import json
import time
import requests
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("/home/admin/Ziwei/data/alpha_signals")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 阈值配置
FUNDING_THRESHOLD = 0.03  # 资金费率阈值（%）
ORDERBOOK_THRESHOLD = 0.2  # 订单簿不平衡阈值（20%）

# 历史数据用于检测变化
history = {
    'funding': {},
    'orderbook': {},
    'alerts': []
}

def get_funding_rate(symbol):
    """获取资金费率"""
    try:
        url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit=1"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if data:
            return float(data[0]['fundingRate']) * 100
    except:
        pass
    return None

def get_orderbook_imbalance(symbol):
    """获取订单簿不平衡"""
    try:
        url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=20"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        
        bids = data.get('bids', [])
        asks = data.get('asks', [])
        
        if not bids or not asks:
            return None
        
        total_bid = sum(float(b[0]) * float(b[1]) for b in bids)
        total_ask = sum(float(a[0]) * float(a[1]) for a in asks)
        
        return (total_bid - total_ask) / (total_bid + total_ask)
    except:
        pass
    return None

def get_price(symbol):
    """获取当前价格"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        resp = requests.get(url, timeout=5)
        return float(resp.json()['price'])
    except:
        pass
    return None

def check_signals():
    """检查所有信号"""
    signals = []
    
    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']
    
    for symbol in symbols:
        # 资金费率
        funding = get_funding_rate(symbol)
        price = get_price(symbol)
        
        if funding is not None:
            if funding > FUNDING_THRESHOLD:
                signals.append({
                    'type': 'FUNDING',
                    'symbol': symbol,
                    'signal': 'SHORT',
                    'value': funding,
                    'message': f'🔴 {symbol} 资金费率 {funding:+.4f}% → 市场过度看多 → 考虑做空',
                    'strength': abs(funding) / FUNDING_THRESHOLD
                })
            elif funding < -FUNDING_THRESHOLD:
                signals.append({
                    'type': 'FUNDING',
                    'symbol': symbol,
                    'signal': 'LONG',
                    'value': funding,
                    'message': f'🟢 {symbol} 资金费率 {funding:+.4f}% → 市场过度看空 → 考虑做多',
                    'strength': abs(funding) / FUNDING_THRESHOLD
                })
        
        # 订单簿不平衡
        imbalance = get_orderbook_imbalance(symbol)
        
        if imbalance is not None:
            if imbalance > ORDERBOOK_THRESHOLD:
                signals.append({
                    'type': 'ORDERBOOK',
                    'symbol': symbol,
                    'signal': 'LONG',
                    'value': imbalance,
                    'message': f'🟢 {symbol} 买盘强于卖盘 {imbalance:+.1%} → 可能上涨',
                    'strength': abs(imbalance) / ORDERBOOK_THRESHOLD
                })
            elif imbalance < -ORDERBOOK_THRESHOLD:
                signals.append({
                    'type': 'ORDERBOOK',
                    'symbol': symbol,
                    'signal': 'SHORT',
                    'value': imbalance,
                    'message': f'🔴 {symbol} 卖盘强于买盘 {imbalance:+.1%} → 可能下跌',
                    'strength': abs(imbalance) / ORDERBOOK_THRESHOLD
                })
    
    return signals, price

def format_signal(signal):
    """格式化信号输出"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    return f"[{timestamp}] {signal['message']}"

def run_monitor(interval_seconds=60):
    """运行监控"""
    print("=" * 60)
    print("🚀 领先信号监控器")
    print("=" * 60)
    print(f"刷新间隔: {interval_seconds}秒")
    print(f"资金费率阈值: ±{FUNDING_THRESHOLD}%")
    print(f"订单簿阈值: ±{ORDERBOOK_THRESHOLD*100:.0f}%")
    print("=" * 60)
    print("按 Ctrl+C 停止\n")
    
    while True:
        try:
            signals, _ = check_signals()
            
            # 清屏效果
            print("\033[2J\033[H", end="")
            
            print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 60)
            
            if signals:
                print(f"📊 发现 {len(signals)} 个信号:\n")
                for s in signals:
                    print(f"  {s['message']}")
                    print(f"    类型: {s['type']} | 方向: {s['signal']} | 强度: {s['strength']:.1f}x\n")
                
                # 保存信号
                with open(DATA_DIR / 'latest_signals.json', 'w') as f:
                    json.dump({
                        'timestamp': datetime.now().isoformat(),
                        'signals': signals
                    }, f, indent=2)
            else:
                print("⚪ 当前无极端信号")
                print("   市场处于相对平衡状态")
            
            print("\n" + "-" * 60)
            print("按 Ctrl+C 停止监控")
            
            time.sleep(interval_seconds)
            
        except KeyboardInterrupt:
            print("\n\n监控已停止")
            break
        except Exception as e:
            print(f"错误: {e}")
            time.sleep(10)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'once':
        # 单次检查
        signals, _ = check_signals()
        if signals:
            for s in signals:
                print(format_signal(s))
        else:
            print("当前无极端信号")
    else:
        # 持续监控
        interval = int(sys.argv[1]) if len(sys.argv) > 1 else 60
        run_monitor(interval)