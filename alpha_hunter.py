#!/usr/bin/env python3
"""
Alpha Hunter - 早期机会发现系统
发现下一个 BTC/ETH/SOL/BNB / WIF / PEPE
专注于：从垃圾价涨到 $1 的潜力股
"""

import json
import time
import requests
from datetime import datetime
import os
import re

# ============== 配置 ==============
DATA_DIR = "/home/admin/Ziwei/data/alpha_hunter"
os.makedirs(DATA_DIR, exist_ok=True)

# 🎯 潜力股筛选标准（从垃圾价涨到 $1）
GEM_CRITERIA = {
    "max_age_hours": 168,        # 7天内上线
    "max_fdv": 500000,           # 市值 < $500K
    "min_liq": 5000,             # 流动性 > $5K（能交易）
    "max_liq": 100000,           # 流动性 < $100K（还在早期）
    "min_price": 0.00001,        # 价格 < $0.00001（垃圾价）
    "max_price": 0.01,           # 价格 < $0.01
}

# 支持的链
SUPPORTED_CHAINS = {
    "solana": {"name": "Solana", "chain_id": "solana", "emoji": "🌞"},
    "bsc": {"name": "BSC", "chain_id": "bsc", "emoji": "🟡"},
    "base": {"name": "Base", "chain_id": "base", "emoji": "🔵"},
    "ethereum": {"name": "Ethereum", "chain_id": "ethereum", "emoji": "💎"},
    "arbitrum": {"name": "Arbitrum", "chain_id": "arbitrum", "emoji": "🔴"},
    "polygon": {"name": "Polygon", "chain_id": "polygon", "emoji": "🟣"},
}

# 热点叙事关键词
NARRATIVES = [
    "AI", "DePIN", "RWA", "Gaming", "Metaverse", "DeFi", "NFT", 
    "Layer2", "Modular", "Parallel", "ZK", "Restaking", "MEME",
    "DeSci", "Social", "Privacy", "Bridge", "Oracle", "Liquid Staking"
]

# ============== DexScreener 多链扫描 ==============
def get_latest_tokens(chain="solana", min_liq=1000, max_liq=500000, limit=30):
    """获取最新上线的代币（按创建时间排序）"""
    try:
        # 使用 token-profiles 接口获取最新代币
        url = f"https://api.dexscreener.com/latest/dex/tokens/{chain}"
        
        # 或者使用搜索接口按时间排序
        url = f"https://api.dexscreener.com/latest/dex/search?q=solana"
        resp = requests.get(url, timeout=15)
        
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        pairs = data.get("pairs", [])
        
        # 按创建时间排序（最新的在前）
        pairs.sort(key=lambda x: x.get("pairCreatedAt", 0) or 0, reverse=True)
        
        tokens = []
        seen = set()
        
        for p in pairs[:100]:  # 只看前100个
            if p.get("chainId") != chain:
                continue
            
            addr = p.get("baseToken", {}).get("address", "")
            if addr in seen:
                continue
            seen.add(addr)
            
            created = p.get("pairCreatedAt", 0)
            age_hours = (time.time() * 1000 - created) / 3600000 if created else 999
            
            liquidity = float(p.get("liquidity", {}).get("usd", 0) or 0)
            volume = float(p.get("volume", {}).get("h24", 0) or 0)
            
            # 只要流动性在范围内的
            if not (min_liq <= liquidity <= max_liq):
                continue
            
            tokens.append({
                "chain": chain,
                "chain_name": SUPPORTED_CHAINS.get(chain, {}).get("name", chain),
                "symbol": p.get("baseToken", {}).get("symbol", "?"),
                "name": p.get("baseToken", {}).get("name", "?"),
                "address": addr,
                "price": float(p.get("priceUsd", 0) or 0),
                "liquidity": liquidity,
                "volume_24h": volume,
                "price_change_24h": float(p.get("priceChange", {}).get("h24", 0) or 0),
                "txns_24h": p.get("txns", {}).get("h24", {}).get("buys", 0) + p.get("txns", {}).get("h24", {}).get("sells", 0),
                "age_hours": round(age_hours, 1),
                "is_new": age_hours < 24,
                "fdv": float(p.get("fdv", 0) or 0),
            })
            
            if len(tokens) >= limit:
                break
        
        return tokens
        
    except Exception as e:
        print(f"获取最新代币失败: {e}")
        return []

