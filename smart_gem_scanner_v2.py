#!/usr/bin/env python3
"""
Smart Gem Scanner v2.1 - 完整版
结合市场动态评估 + 自动止盈止损追踪

使用方法:
  python3 smart_gem_scanner_v2.py              # 完整扫描 + 追踪更新
  python3 smart_gem_scanner_v2.py --track      # 只更新追踪
  python3 smart_gem_scanner_v2.py --market     # 只看市场状态
  python3 smart_gem_scanner_v2.py --add <addr> <price> <symbol>  # 添加追踪
"""

import json
import time
import requests
from datetime import datetime
import os
import sys

# ============== 配置 ==============
DATA_DIR = "/home/admin/Ziwei/data/smart_gem_scanner"
TRACKED_FILE = f"{DATA_DIR}/tracked_tokens.json"
os.makedirs(DATA_DIR, exist_ok=True)

# ============== 市场状态评估 ==============
def get_market_status():
    """获取市场综合状态"""
    status = {
        "time": datetime.now().isoformat(),
        "fear_greed": None,
        "fear_greed_class": None,
        "btc_price": None,
        "btc_change_24h": None,
        "sol_price": None,
        "sol_change_24h": None,
        "market_health": "unknown",
        "recommend_modifier": 1.0,
        "suggestions": []
    }
    
    try:
        # 恐惧贪婪指数
        resp = requests.get("https://api.alternative.me/fng/", timeout=10)
        fng = resp.json()['data'][0]
        status["fear_greed"] = int(fng['value'])
        status["fear_greed_class"] = fng['value_classification']
    except:
        pass
    
    try:
        # BTC 数据
        resp = requests.get("https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT", timeout=10)
        btc = resp.json()
        status["btc_price"] = float(btc['lastPrice'])
        status["btc_change_24h"] = float(btc['priceChangePercent'])
    except:
        pass
    
    try:
        # SOL 数据
        resp = requests.get("https://api.binance.com/api/v3/ticker/24hr?symbol=SOLUSDT", timeout=10)
        sol = resp.json()
        status["sol_price"] = float(sol['lastPrice'])
        status["sol_change_24h"] = float(sol['priceChangePercent'])
    except:
        pass
    
    # 计算市场健康度
    fng = status.get("fear_greed", 50)
    btc_change = status.get("btc_change_24h", 0)
    
    if fng <= 20:
        status["market_health"] = "extreme_fear"
        status["recommend_modifier"] = 0.4
        status["suggestions"] = [
            "🛑 市场极度恐惧，暂停推荐新币",
            "📉 持仓币跌超30%建议止损",
            "⏳ 等待市场企稳再入场"
        ]
    elif fng <= 40:
        status["market_health"] = "fear"
        status["recommend_modifier"] = 0.6
        status["suggestions"] = [
            "⚠️ 市场恐惧，谨慎操作",
            "🔍 筛选标准更严格",
            "💰 控制仓位，不要重仓"
        ]
    elif fng <= 60:
        status["market_health"] = "neutral"
        status["recommend_modifier"] = 1.0
        status["suggestions"] = [
            "📊 市场中性，正常筛选",
            "⚖️ 可正常建仓"
        ]
    elif fng <= 80:
        status["market_health"] = "greed"
        status["recommend_modifier"] = 1.2
        status["suggestions"] = [
            "📈 市场贪婪，注意风险",
            "🎯 涨幅大的及时止盈"
        ]
    else:
        status["market_health"] = "extreme_greed"
        status["recommend_modifier"] = 0.8
        status["suggestions"] = [
            "⚠️ 市场极度贪婪，可能见顶",
            "🛑 不追高，持仓及时止盈"
        ]
    
    # BTC 下跌时更谨慎
    if btc_change < -5:
        status["recommend_modifier"] *= 0.5
        status["suggestions"].insert(0, "🚨 BTC 大跌，暂停新币推荐")
    elif btc_change < -2:
        status["recommend_modifier"] *= 0.7
        status["suggestions"].insert(0, "⚠️ BTC 下跌，谨慎操作")
    
    return status


# ============== 动态筛选标准 ==============
def get_filter_criteria(market_status):
    """根据市场状态动态调整筛选标准"""
    modifier = market_status.get("recommend_modifier", 1.0)
    
    return {
        "max_price_change_24h": 200 * modifier,  # 最大涨幅
        "min_price_change_24h": -50,             # 最大跌幅
        "min_liquidity": 30000 / modifier,       # 最小流动性
        "max_liquidity": 200000,                 # 最大流动性
        "min_age_hours": 1,                      # 最小存活时间
        "max_age_hours": 72,                     # 最大存活时间
    }


