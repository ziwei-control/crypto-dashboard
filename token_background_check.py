#!/usr/bin/env python3
"""
代币背景调查脚本
调查新币的背景、团队、持仓分布等
"""

import requests
import json
import sys
from datetime import datetime

# DexScreener API
DEXSCREENER_API = "https://api.dexscreener.com"

# Solana RPC (公共)
SOLANA_RPC = "https://api.mainnet-beta.solana.com"

def get_token_info(address):
    """从 DexScreener 获取代币信息"""
    try:
        url = f"{DEXSCREENER_API}/latest/dex/tokens/{address}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("pairs"):
                return data["pairs"][0]  # 返回主要交易对
    except Exception as e:
        print(f"获取代币信息失败: {e}")
    return None

def get_top_holders(address, limit=10):
    """获取持仓大户（Solana）"""
    try:
        # 使用 QuickNode 演示端点
        url = "https://docs-demo.solana-mainnet.quiknode.pro/"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenLargestAccounts",
            "params": [address]
        }
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "result" in data and data["result"].get("value"):
                holders = data["result"]["value"][:limit]
                return holders
    except Exception as e:
        print(f"获取持仓大户失败: {e}")
    return []

def analyze_creator_wallet(wallet_address):
    """分析创建者钱包"""
    print(f"\n🔍 分析创建者钱包: {wallet_address[:8]}...{wallet_address[-4:]}")
    
    # 这里可以扩展：查看创建者的历史交易、其他项目等
    # 目前简化处理
    return {
        "address": wallet_address,
        "note": "需要手动查看 Solscan"
    }

def check_social_links(token_info):
    """检查社交链接"""
    socials = {}
    
    if token_info.get("info"):
        info = token_info["info"]
        if info.get("websites"):
            socials["website"] = info["websites"][0].get("url", "")
        if info.get("socials"):
            for s in info["socials"]:
                socials[s.get("type", "unknown")] = s.get("url", "")
    
    return socials

def calculate_holder_concentration(holders):
    """计算持仓集中度"""
    if not holders:
        return None
    
    total = sum(float(h.get("amount", 0)) for h in holders)
    if total == 0:
        return None
    
    top1 = float(holders[0].get("amount", 0)) / total * 100 if holders else 0
    top3 = sum(float(h.get("amount", 0)) for h in holders[:3]) / total * 100 if len(holders) >= 3 else 0
    top10 = sum(float(h.get("amount", 0)) for h in holders[:10]) / total * 100
    
    return {
        "top1_pct": round(top1, 2),
        "top3_pct": round(top3, 2),
        "top10_pct": round(top10, 2)
    }