def scan_new_tokens(chain="solana", min_liq=1000, max_liq=200000, min_vol=5000, limit=20):
    """扫描某条链的新币"""
    try:
        # 使用搜索接口，搜索常见关键词来发现新币
        search_terms = ["new", "meme", "ai", "degen", "based", "moon", "pepe"]
        all_pairs = []
        
        for term in search_terms[:3]:  # 限制搜索次数避免被限
            url = f"https://api.dexscreener.com/latest/dex/search?q={term}"
            resp = requests.get(url, timeout=15)
            
            if resp.status_code != 200:
                continue
            
            data = resp.json()
            pairs = data.get("pairs", [])
            
            for p in pairs:
                if p.get("chainId") != chain:
                    continue
                
                liquidity = float(p.get("liquidity", {}).get("usd", 0) or 0)
                volume = float(p.get("volume", {}).get("h24", 0) or 0)
                
                if min_liq <= liquidity <= max_liq and volume >= min_vol:
                    all_pairs.append(p)
            
            time.sleep(0.3)
        
        # 去重并处理
        seen = set()
        tokens = []
        
        for p in all_pairs:
            addr = p.get("baseToken", {}).get("address", "")
            if addr in seen:
                continue
            seen.add(addr)
            
            created = p.get("pairCreatedAt", 0)
            age_hours = (time.time() * 1000 - created) / 3600000 if created else 999
            
            # 🆕 年龄过滤：只保留真正的新币
            # 策略：新币(<24h) + 较新(<7天) + 有热度
            is_new = age_hours < 24
            is_recent = age_hours < 168  # 7天
            has_volume = float(p.get("volume", {}).get("h24", 0) or 0) > 50000
            is_trending = abs(float(p.get("priceChange", {}).get("h24", 0) or 0)) > 20
            
            # 只保留：新币 或 (较新且有热度)
            if not (is_new or (is_recent and (has_volume or is_trending))):
                continue
            
            tokens.append({
                "chain": chain,
                "chain_name": SUPPORTED_CHAINS.get(chain, {}).get("name", chain),
                "symbol": p.get("baseToken", {}).get("symbol", "?"),
                "name": p.get("baseToken", {}).get("name", "?"),
                "address": addr,
                "price": float(p.get("priceUsd", 0) or 0),
                "liquidity": float(p.get("liquidity", {}).get("usd", 0) or 0),
                "volume_24h": float(p.get("volume", {}).get("h24", 0) or 0),
                "price_change_24h": float(p.get("priceChange", {}).get("h24", 0) or 0),
                "txns_24h": p.get("txns", {}).get("h24", {}).get("buys", 0) + p.get("txns", {}).get("h24", {}).get("sells", 0),
                "age_hours": round(age_hours, 1),
                "is_new": is_new,
                "fdv": float(p.get("fdv", 0) or 0),
            })
        
        # 按成交量排序
        tokens.sort(key=lambda x: x["volume_24h"], reverse=True)
        return tokens[:limit]
        
    except Exception as e:
        print(f"扫描 {chain} 失败: {e}")
        return []

def scan_all_chains():
    """扫描所有链的新币"""
    all_tokens = []
    
    for chain_id in SUPPORTED_CHAINS:
        print(f"  扫描 {SUPPORTED_CHAINS[chain_id]['name']}...")
        
        # 优先使用最新代币接口
        new_tokens = get_latest_tokens(chain=chain_id, min_liq=1000, max_liq=500000, limit=10)
        
        # 如果新币不够，补充搜索结果
        if len(new_tokens) < 5:
            more_tokens = scan_new_tokens(chain=chain_id, min_liq=1000, max_liq=500000, min_vol=5000, limit=10)
            # 合并去重
            seen = set(t["address"] for t in new_tokens)
            for t in more_tokens:
                if t["address"] not in seen:
                    new_tokens.append(t)
                    seen.add(t["address"])
        
        all_tokens.extend(new_tokens)
        time.sleep(0.3)
    
    # 按年龄排序，最新的在前
    all_tokens.sort(key=lambda x: x.get("age_hours", 999))
    
    return all_tokens