# ============== 代币追踪 ==============
class TokenTracker:
    def __init__(self):
        self.tracked = self.load()
    
    def load(self):
        if os.path.exists(TRACKED_FILE):
            with open(TRACKED_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def save(self):
        with open(TRACKED_FILE, 'w') as f:
            json.dump(self.tracked, f, indent=2, ensure_ascii=False)
    
    def add(self, symbol, chain, address, rec_price):
        key = symbol.replace(".", "_").replace(" ", "_")
        self.tracked[key] = {
            "symbol": symbol,
            "chain": chain,
            "address": address,
            "recommended_price": rec_price,
            "recommended_time": datetime.now().isoformat(),
            "current_price": rec_price,
            "current_change": 0,
            "highest_price": rec_price,
            "lowest_price": rec_price,
            "stop_loss": rec_price * 0.7,    # -30% 止损
            "take_profit": rec_price * 1.5,  # +50% 止盈
            "status": "active"
        }
        self.save()
        print(f"✅ 已添加追踪: {symbol} @ ${rec_price}")
    
    def update_all(self):
        """更新所有追踪代币的价格"""
        alerts = []
        
        for key, info in self.tracked.items():
            if info.get("status") in ["stopped", "sold"]:
                continue
            
            addr = info.get("address", "")
            if not addr:
                continue
            
            try:
                url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
                resp = requests.get(url, timeout=10)
                data = resp.json()
                
                for p in data.get("pairs", []):
                    if p.get("chainId") == info.get("chain"):
                        cur_price = float(p.get("priceUsd", 0) or 0)
                        break
                else:
                    continue
                
                # 更新价格
                info["current_price"] = cur_price
                info["last_update"] = datetime.now().isoformat()
                
                # 计算涨跌
                rec_price = info["recommended_price"]
                change = (cur_price - rec_price) / rec_price * 100
                info["current_change"] = change
                
                # 更新最高最低
                if cur_price > info["highest_price"]:
                    info["highest_price"] = cur_price
                    # 追踪止盈
                    info["take_profit"] = cur_price * 0.85
                
                if cur_price < info["lowest_price"]:
                    info["lowest_price"] = cur_price
                
                # 检查止盈止损
                stop_loss = info.get("stop_loss", rec_price * 0.7)
                take_profit = info.get("take_profit", rec_price * 1.5)
                
                if cur_price <= stop_loss:
                    alerts.append({
                        "type": "🛑 止损",
                        "symbol": info["symbol"],
                        "change": change,
                        "msg": f"{info['symbol']} 跌 {change:.1f}%，触发止损！建议卖出"
                    })
                    info["status"] = "stopped"
                
                elif cur_price >= take_profit:
                    alerts.append({
                        "type": "🎯 止盈",
                        "symbol": info["symbol"],
                        "change": change,
                        "msg": f"{info['symbol']} 涨 {change:.1f}%，可考虑止盈！"
                    })
                    info["status"] = "take_profit_zone"
                
            except Exception as e:
                info["error"] = str(e)
        
        self.save()
        return alerts
    
    def get_report(self):
        """生成表现报告"""
        if not self.tracked:
            return "暂无追踪记录"
        
        lines = ["\n📋 已推荐代币追踪报告", "-" * 50]
        
        total_pnl = 0
        winners = 0
        losers = 0
        stopped = 0
        
        for key, info in self.tracked.items():
            symbol = info.get("symbol", "?")
            change = info.get("current_change")
            status = info.get("status", "active")
            
            # 处理 None 值
            if change is None:
                change = 0
            
            if change > 0:
                emoji = "🟢"
                winners += 1
            else:
                emoji = "🔴"
                losers += 1
            
            if status in ["stopped", "sold"]:
                stopped += 1
            
            total_pnl += change
            
            status_emoji = ""
            if status == "stopped":
                status_emoji = "🛑"
            elif status == "take_profit_zone":
                status_emoji = "🎯"
            elif status == "big_winner":
                status_emoji = "🏆"
            elif status == "winner":
                status_emoji = "✅"
            
            lines.append(f"{emoji} {symbol}: {change:+.1f}% {status_emoji}")
            current = info.get('current_price') or 0
            lines.append(f"   推荐: ${info['recommended_price']:.6f} → 现在: ${current:.6f}")
        
        lines.append("-" * 50)
        if winners + losers > 0:
            lines.append(f"胜率: {winners}/{winners+losers} = {winners/(winners+losers)*100:.0f}%")
            lines.append(f"平均涨跌: {total_pnl/(winners+losers):.1f}%")
        
        return "\n".join(lines)


# ============== 扫描新币 ==============
def scan_new_gems(criteria):
    """扫描符合条件的新币"""
    gems = []
    
    try:
        url = "https://api.dexscreener.com/latest/dex/search?q=solana"
        resp = requests.get(url, timeout=15)
        pairs = resp.json().get("pairs", [])
        
        for p in pairs:
            if p.get("chainId") != "solana":
                continue
            
            liq = float(p.get("liquidity", {}).get("usd", 0) or 0)
            change = float(p.get("priceChange", {}).get("h24", 0) or 0)
            
            # 应用筛选条件
            if liq < criteria["min_liquidity"]:
                continue
            if liq > criteria["max_liquidity"]:
                continue
            if change > criteria["max_price_change_24h"]:
                continue
            if change < criteria["min_price_change_24h"]:
                continue
            
            gems.append({
                "symbol": p.get("baseToken", {}).get("symbol", "?"),
                "name": p.get("baseToken", {}).get("name", "?"),
                "address": p.get("baseToken", {}).get("address", ""),
                "price": float(p.get("priceUsd", 0) or 0),
                "liquidity": liq,
                "volume_24h": float(p.get("volume", {}).get("h24", 0) or 0),
                "price_change_24h": change,
                "chain": "solana"
            })
        
        # 按流动性排序
        gems.sort(key=lambda x: x["liquidity"], reverse=True)
        
    except Exception as e:
        print(f"扫描失败: {e}")
    
    return gems


# ============== 主函数 ==============
def main():
    print("=" * 60)
    print("🔍 Smart Gem Scanner v2.1 - 动态市场评估")
    print("=" * 60)
    
    # 1. 市场状态
    market = get_market_status()
    
    print(f"\n📈 市场状态:")
    print(f"   恐惧贪婪: {market.get('fear_greed', '?')} ({market.get('fear_greed_class', '?')})")
    print(f"   BTC: ${market.get('btc_price', 0):,.0f} ({market.get('btc_change_24h', 0):+.2f}%)")
    print(f"   SOL: ${market.get('sol_price', 0):,.2f} ({market.get('sol_change_24h', 0):+.2f}%)")
    print(f"   市场健康: {market.get('market_health', '?')}")
    print(f"   筛选系数: {market.get('recommend_modifier', 1):.2f}x")
    
    # 2. 建议
    print(f"\n💡 市场建议:")
    for s in market.get("suggestions", []):
        print(f"   {s}")
    
    # 3. 筛选标准
    criteria = get_filter_criteria(market)
    print(f"\n🎯 筛选标准:")
    print(f"   最大涨幅: {criteria['max_price_change_24h']:.0f}%")
    print(f"   流动性: ${criteria['min_liquidity']:,.0f} - ${criteria['max_liquidity']:,.0f}")
    
    # 4. 追踪更新
    tracker = TokenTracker()
    print(f"\n📋 更新追踪...")
    alerts = tracker.update_all()
    
    if alerts:
        print(f"\n⚠️ 止盈止损提醒:")
        for a in alerts:
            print(f"   {a['type']}: {a['msg']}")
    
    # 5. 表现报告
    print(tracker.get_report())
    
    # 6. 扫描新币
    print(f"\n🔍 扫描符合条件的新币...")
    gems = scan_new_gems(criteria)
    
    if gems:
        print(f"\n✅ 发现 {len(gems)} 个符合条件的代币:")
        print("-" * 50)
        for i, g in enumerate(gems[:5], 1):
            emoji = "🟢" if g["price_change_24h"] > 0 else "🔴"
            print(f"\n[{i}] {emoji} {g['symbol']} - ${g['price']:.6f}")
            print(f"    24h: {g['price_change_24h']:+.1f}% | Liq: ${g['liquidity']:,.0f}")
            print(f"    成交量: ${g['volume_24h']:,.0f}")
    else:
        print("\n⚠️ 当前没有符合条件的新币，等待市场企稳")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "--track":
            tracker = TokenTracker()
            alerts = tracker.update_all()
            print(tracker.get_report())
            if alerts:
                print("\n⚠️ 提醒:")
                for a in alerts:
                    print(f"  {a['msg']}")
        
        elif cmd == "--market":
            market = get_market_status()
            print(json.dumps(market, indent=2, ensure_ascii=False))
        
        elif cmd == "--add" and len(sys.argv) >= 5:
            tracker = TokenTracker()
            addr = sys.argv[2]
            price = float(sys.argv[3])
            symbol = sys.argv[4]
            tracker.add(symbol, "solana", addr, price)
        
        else:
            print("用法:")
            print("  python3 smart_gem_scanner_v2.py              # 完整扫描")
            print("  python3 smart_gem_scanner_v2.py --track      # 只更新追踪")
            print("  python3 smart_gem_scanner_v2.py --market     # 只看市场")
            print("  python3 smart_gem_scanner_v2.py --add <addr> <price> <symbol>")
    else:
        main()