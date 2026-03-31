#!/usr/bin/env python3
"""
Smart Gem Scanner v2.0 - 结合市场动态评估
核心改进：
1. 涨幅过滤：不追高
2. 市场情绪：恐惧时更谨慎
3. 实时追踪：已推荐币的表现
4. 止盈止损：自动提醒
"""

import json
import time
import requests
from datetime import datetime
import os

# ============== 配置 ==============
DATA_DIR = "/home/admin/Ziwei/data/smart_gem_scanner"
TRACKED_FILE = f"{DATA_DIR}/tracked_tokens.json"
MARKET_FILE = f"{DATA_DIR}/market_status.json"
os.makedirs(DATA_DIR, exist_ok=True)

# ============== 动态筛选标准 ==============
class DynamicCriteria:
    """根据市场情况动态调整筛选标准"""
    
    def __init__(self):
        self.base_criteria = {
            "max_price_change_24h": 200,    # 基础：不追涨幅 > 200%
            "min_liquidity": 30000,          # 基础：流动性 > $30K
            "max_liquidity": 200000,         # 基础：流动性 < $200K
            "min_age_hours": 1,              # 至少存活1小时
            "max_age_hours": 72,             # 最多3天
        }
        self.market_modifier = 1.0
        self.market_status = "unknown"
        
    def fetch_market_status(self):
        """获取市场情绪"""
        try:
            # 恐惧贪婪指数
            resp = requests.get("https://api.alternative.me/fng/", timeout=10)
            fng = resp.json()['data'][0]
            fng_value = int(fng['value'])
            
            # BTC 走势
            resp = requests.get("https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT", timeout=10)
            btc = resp.json()
            btc_change = float(btc['priceChangePercent'])
            
            # 判断市场状态
            if fng_value <= 25:
                self.market_status = "extreme_fear"
                self.market_modifier = 0.5  # 极度恐惧，更严格
            elif fng_value <= 45:
                self.market_status = "fear"
                self.market_modifier = 0.7
            elif fng_value <= 55:
                self.market_status = "neutral"
                self.market_modifier = 1.0
            elif fng_value <= 75:
                self.market_status = "greed"
                self.market_modifier = 1.2
            else:
                self.market_status = "extreme_greed"
                self.market_modifier = 1.5
            
            # BTC 下跌时更谨慎
            if btc_change < -5:
                self.market_modifier *= 0.6
            elif btc_change < -2:
                self.market_modifier *= 0.8
                
            return {
                "fear_greed": fng_value,
                "fear_greed_class": fng['value_classification'],
                "btc_price": float(btc['lastPrice']),
                "btc_change_24h": btc_change,
                "market_status": self.market_status,
                "market_modifier": self.market_modifier
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_criteria(self):
        """获取调整后的筛选标准"""
        adjusted = {}
        for k, v in self.base_criteria.items():
            if "max_price_change" in k:
                # 恐惧时更严格，贪婪时可以放松
                adjusted[k] = v * self.market_modifier
            else:
                adjusted[k] = v
        return adjusted
    
    def should_recommend(self, token):
        """判断是否应该推荐"""
        criteria = self.get_criteria()
        
        reasons_pass = []
        reasons_fail = []
        
        # 1. 涨幅检查
        change_24h = token.get("price_change_24h", 0)
        max_change = criteria["max_price_change_24h"]
        
        if change_24h > max_change:
            reasons_fail.append(f"涨幅过大 {change_24h:.1f}% > {max_change:.0f}%")
        elif change_24h > max_change * 0.7:
            reasons_pass.append(f"涨幅适中 {change_24h:.1f}%")
        else:
            reasons_pass.append(f"涨幅合理 {change_24h:.1f}%")
        
        # 2. 流动性检查
        liq = token.get("liquidity", 0)
        if liq < criteria["min_liquidity"]:
            reasons_fail.append(f"流动性过低 ${liq:,.0f}")
        elif liq > criteria["max_liquidity"]:
            reasons_pass.append(f"流动性充足 ${liq:,.0f}")
        else:
            reasons_pass.append(f"流动性合适 ${liq:,.0f}")
        
        # 3. 存活时间检查
        age = token.get("age_hours", 0)
        if age < criteria["min_age_hours"]:
            reasons_fail.append(f"太新 {age:.1f}h")
        elif age > criteria["max_age_hours"]:
            reasons_fail.append(f"太老 {age:.1f}h")
        else:
            reasons_pass.append(f"存活 {age:.1f}h")
        
        # 4. 市场情绪调整
        if self.market_status == "extreme_fear":
            reasons_pass.append("⚠️ 市场极度恐惧，建议观望")
        elif self.market_status == "fear":
            reasons_pass.append("⚠️ 市场恐惧，谨慎操作")
        
        return {
            "should_recommend": len(reasons_fail) == 0,
            "pass_reasons": reasons_pass,
            "fail_reasons": reasons_fail,
            "criteria_used": criteria
        }


# ============== 代币追踪系统 ==============
class TokenTracker:
    """追踪已推荐的代币"""
    
    def __init__(self):
        self.tracked = self.load_tracked()
    
    def load_tracked(self):
        if os.path.exists(TRACKED_FILE):
            with open(TRACKED_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def save_tracked(self):
        with open(TRACKED_FILE, 'w') as f:
            json.dump(self.tracked, f, indent=2, ensure_ascii=False)
    
    def add_token(self, token, recommended_price):
        """添加追踪"""
        addr = token.get("address", "")
        if not addr:
            return
        
        self.tracked[addr] = {
            "symbol": token.get("symbol", "?"),
            "chain": token.get("chain", "?"),
            "recommended_price": recommended_price,
            "recommended_time": datetime.now().isoformat(),
            "highest_price": recommended_price,
            "lowest_price": recommended_price,
            "stop_loss": recommended_price * 0.7,  # -30% 止损
            "take_profit": recommended_price * 1.5,  # +50% 止盈
            "status": "active"
        }
        self.save_tracked()
    
    def update_prices(self):
        """更新所有追踪代币的价格"""
        alerts = []
        
        for addr, info in self.tracked.items():
            if info.get("status") != "active":
                continue
            
            try:
                url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
                resp = requests.get(url, timeout=10)
                data = resp.json()
                
                for p in data.get("pairs", []):
                    if p.get("chainId") == info.get("chain"):
                        current_price = float(p.get("priceUsd", 0) or 0)
                        break
                else:
                    continue
                
                # 更新最高最低价
                if current_price > info["highest_price"]:
                    info["highest_price"] = current_price
                    # 追踪止盈
                    info["take_profit"] = current_price * 0.85  # 从最高点回撤15%止盈
                
                if current_price < info["lowest_price"]:
                    info["lowest_price"] = current_price
                
                # 计算涨跌幅
                change = (current_price - info["recommended_price"]) / info["recommended_price"] * 100
                
                # 检查止盈止损
                if current_price <= info["stop_loss"]:
                    alerts.append({
                        "type": "🛑 止损警告",
                        "symbol": info["symbol"],
                        "change": change,
                        "message": f"{info['symbol']} 已跌 {change:.1f}%，触发止损！"
                    })
                    info["status"] = "stopped"
                
                elif current_price >= info["take_profit"]:
                    alerts.append({
                        "type": "🎯 止盈提醒",
                        "symbol": info["symbol"],
                        "change": change,
                        "message": f"{info['symbol']} 已涨 {change:.1f}%，可考虑止盈！"
                    })
                
                info["current_price"] = current_price
                info["current_change"] = change
                info["last_update"] = datetime.now().isoformat()
                
            except Exception as e:
                info["error"] = str(e)
        
        self.save_tracked()
        return alerts
    
    def get_performance_report(self):
        """生成表现报告"""
        if not self.tracked:
            return "暂无追踪记录"
        
        lines = ["📊 已推荐代币表现追踪", "=" * 40]
        
        total_pnl = 0
        winners = 0
        losers = 0
        
        for addr, info in self.tracked.items():
            symbol = info.get("symbol", "?")
            rec_price = info.get("recommended_price", 0)
            cur_price = info.get("current_price", rec_price)
            change = info.get("current_change", 0)
            status = info.get("status", "active")
            
            if change > 0:
                emoji = "🟢"
                winners += 1
            else:
                emoji = "🔴"
                losers += 1
            
            total_pnl += change
            
            lines.append(f"{emoji} {symbol}: {change:+.1f}%")
            lines.append(f"   推荐: ${rec_price:.6f} → 现在: ${cur_price:.6f}")
            lines.append(f"   最高: ${info.get('highest_price', rec_price):.6f}")
            lines.append(f"   状态: {status}")
            lines.append("")
        
        lines.append("=" * 40)
        lines.append(f"胜率: {winners}/{winners+losers} = {winners/(winners+losers)*100:.0f}%")
        lines.append(f"平均涨跌: {total_pnl/len(self.tracked):.1f}%")
        
        return "\n".join(lines)


# ============== 主扫描函数 ==============
def scan_and_recommend():
    """扫描并推荐"""
    criteria = DynamicCriteria()
    tracker = TokenTracker()
    
    print("\n" + "="*50)
    print("🔍 Smart Gem Scanner v2.0 - 动态市场评估")
    print("="*50)
    
    # 1. 获取市场状态
    market = criteria.fetch_market_status()
    print(f"\n📈 市场状态:")
    print(f"   恐惧贪婪: {market.get('fear_greed', '?')} ({market.get('fear_greed_class', '?')})")
    print(f"   BTC: ${market.get('btc_price', 0):,.0f} ({market.get('btc_change_24h', 0):+.2f}%)")
    print(f"   市场状态: {market.get('market_status', '?')}")
    print(f"   筛选严格度: {market.get('market_modifier', 1):.1f}x")
    
    # 2. 获取调整后的标准
    adjusted = criteria.get_criteria()
    print(f"\n🎯 调整后筛选标准:")
    print(f"   最大涨幅: {adjusted['max_price_change_24h']:.0f}%")
    print(f"   流动性: ${adjusted['min_liquidity']:,.0f} - ${adjusted['max_liquidity']:,.0f}")
    print(f"   存活时间: {adjusted['min_age_hours']}h - {adjusted['max_age_hours']}h")
    
    # 3. 扫描代币
    print(f"\n🔍 扫描 Solana 热门代币...")
    
    try:
        url = "https://api.dexscreener.com/latest/dex/search?q=solana"
        resp = requests.get(url, timeout=15)
        data = resp.json()
        pairs = data.get("pairs", [])
        
        # 按流动性排序
        valid_pairs = []
        for p in pairs:
            if p.get("chainId") != "solana":
                continue
            liq = float(p.get("liquidity", {}).get("usd", 0) or 0)
            if liq >= adjusted["min_liquidity"]:
                valid_pairs.append(p)
        
        # 按流动性排序
        valid_pairs.sort(key=lambda x: float(x.get("liquidity", {}).get("usd", 0) or 0), reverse=True)
        
        recommendations = []
        
        for p in valid_pairs[:20]:
            token = {
                "symbol": p.get("baseToken", {}).get("symbol", "?"),
                "name": p.get("baseToken", {}).get("name", "?"),
                "address": p.get("baseToken", {}).get("address", ""),
                "chain": "solana",
                "price": float(p.get("priceUsd", 0) or 0),
                "liquidity": float(p.get("liquidity", {}).get("usd", 0) or 0),
                "volume_24h": float(p.get("volume", {}).get("h24", 0) or 0),
                "price_change_24h": float(p.get("priceChange", {}).get("h24", 0) or 0),
                "age_hours": (time.time() * 1000 - (p.get("pairCreatedAt", 0) or 0)) / 3600000
            }
            
            result = criteria.should_recommend(token)
            
            if result["should_recommend"]:
                token["pass_reasons"] = result["pass_reasons"]
                recommendations.append(token)
        
        # 4. 输出推荐
        print(f"\n✅ 筛选出 {len(recommendations)} 个可考虑的代币:")
        print("-" * 50)
        
        for i, t in enumerate(recommendations[:5], 1):
            print(f"\n[{i}] {t['symbol']} - ${t['price']:.6f}")
            print(f"    流动性: ${t['liquidity']:,.0f}")
            print(f"    24h涨幅: {t['price_change_24h']:+.1f}%")
            print(f"    成交量: ${t['volume_24h']:,.0f}")
            print(f"    ✅ {', '.join(t['pass_reasons'])}")
            print(f"    地址: {t['address'][:20]}...")
        
        # 5. 更新追踪
        print(f"\n📋 更新已追踪代币...")
        alerts = tracker.update_prices()
        
        if alerts:
            print("\n⚠️ 止盈止损提醒:")
            for a in alerts:
                print(f"  {a['type']}: {a['message']}")
        
        # 6. 表现报告
        print(f"\n{tracker.get_performance_report()}")
        
        return recommendations
        
    except Exception as e:
        print(f"❌ 扫描失败: {e}")
        return []


# ============== 入口 ==============
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--track":
            # 只更新追踪
            tracker = TokenTracker()
            alerts = tracker.update_prices()
            print(tracker.get_performance_report())
            if alerts:
                print("\n⚠️ 提醒:")
                for a in alerts:
                    print(f"  {a['message']}")
        elif sys.argv[1] == "--status":
            # 只看市场状态
            criteria = DynamicCriteria()
            market = criteria.fetch_market_status()
            print(json.dumps(market, indent=2))
        elif sys.argv[1] == "--add":
            # 添加追踪
            if len(sys.argv) >= 4:
                tracker = TokenTracker()
                addr = sys.argv[2]
                price = float(sys.argv[3])
                tracker.add_token({"address": addr, "symbol": "MANUAL", "chain": "solana"}, price)
                print(f"✅ 已添加追踪")
    else:
        scan_and_recommend()