# ============== 🎯 潜力股筛选 ==============
def find_gem_tokens(tokens):
    """
    筛选潜力股：从垃圾价涨到 $1 的候选
    标准：市值低 + 年龄新 + 价格低 + 有热度
    """
    gems = []
    
    for t in tokens:
        age = t.get("age_hours", 999)
        fdv = t.get("fdv", 0)
        liq = t.get("liquidity", 0)
        price = t.get("price", 0)
        
        # 筛选条件
        checks = []
        
        # 1. 年龄检查（7天内）
        if age <= GEM_CRITERIA["max_age_hours"]:
            checks.append(("age", True, f"{age:.1f}h"))
        else:
            continue  # 太老，跳过
        
        # 2. 市值检查（< $500K）
        if fdv <= GEM_CRITERIA["max_fdv"]:
            checks.append(("fdv", True, f"${fdv:,.0f}"))
        elif fdv <= 1000000:  # 放宽到 $1M
            checks.append(("fdv", "warn", f"${fdv:,.0f} (偏高)"))
        else:
            continue  # 市值太大，跳过
        
        # 3. 价格检查（垃圾价区间）
        if GEM_CRITERIA["min_price"] <= price <= GEM_CRITERIA["max_price"]:
            checks.append(("price", True, f"${price:.8f}"))
        else:
            continue  # 价格不在潜力区间
        
        # 4. 流动性检查
        if GEM_CRITERIA["min_liq"] <= liq <= GEM_CRITERIA["max_liq"]:
            checks.append(("liq", True, f"${liq:,.0f}"))
        elif liq > GEM_CRITERIA["max_liq"]:
            checks.append(("liq", "warn", f"${liq:,.0f} (较高)"))
        else:
            continue
        
        # 5. 热度检查
        vol = t.get("volume_24h", 0)
        change = abs(t.get("price_change_24h", 0))
        if vol > 50000 or change > 50:
            checks.append(("hot", True, f"Vol ${vol:,.0f}, {change:.0f}%"))
        
        # 计算潜力分数
        score = 0
        for name, status, _ in checks:
            if status is True:
                score += 2
            elif status == "warn":
                score += 1
        
        # 潜力计算：从当前价到 $1 需要的倍数
        potential = 1 / price if price > 0 else 0
        
        gems.append({
            **t,
            "gem_score": score,
            "potential_x": potential,
            "checks": checks,
        })
    
    # 按潜力分数排序
    gems.sort(key=lambda x: x["gem_score"], reverse=True)
    
    return gems

