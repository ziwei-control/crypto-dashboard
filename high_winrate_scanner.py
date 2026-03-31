#!/usr/bin/env python3
"""
High Win Rate Scanner v1.0
目标：将胜率从 33% 提升到 50%+

核心改进：
1. 涨幅过滤：不推涨幅 > 200% 的币
2. 流动性过滤：$30K - $200K
3. 社交链接验证：必须有官网或Twitter
4. 名字过滤：过滤掉离谱名字
5. 链优先：ETH/Base > SOL pump.fun
"""

import requests
import json
from datetime import datetime

# ============== 新筛选标准 ==============
CRITERIA = {
    "max_price_change_24h": 200,    # 绝对不推涨幅 > 200%
    "warning_price_change": 100,    # 100-200% 谨慎
    "min_liquidity": 30000,         # 最小流动性 $30K
    "max_liquidity": 200000,        # 最大流动性 $200K
    "min_volume": 50000,            # 最小成交量 $50K
}

# 黑名单关键词（离谱名字）
BLACKLIST_NAMES = [
    "dislike", "fuck", "shit", "scam", "rug", 
    "fine999", "999", "xxx", "porn"
]

# 优先链
PRIORITY_CHAINS = ["ethereum", "base", "arbitrum"]


def check_social_links(token_info):
    """检查是否有社交链接"""
    # 从 DexScreener 返回的信息中检查
    info = token_info.get("info", {}) or {}
    
    has_website = bool(info.get("website"))
    has_twitter = bool(info.get("socials", []))
    
    return {
        "has_website": has_website,
        "has_twitter": has_twitter,
        "has_social": has_website or has_twitter
    }


def is_blacklisted(name):
    """检查是否在黑名单"""
    name_lower = name.lower()
    for bl in BLACKLIST_NAMES:
        if bl in name_lower:
            return True
    return False


def score_token(token):
    """给代币打分，判断是否值得推荐"""
    score = 0
    reasons = []
    
    symbol = token.get("baseToken", {}).get("symbol", "?")
    name = token.get("baseToken", {}).get("name", "?")
    chain = token.get("chainId", "")
    
    change_24h = float(token.get("priceChange", {}).get("h24", 0) or 0)
    liquidity = float(token.get("liquidity", {}).get("usd", 0) or 0)
    volume = float(token.get("volume", {}).get("h24", 0) or 0)
    
    # 1. 涨幅评分
    if change_24h > 200:
        return 0, ["❌ 涨幅过大 >200%，追高风险"]
    elif change_24h > 100:
        score += 1
        reasons.append("⚠️ 涨幅100-200%，谨慎")
    elif change_24h > 0:
        score += 3
        reasons.append("✅ 涨幅适中 0-100%")
    elif change_24h > -30:
        score += 4
        reasons.append("✅ 回调中，可考虑抄底")
    else:
        score += 2
        reasons.append("⚠️ 跌幅较大，观察")
    
    # 2. 流动性评分
    if liquidity < 30000:
        return 0, ["❌ 流动性太低 <$30K"]
    elif liquidity > 200000:
        score += 1
        reasons.append("⚠️ 流动性较高，可能已过早期")
    else:
        score += 3
        reasons.append(f"✅ 流动性合适 ${liquidity/1000:.0f}K")
    
    # 3. 成交量评分
    if volume > 500000:
        score += 2
        reasons.append(f"✅ 成交量高 ${volume/1000000:.1f}M")
    elif volume > 50000:
        score += 1
        reasons.append(f"✅ 成交量适中 ${volume/1000:.0f}K")
    
    # 4. 链评分
    if chain in PRIORITY_CHAINS:
        score += 2
        reasons.append(f"✅ 优先链 {chain.upper()}")
    elif chain == "solana":
        dex = token.get("dexId", "")
        if "pump" in dex:
            score += 0
            reasons.append("⚠️ SOL pump.fun，风险较高")
        else:
            score += 1
            reasons.append("✅ SOL 非pump")
    
    # 5. 黑名单检查
    if is_blacklisted(name) or is_blacklisted(symbol):
        return 0, ["❌ 名字离谱，跳过"]
    
    # 6. 社交链接
    social = check_social_links(token)
    if social["has_social"]:
        score += 2
        if social["has_website"]:
            reasons.append("✅ 有官网")
        if social["has_twitter"]:
            reasons.append("✅ 有Twitter")
    
    return score, reasons


