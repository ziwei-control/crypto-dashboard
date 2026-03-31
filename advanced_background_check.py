#!/usr/bin/env python3
"""
高级背景调查 - 检测有背景、有能力的人做的项目
"""

import requests
import json
import re
import sys
from datetime import datetime

# 代币合约地址
TOKEN_ADDRESS = sys.argv[1] if len(sys.argv) > 1 else None

def get_dexscreener_info(address):
    """从 DexScreener 获取完整信息"""
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("pairs", [])[0] if data.get("pairs") else None
    except:
        pass
    return None

def analyze_twitter(twitter_url):
    """分析 Twitter 账号（简化版）"""
    if not twitter_url:
        return None
    
    # 提取用户名
    match = re.search(r'x\.com/(\w+)', twitter_url)
    if not match:
        return None
    
    username = match.group(1)
    
    # 检查是否是知名账号（简化检测）
    known_accounts = {
        "elonmusk": {"name": "Elon Musk", "influence": "极高"},
        "VitalikButerin": {"name": "Vitalik", "influence": "极高"},
        "sama": {"name": "Sam Altman", "influence": "极高"},
        "balajis": {"name": "Balaji", "influence": "高"},
        "naval": {"name": "Naval", "influence": "高"},
        "aantonop": {"name": "Andreas", "influence": "高"},
        "APompliano": {"name": "Pomp", "influence": "中"},
        "cameron": {"name": "Cameron Winklevoss", "influence": "中"},
        "tyler": {"name": "Tyler Winklevoss", "influence": "中"},
    }
    
    if username.lower() in known_accounts:
        return known_accounts[username.lower()]
    
    return {"username": username, "influence": "未知"}

def check_creator_history(creator_address):
    """检查创建者历史（通过 Solscan API 模拟）"""
    # 这里可以扩展为实际的 API 调用
    # 目前返回建议手动检查
    return {
        "address": creator_address,
        "solscan": f"https://solscan.io/account/{creator_address}",
        "suggestion": "手动查看创建者历史交易"
    }

def detect_red_flags(token_info):
    """检测危险信号"""
    flags = []
    
    # 流动性检查
    liq = float(token_info.get("liquidity", {}).get("usd", 0))
    if liq < 10000:
        flags.append({"type": "danger", "msg": f"流动性过低 (${liq:,.0f})"})
    elif liq < 50000:
        flags.append({"type": "warning", "msg": f"流动性较低 (${liq:,.0f})"})
    
    # 涨跌检查
    change_24h = token_info.get("priceChange", {}).get("h24", 0)
    if change_24h < -30:
        flags.append({"type": "danger", "msg": f"24h暴跌 {change_24h}%"})
    elif change_24h > 100:
        flags.append({"type": "warning", "msg": f"24h暴涨 {change_24h}%，注意追高风险"})
    
    # 年龄检查
    created = token_info.get("pairCreatedAt")
    if created:
        age_hours = (datetime.now().timestamp() * 1000 - created) / 3600000
        if age_hours < 1:
            flags.append({"type": "info", "msg": f"刚上线 {age_hours:.1f} 小时"})
        elif age_hours < 24:
            flags.append({"type": "info", "msg": f"上线 {age_hours:.1f} 小时"})
    
    return flags

def detect_green_flags(token_info, socials):
    """检测正面信号"""
    flags = []
    
    # 流动性充足
    liq = float(token_info.get("liquidity", {}).get("usd", 0))
    if liq > 100000:
        flags.append({"type": "good", "msg": f"流动性充足 (${liq:,.0f})"})
    
    # 有官网和社交
    if socials.get("website"):
        flags.append({"type": "good", "msg": "有官网"})
    if socials.get("twitter"):
        flags.append({"type": "good", "msg": "有 Twitter"})
    if socials.get("telegram"):
        flags.append({"type": "good", "msg": "有 Telegram"})
    
    # 成交量高
    vol = float(token_info.get("volume", {}).get("h24", 0))
    if vol > 100000:
        flags.append({"type": "good", "msg": f"24h成交量 ${vol:,.0f}"})
    
    return flags