# ============== 热点代币 ==============
def get_boosted_tokens():
    """获取被推广的代币（通常是热点）"""
    try:
        url = "https://api.dexscreener.com/token-boosts/top/v1"
        resp = requests.get(url, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            # 可能是列表也可能是 dict
            if isinstance(data, list):
                boosts = data
            else:
                boosts = data.get("data", data.get("tokens", []))
            
            hot_tokens = []
            
            for b in boosts[:30]:
                chain = b.get("chainId", "")
                if chain in SUPPORTED_CHAINS:
                    # 从 URL 提取 symbol 或直接用地址
                    url_path = b.get("url", "")
                    address = b.get("tokenAddress", "")
                    
                    hot_tokens.append({
                        "chain": chain,
                        "chain_name": SUPPORTED_CHAINS.get(chain, {}).get("name", chain),
                        "address": address,
                        "description": b.get("description", "")[:100] if b.get("description") else "",
                        "boost_amount": b.get("totalAmount", 0),
                        "links": b.get("links", []),
                    })
            
            return hot_tokens
    except Exception as e:
        print(f"获取热点代币失败: {e}")
    
    return []

# ============== 新闻抓取 ==============
def fetch_crypto_news():
    """获取加密货币新闻"""
    news_sources = [
        {
            "name": "CoinDesk",
            "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        },
        {
            "name": "Cointelegraph", 
            "url": "https://cointelegraph.com/rss",
        },
        {
            "name": "Decrypt",
            "url": "https://decrypt.co/feed",
        }
    ]
    
    all_news = []
    
    for source in news_sources:
        try:
            import xml.etree.ElementTree as ET
            import urllib.request
            
            req = urllib.request.Request(source["url"], headers={"User-Agent": "Mozilla/5.0"})
            resp = urllib.request.urlopen(req, timeout=15)
            content = resp.read()
            
            root = ET.fromstring(content)
            items = root.findall(".//item")[:5]
            
            for item in items:
                title = item.find("title")
                link = item.find("link")
                pub_date = item.find("pubDate")
                
                if title is not None:
                    # 检查是否包含关键叙事
                    title_text = title.text or ""
                    relevant_narrative = None
                    for nar in NARRATIVES:
                        if nar.lower() in title_text.lower():
                            relevant_narrative = nar
                            break
                    
                    all_news.append({
                        "source": source["name"],
                        "title": title_text,
                        "link": link.text if link is not None else "",
                        "date": pub_date.text if pub_date is not None else "",
                        "narrative": relevant_narrative,
                    })
        
        except Exception as e:
            print(f"获取 {source['name']} 新闻失败: {e}")
    
    # 按相关性排序（有叙事的在前）
    all_news.sort(key=lambda x: 0 if x["narrative"] else 1)
    return all_news[:20]

# ============== 空投机会 ==============
def check_airdrops():
    """检查潜在空投机会"""
    # 这里可以接入各种空投聚合器
    # 目前先返回一些常见的空投检查点
    airdrop_sources = [
        {"name": "Galxe", "url": "https://app.galxe.com/quest", "type": "任务平台"},
        {"name": "LayerZero", "url": "https://layerzero.network/", "type": "跨链协议"},
        {"name": "ZkSync", "url": "https://zksync.io/", "type": "L2"},
        {"name": "Starknet", "url": "https://starknet.io/", "type": "L2"},
        {"name": "Scroll", "url": "https://scroll.io/", "type": "L2"},
    ]
    return airdrop_sources

# ============== 趋势分析 ==============
def analyze_trends(tokens):
    """分析趋势"""
    
    # 按链统计
    chain_stats = {}
    for t in tokens:
        chain = t.get("chain", "unknown")
        if chain not in chain_stats:
            chain_stats[chain] = {"count": 0, "total_volume": 0, "total_liq": 0}
        chain_stats[chain]["count"] += 1
        chain_stats[chain]["total_volume"] += t.get("volume_24h", 0)
        chain_stats[chain]["total_liq"] += t.get("liquidity", 0)
    
    # 找出热门链
    hot_chains = sorted(chain_stats.items(), key=lambda x: x[1]["total_volume"], reverse=True)
    
    # 找出新币中的明星
    rising_stars = sorted(tokens, key=lambda x: x.get("price_change_24h", 0), reverse=True)[:5]
    
    # 找出高成交量代币
    high_volume = sorted(tokens, key=lambda x: x.get("volume_24h", 0), reverse=True)[:5]
    
    return {
        "chain_stats": chain_stats,
        "hot_chains": hot_chains[:3],
        "rising_stars": rising_stars,
        "high_volume": high_volume,
    }

# ============== 主报告 ==============
def generate_report():
    """生成 Alpha 报告"""
    
    print("=" * 70)
    print("🌟 Alpha Hunter - 早期机会发现报告")
    print("=" * 70)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 1. 多链新币扫描
    print("\n📊 多链新币扫描...")
    all_tokens = scan_all_chains()
    
    # 🎯 筛选潜力股
    print("\n" + "=" * 70)
    print("🎯 潜力股筛选（从垃圾价涨到 $1）")
    print("=" * 70)
    gems = find_gem_tokens(all_tokens)
    
    if gems:
        print(f"\n发现 {len(gems)} 个潜力股候选：")
        for i, g in enumerate(gems[:5], 1):
            print(f"\n[{i}] {g['symbol']} ({g['chain_name']})")
            print(f"    价格: ${g['price']:.8f}")
            print(f"    潜力: 涨到 $1 需要 {g['potential_x']:,.0f} 倍")
            print(f"    市值: ${g['fdv']:,.0f} | 流动性: ${g['liquidity']:,.0f}")
            print(f"    年龄: {g['age_hours']:.1f}h | 评分: {g['gem_score']}/10")
            print(f"    地址: {g['address']}")
    else:
        print("\n⚠️ 未发现符合条件的潜力股")
        print("   标准: 市值<$500K + 年龄<7天 + 价格$0.00001-$0.01")
    
    # 📧 发送邮件通知
    if gems:
        try:
            import sys
            sys.path.insert(0, '/home/admin/Ziwei/scripts')
            from alpha_email_notify import notify_multiple_gems
            notify_multiple_gems(gems)
        except Exception as e:
            print(f"⚠️ 邮件通知失败: {e}")
    
    if all_tokens:
        print(f"\n\n📊 全部扫描结果: {len(all_tokens)} 个代币")
        
        # 按链分组显示
        for chain_id in SUPPORTED_CHAINS:
            chain_tokens = [t for t in all_tokens if t["chain"] == chain_id]
            if chain_tokens:
                emoji = SUPPORTED_CHAINS[chain_id]["emoji"]
                name = SUPPORTED_CHAINS[chain_id]["name"]
                print(f"\n{emoji} {name} ({len(chain_tokens)} 个):")
                
                for t in chain_tokens[:3]:
                    change_emoji = "🟢" if t["price_change_24h"] > 0 else "🔴"
                    new_tag = "🆕 " if t.get("is_new") else ""
                    age_str = f"{t['age_hours']:.1f}h" if t['age_hours'] < 24 else f"{t['age_hours']/24:.1f}d"
                    print(f"   {new_tag}{t['symbol']}: ${t['price']:.8f} | 流动性 ${t['liquidity']:,.0f} | 年龄 {age_str} | 24h {change_emoji} {t['price_change_24h']:.1f}%")
    
    # 2. 趋势分析
    if all_tokens:
        print("\n\n📈 趋势分析...")
        trends = analyze_trends(all_tokens)
        
        print("\n🔥 热门链（按成交量）:")
        for chain, stats in trends["hot_chains"]:
            emoji = SUPPORTED_CHAINS.get(chain, {}).get("emoji", "⚪")
            print(f"   {emoji} {SUPPORTED_CHAINS.get(chain, {}).get('name', chain)}: 成交量 ${stats['total_volume']:,.0f}")
        
        print("\n🚀 涨幅榜:")
        for t in trends["rising_stars"]:
            print(f"   {t['symbol']} ({t['chain_name']}): +{t['price_change_24h']:.1f}%")
    
    # 3. 热点代币
    print("\n\n🔥 推广热点代币...")
    boosted = get_boosted_tokens()
    if boosted:
        for b in boosted[:5]:
            emoji = SUPPORTED_CHAINS.get(b["chain"], {}).get("emoji", "⚪")
            desc = b.get("description", "")[:40] if b.get("description") else b.get("address", "")[:10]
            print(f"   {emoji} {desc}... (推广: ${b.get('boost_amount', 0)})")
    
    # 4. 新闻热点
    print("\n\n📰 行业新闻...")
    news = fetch_crypto_news()
    if news:
        for n in news[:8]:
            narrative_tag = f"[{n['narrative']}]" if n.get("narrative") else ""
            print(f"   [{n['source']}] {n['title'][:60]}... {narrative_tag}")
    
    # 保存报告
    report = {
        "time": datetime.now().isoformat(),
        "tokens": all_tokens,
        "news": news,
        "boosted": boosted,
    }
    
    filepath = os.path.join(DATA_DIR, f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.json")
    with open(filepath, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 报告已保存: {filepath}")
    
    # 5. 新币背景调查
    if all_tokens:
        print(f"\n\n{'='*70}")
        print(f"🔍 新币背景调查 (前3个)")
        print(f"{'='*70}")
        
        for i, token in enumerate(all_tokens[:3], 1):
            addr = token.get("address", "")
            symbol = token.get("symbol", "?")
            print(f"\n[{i}] 调查 {symbol} ({token.get('chain_name', '?')})...")
            
            try:
                import subprocess
                result = subprocess.run(
                    ["python3", "/home/admin/Ziwei/scripts/token_background_check.py", addr],
                    capture_output=True, text=True, timeout=30
                )
                # 提取关键信息
                lines = result.stdout.split("\n")
                show_line = False
                for line in lines:
                    if "基本信息:" in line or "社交链接:" in line or "风险评估:" in line:
                        show_line = True
                    if "后续调查建议" in line:
                        show_line = False
                    if show_line and line.strip():
                        print(line)
            except Exception as e:
                print(f"  ⚠️ 调查失败: {e}")
    
    return report

# ============== 入口 ==============
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--chain":
            chain = sys.argv[2] if len(sys.argv) > 2 else "solana"
            tokens = scan_new_tokens(chain=chain)
            for t in tokens:
                print(f"{t['symbol']}: ${t['price']:.8f} | Liq ${t['liquidity']:,.0f} | Vol ${t['volume_24h']:,.0f}")
        elif sys.argv[1] == "--news":
            news = fetch_crypto_news()
            for n in news:
                print(f"[{n['source']}] {n['title']}")
        elif sys.argv[1] == "--monitor":
            # 持续监控
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 600
            while True:
                generate_report()
                print(f"\n⏳ {interval//60} 分钟后继续...")
                time.sleep(interval)
    else:
        generate_report()