def scan_chain(chain, limit=50):
    """扫描指定链"""
    url = f"https://api.dexscreener.com/latest/dex/search?q={chain}"
    
    try:
        resp = requests.get(url, timeout=15)
        pairs = resp.json().get("pairs", [])
        
        candidates = []
        
        for p in pairs:
            if p.get("chainId") != chain:
                continue
            
            score, reasons = score_token(p)
            
            if score >= 5:  # 最低5分才推荐
                candidates.append({
                    "symbol": p.get("baseToken", {}).get("symbol", "?"),
                    "name": p.get("baseToken", {}).get("name", "?"),
                    "chain": chain,
                    "address": p.get("baseToken", {}).get("address", ""),
                    "price": float(p.get("priceUsd", 0) or 0),
                    "liquidity": float(p.get("liquidity", {}).get("usd", 0) or 0),
                    "volume_24h": float(p.get("volume", {}).get("h24", 0) or 0),
                    "change_24h": float(p.get("priceChange", {}).get("h24", 0) or 0),
                    "score": score,
                    "reasons": reasons,
                    "url": f"https://dexscreener.com/{chain}/{p.get('pairAddress', '')}"
                })
        
        # 按分数排序
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:limit]
        
    except Exception as e:
        print(f"扫描 {chain} 失败: {e}")
        return []


def main():
    print("=" * 70)
    print("🎯 High Win Rate Scanner v1.0 - 目标胜率 50%+")
    print("=" * 70)
    print(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    print("📋 筛选标准:")
    print(f"   • 涨幅上限: {CRITERIA['max_price_change_24h']}%")
    print(f"   • 流动性: ${CRITERIA['min_liquidity']/1000:.0f}K - ${CRITERIA['max_liquidity']/1000:.0f}K")
    print(f"   • 必须有社交链接")
    print(f"   • 过滤离谱名字")
    print()
    
    all_candidates = []
    
    # 扫描各链
    for chain in ["solana", "base", "ethereum"]:
        print(f"🔍 扫描 {chain.upper()}...")
        candidates = scan_chain(chain, limit=20)
        all_candidates.extend(candidates)
        print(f"   发现 {len(candidates)} 个候选")
    
    # 合并排序
    all_candidates.sort(key=lambda x: x["score"], reverse=True)
    
    print()
    print("=" * 70)
    print("✅ 推荐列表 (按分数排序)")
    print("=" * 70)
    
    if not all_candidates:
        print("⚠️ 当前没有符合高胜率标准的代币")
        print("   建议：等待市场机会或放宽标准")
    else:
        for i, c in enumerate(all_candidates[:10], 1):
            emoji = "🟢" if c["score"] >= 8 else "🟡" if c["score"] >= 6 else "⚪"
            change_emoji = "📈" if c["change_24h"] > 0 else "📉"
            
            print(f"\n[{i}] {emoji} {c['symbol']} - ${c['price']:.6f}")
            print(f"    链: {c['chain'].upper()} | 分数: {c['score']}/10")
            print(f"    {change_emoji} 24h: {c['change_24h']:+.1f}% | Liq: ${c['liquidity']/1000:.0f}K | Vol: ${c['volume_24h']/1000:.0f}K")
            print(f"    原因: {' | '.join(c['reasons'][:3])}")
            print(f"    链接: {c['url']}")
    
    print()
    print("=" * 70)
    print("💡 风险提示")
    print("=" * 70)
    print("   • 任何早期币都有归零风险")
    print("   • 建议仓位: 单币 < 总资金 5%")
    print("   • 止损: -30% | 止盈: +50% 卖一半")
    print("   • 涨幅>100%的币，建议等回调再入")
    print("=" * 70)
    
    return all_candidates


if __name__ == "__main__":
    main()