def investigate_token(address):
    """调查代币"""
    print(f"\n{'='*70}")
    print(f"🔍 代币背景调查: {address}")
    print(f"{'='*70}")
    
    # 1. 获取基本信息
    print("\n📋 获取代币信息...")
    token_info = get_token_info(address)
    
    if not token_info:
        print("❌ 无法获取代币信息")
        return
    
    # 基本信息
    print(f"\n📊 基本信息:")
    print(f"   名称: {token_info.get('baseToken', {}).get('name', '?')}")
    print(f"   代号: {token_info.get('baseToken', {}).get('symbol', '?')}")
    print(f"   价格: ${token_info.get('priceUsd', '?')}")
    print(f"   流动性: ${float(token_info.get('liquidity', {}).get('usd', 0)):,.0f}")
    print(f"   24h成交量: ${float(token_info.get('volume', {}).get('h24', 0)):,.0f}")
    print(f"   24h涨跌: {token_info.get('priceChange', {}).get('h24', 0)}%")
    
    # 创建时间
    pair_created = token_info.get('pairCreatedAt')
    if pair_created:
        age_hours = (datetime.now().timestamp() * 1000 - pair_created) / 3600000
        if age_hours < 24:
            print(f"   年龄: {age_hours:.1f} 小时 🆕")
        else:
            print(f"   年龄: {age_hours/24:.1f} 天")
    
    # 2. 检查社交链接
    print(f"\n🌐 社交链接:")
    socials = check_social_links(token_info)
    
    if socials.get("website"):
        print(f"   官网: {socials['website']}")
    if socials.get("twitter"):
        print(f"   Twitter: {socials['twitter']}")
    if socials.get("telegram"):
        print(f"   Telegram: {socials['telegram']}")
    
    if not socials:
        print("   ⚠️ 未找到社交链接")
    
    # 3. 检查是否被标记
    print(f"\n🏷️ 标签:")
    labels = token_info.get("labels", [])
    if labels:
        for label in labels:
            print(f"   • {label}")
    else:
        print("   无特殊标签")
    
    # 4. 持仓分布
    print(f"\n🐋 持仓大户分析...")
    holders = get_top_holders(address)
    
    if holders:
        print(f"   前10大户持仓:")
        for i, h in enumerate(holders[:5], 1):
            addr = h.get("address", "?")
            amount = float(h.get("amount", 0))
            pct = float(h.get("uiAmount", 0)) if h.get("uiAmount") else 0
            print(f"   {i}. {addr[:8]}...{addr[-4:]} | {amount:,.0f} ({pct:.4f}%)")
        
        concentration = calculate_holder_concentration(holders)
        if concentration:
            print(f"\n   📊 持仓集中度:")
            print(f"      前1大户: {concentration['top1_pct']}%")
            print(f"      前3大户: {concentration['top3_pct']}%")
            print(f"      前10大户: {concentration['top10_pct']}%")
            
            if concentration['top1_pct'] > 50:
                print(f"      ⚠️ 高度集中！前1大户持有超过50%")
            elif concentration['top3_pct'] > 70:
                print(f"      ⚠️ 较为集中，前3大户持有超过70%")
            else:
                print(f"      ✅ 分散度较好")
    else:
        print("   无法获取持仓数据")
    
    # 5. 创建者信息
    creator = token_info.get("mint", "")
    if creator:
        print(f"\n👤 创建者/铸造地址:")
        print(f"   {creator}")
        print(f"   查看详情: https://solscan.io/account/{creator}")
    
    # 6. 风险评估
    print(f"\n⚠️ 风险评估:")
    risks = []
    
    liq = float(token_info.get('liquidity', {}).get('usd', 0))
    if liq < 10000:
        risks.append("流动性过低 (<$10K)")
    elif liq < 50000:
        risks.append("流动性较低 (<$50K)")
    
    if not socials:
        risks.append("无社交链接")
    
    if holders and concentration and concentration['top1_pct'] > 50:
        risks.append("持仓高度集中")
    
    if token_info.get("priceChange", {}).get("h24", 0) < -20:
        risks.append("24h跌幅超过20%")
    
    if risks:
        for r in risks:
            print(f"   ❌ {r}")
    else:
        print("   ✅ 未发现明显风险")
    
    # 7. 调查建议
    print(f"\n📝 后续调查建议:")
    print(f"   1. 查看 Twitter 是否有真人互动")
    print(f"   2. 查看创建者钱包历史交易: https://solscan.io/account/{creator if creator else address}")
    print(f"   3. 检查大户钱包是否有关联交易")
    print(f"   4. 查看合约是否有后门: https://tokensniffer.com/")
    
    return {
        "address": address,
        "name": token_info.get('baseToken', {}).get('name', '?'),
        "symbol": token_info.get('baseToken', {}).get('symbol', '?'),
        "socials": socials,
        "holders": holders[:5] if holders else [],
        "concentration": concentration if holders else None,
        "risks": risks
    }

def main():
    if len(sys.argv) < 2:
        print("用法: python3 token_background_check.py <代币地址>")
        print("示例: python3 token_background_check.py 7oXNE1dbpHUp6dn1JF8pRgCtzfCy4P2FuBneWjZHpump")
        sys.exit(1)
    
    address = sys.argv[1]
    investigate_token(address)

if __name__ == "__main__":
    main()