def comprehensive_check(address):
    """综合背景调查"""
    print(f"\n{'='*70}")
    print(f"🔍 高级背景调查")
    print(f"{'='*70}")
    print(f"代币地址: {address}")
    
    # 获取信息
    token_info = get_dexscreener_info(address)
    if not token_info:
        print("❌ 无法获取代币信息")
        return
    
    # 基本信息
    base = token_info.get("baseToken", {})
    print(f"\n📊 基本信息:")
    print(f"   名称: {base.get('name', '?')}")
    print(f"   代号: {base.get('symbol', '?')}")
    print(f"   链: {token_info.get('chainId', '?')}")
    print(f"   价格: ${token_info.get('priceUsd', '?')}")
    
    # 社交链接
    print(f"\n🌐 社交链接:")
    socials = {}
    info = token_info.get("info", {})
    
    if info.get("websites"):
        socials["website"] = info["websites"][0].get("url", "")
        print(f"   官网: {socials['website']}")
    
    if info.get("socials"):
        for s in info["socials"]:
            stype = s.get("type", "")
            url = s.get("url", "")
            socials[stype] = url
            print(f"   {stype}: {url}")
    
    if not socials:
        print("   ⚠️ 无社交链接")
    
    # Twitter 分析
    if socials.get("twitter"):
        tw_analysis = analyze_twitter(socials["twitter"])
        if tw_analysis.get("influence") in ["极高", "高"]:
            print(f"\n🌟 知名 Twitter!")
            print(f"   {tw_analysis.get('name', '')} - 影响力: {tw_analysis['influence']}")
    
    # 危险信号
    print(f"\n🚩 危险信号:")
    red_flags = detect_red_flags(token_info)
    if red_flags:
        for f in red_flags:
            emoji = "⚠️" if f["type"] == "warning" else "❌" if f["type"] == "danger" else "ℹ️"
            print(f"   {emoji} {f['msg']}")
    else:
        print("   ✅ 未发现明显危险信号")
    
    # 正面信号
    print(f"\n✅ 正面信号:")
    green_flags = detect_green_flags(token_info, socials)
    if green_flags:
        for f in green_flags:
            print(f"   ✅ {f['msg']}")
    else:
        print("   无特殊正面信号")
    
    # 创建者分析
    creator = token_info.get("mint", "")
    if creator:
        print(f"\n👤 创建者:")
        print(f"   地址: {creator[:10]}...{creator[-4:]}")
        print(f"   查看: https://solscan.io/account/{creator}")
    
    # 持仓大户
    print(f"\n🐋 前5大户:")
    holders = token_info.get("holders", [])
    if not holders:
        # 尝试获取
        try:
            import subprocess
            result = subprocess.run(
                ["python3", "/home/admin/Ziwei/scripts/token_background_check.py", address],
                capture_output=True, text=True, timeout=30
            )
            # 提取持仓信息
            lines = result.stdout.split("\n")
            in_holders = False
            for line in lines:
                if "持仓大户" in line:
                    in_holders = True
                if in_holders and line.strip():
                    print(line)
                if "集中度" in line:
                    break
        except:
            print("   无法获取持仓数据")
    
    # 最终评估
    print(f"\n{'='*70}")
    print(f"📋 最终评估")
    print(f"{'='*70}")
    
    score = 0
    reasons = []
    
    # 评分
    liq = float(token_info.get("liquidity", {}).get("usd", 0))
    if liq > 100000:
        score += 2
        reasons.append("流动性充足")
    elif liq > 50000:
        score += 1
        reasons.append("流动性一般")
    
    if socials.get("website") and socials.get("twitter"):
        score += 1
        reasons.append("有完整社交")
    
    vol = float(token_info.get("volume", {}).get("h24", 0))
    if vol > 50000:
        score += 1
        reasons.append("成交活跃")
    
    if len(red_flags) > 0:
        score -= len(red_flags)
        reasons.append(f"有 {len(red_flags)} 个风险点")
    
    # 输出评级
    if score >= 3:
        rating = "🟢 值得关注"
    elif score >= 1:
        rating = "🟡 一般"
    else:
        rating = "🔴 风险较高"
    
    print(f"评分: {score} 分")
    print(f"评级: {rating}")
    print(f"原因: {', '.join(reasons)}")
    
    return {
        "address": address,
        "score": score,
        "rating": rating,
        "red_flags": red_flags,
        "green_flags": green_flags
    }

if __name__ == "__main__":
    if not TOKEN_ADDRESS:
        print("用法: python3 advanced_background_check.py <代币地址>")
        sys.exit(1)
    
    comprehensive_check(TOKEN_ADDRESS)