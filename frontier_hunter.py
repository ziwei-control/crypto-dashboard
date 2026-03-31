#!/usr/bin/env python3
"""
前沿热点猎手 - 发现刚上线的潜力代币
核心：在流动性低、刚上线时发现机会，而不是等大户买完才看到
"""

import json
import time
import requests
from datetime import datetime, timedelta
import os

# ============== 配置 ==============
DEXSCREENER_API = "https://api.dexscreener.com/latest"
RPC_URL = "https://api.mainnet-beta.solana.com"

# 数据目录
DATA_DIR = "/home/admin/Ziwei/data/frontier_hunter"
os.makedirs(DATA_DIR, exist_ok=True)

# ============== DexScreener API ==============
def get_new_solana_tokens():
    """获取 Solana 最新代币"""
    try:
        # DexScreener 的 token boosting 接口
        url = f"{DEXSCREENER_API}/dex/tokens/boosts/top/v1"
        resp = requests.get(url, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            # 筛选 Solana 链
            solana_tokens = []
            for token in data.get("data", []):
                if token.get("chainId") == "solana":
                    solana_tokens.append(token)
            return solana_tokens
    except Exception as e:
        print(f"获取 boosting 代币失败: {e}")
    
    return []

def get_token_profiles():
    """获取代币配置文件（包含社交信息）"""
    try:
        url = f"{DEXSCREENER_API}/token-profiles/latest/v1"
        resp = requests.get(url, timeout=15)
        
        if resp.status_code == 200:
            return resp.json().get("data", [])
    except Exception as e:
        print(f"获取代币配置失败: {e}")
    
    return []

def search_new_tokens(min_liquidity=1000, max_liquidity=100000, min_volume=1000):
    """搜索新代币 - 流动性低但有成交量的"""
    try:
        # 使用 token search 接口
        url = f"{DEXSCREENER_API}/dex/search?q=solana"
        resp = requests.get(url, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            pairs = data.get("pairs", [])
            
            # 筛选 Solana 且符合前沿标准的
            frontier = []
            for pair in pairs:
                if pair.get("chainId") != "solana":
                    continue
                    
                liquidity = float(pair.get("liquidity", {}).get("usd", 0) or 0)
                volume_24h = float(pair.get("volume", {}).get("h24", 0) or 0)
                created_at = pair.get("pairCreatedAt", 0)
                
                # 前沿标准
                if (min_liquidity <= liquidity <= max_liquidity and 
                    volume_24h >= min_volume):
                    
                    age_hours = (time.time() * 1000 - created_at) / 3600000 if created_at else 999
                    
                    frontier.append({
                        "symbol": pair.get("baseToken", {}).get("symbol", "?"),
                        "name": pair.get("baseToken", {}).get("name", "?"),
                        "address": pair.get("baseToken", {}).get("address", ""),
                        "pair_address": pair.get("pairAddress", ""),
                        "price": float(pair.get("priceUsd", 0) or 0),
                        "liquidity": liquidity,
                        "volume_24h": volume_24h,
                        "price_change_24h": float(pair.get("priceChange", {}).get("h24", 0) or 0),
                        "txns_24h": pair.get("txns", {}).get("h24", {}).get("buys", 0) + pair.get("txns", {}).get("h24", {}).get("sells", 0),
                        "age_hours": round(age_hours, 1),
                        "created_at": datetime.fromtimestamp(created_at/1000).strftime("%Y-%m-%d %H:%M") if created_at else ""
                    })
            
            # 按流动性排序（越低越前沿）
            frontier.sort(key=lambda x: x["liquidity"])
            return frontier
            
    except Exception as e:
        print(f"搜索代币失败: {e}")
    
    return []

def get_trending_tokens():
    """获取趋势代币"""
    try:
        url = f"{DEXSCREENER_API}/dex/tokens/trending/v1"
        resp = requests.get(url, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            # 筛选 Solana
            solana_trending = []
            for token in data.get("data", [])[:20]:
                pairs = token.get("pairs", [])
                solana_pairs = [p for p in pairs if p.get("chainId") == "solana"]
                if solana_pairs:
                    best_pair = sorted(solana_pairs, key=lambda x: x.get("liquidity", {}).get("usd", 0) or 0, reverse=True)[0]
                    liquidity = float(best_pair.get("liquidity", {}).get("usd", 0) or 0)
                    
                    # 只关注流动性 < $500K 的（还有空间）
                    if liquidity < 500000:
                        solana_trending.append({
                            "symbol": best_pair.get("baseToken", {}).get("symbol", "?"),
                            "name": best_pair.get("baseToken", {}).get("name", "?"),
                            "address": best_pair.get("baseToken", {}).get("address", ""),
                            "price": float(best_pair.get("priceUsd", 0) or 0),
                            "liquidity": liquidity,
                            "price_change_24h": float(best_pair.get("priceChange", {}).get("h24", 0) or 0),
                        })
            
            return solana_trending
            
    except Exception as e:
        print(f"获取趋势代币失败: {e}")
    
    return []

# ============== 持仓大户检查 ==============
def get_top_holders(token_address, limit=10):
    """获取代币持仓大户"""
    import urllib.request
    
    payload = json.dumps({
        "jsonrpc": "2.0", 
        "id": 1, 
        "method": "getTokenLargestAccounts", 
        "params": [token_address]
    }).encode()
    
    req = urllib.request.Request(
        RPC_URL, 
        data=payload, 
        headers={"Content-Type": "application/json"}
    )
    
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read().decode())
        
        if "result" in data and data["result"]:
            accounts = data["result"].get("value", [])[:limit]
            holders = []
            for acc in accounts:
                amount = float(acc.get("uiAmount", 0) or 0)
                holders.append({
                    "address": acc.get("address", ""),
                    "amount": amount,
                    "rank": len(holders) + 1
                })
            return holders
    except Exception as e:
        print(f"获取大户失败: {e}")
    
    return []

# ============== 分析代币 ==============
def analyze_token(token_info):
    """深度分析代币"""
    print(f"\n{'='*60}")
    print(f"🪙 {token_info['symbol']} - {token_info['name']}")
    print(f"{'='*60}")
    print(f"   价格: ${token_info.get('price', 0):.10f}")
    print(f"   流动性: ${token_info.get('liquidity', 0):,.0f}")
    print(f"   24h成交量: ${token_info.get('volume_24h', 0):,.0f}")
    print(f"   24h涨幅: {token_info.get('price_change_24h', 0):.1f}%")
    print(f"   年龄: {token_info.get('age_hours', '?')} 小时")
    
    # 检查持仓分布
    if token_info.get('address'):
        print(f"\n   📊 持仓大户...")
        holders = get_top_holders(token_info['address'], limit=5)
        
        if holders:
            total = sum(h['amount'] for h in holders)
            print(f"   Top 5 持仓占比: {total/holders[0]['amount']*100 if holders else 0:.0f}%")
            
            for h in holders[:3]:
                print(f"      #{h['rank']}: {h['amount']:,.0f}")
    
    return token_info

# ============== 主扫描 ==============
def scan_frontier():
    """扫描前沿热点"""
    
    print("=" * 70)
    print("🔥 前沿热点扫描")
    print("=" * 70)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 1. 趋势代币
    print("\n📈 趋势代币（流动性 < $500K）...")
    trending = get_trending_tokens()
    
    if trending:
        print(f"发现 {len(trending)} 个趋势代币")
        for t in trending[:5]:
            change_emoji = "🟢" if t['price_change_24h'] > 0 else "🔴"
            print(f"\n   {t['symbol']} - {t['name']}")
            print(f"   价格: ${t['price']:.10f}")
            print(f"   流动性: ${t['liquidity']:,.0f}")
            print(f"   24h: {change_emoji} {t['price_change_24h']:.1f}%")
    else:
        print("暂无趋势代币")
    
    # 2. 前沿新币
    print("\n\n🚀 前沿新币（流动性 $1K-$100K，有成交量）...")
    frontier = search_new_tokens(min_liquidity=1000, max_liquidity=100000, min_volume=5000)
    
    if frontier:
        print(f"发现 {len(frontier)} 个前沿代币")
        
        # 深度分析前 3 个
        for t in frontier[:3]:
            analyze_token(t)
    else:
        print("暂无前沿代币")
    
    # 保存结果
    result = {
        "scan_time": datetime.now().isoformat(),
        "trending": trending,
        "frontier": frontier[:10]
    }
    
    filepath = os.path.join(DATA_DIR, "latest_scan.json")
    with open(filepath, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\n✅ 扫描完成，结果已保存")
    
    return result

# ============== 持续监控 ==============
def monitor_frontier(interval=300):
    """持续监控前沿热点"""
    
    while True:
        scan_frontier()
        print(f"\n⏳ {interval//60} 分钟后继续扫描...")
        time.sleep(interval)

# ============== 入口 ==============
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--monitor":
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 300
            monitor_frontier(interval)
        elif sys.argv[1] == "--trending":
            trending = get_trending_tokens()
            for t in trending:
                print(f"{t['symbol']}: ${t['price']:.10f} | 流动性 ${t['liquidity']:,.0f} | 24h {t['price_change_24h']:.1f}%")
        elif sys.argv[1] == "--analyze":
            if len(sys.argv) > 2:
                address = sys.argv[2]
                analyze_token({"address": address, "symbol": "Unknown", "name": "Unknown"})
    else:
        scan_frontier()