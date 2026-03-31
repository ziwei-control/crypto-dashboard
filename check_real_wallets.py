#!/usr/bin/env python3
# =============================================================================
# 真实钱包余额查询脚本
# 功能：查询所有配置钱包的真实余额
# =============================================================================

import requests
import json
from datetime import datetime

# 钱包配置
WALLET_CONFIG = {
    "eth": [
        "0x46d2695ffF3d7d79CC94A81Ae266742BBc080cFd",
        "0x0a38cc11a5160de007e7745a90e2c66921036e3e",
        "0xa5996f6b731b349e25d7d5f4dd93a5ce9947841f",
        "0x0189d31f6629c359007f72b8d5ec8fa1c126f95c",
        "0xdb6192baf0e72ffd88d33508f15caedd5c79d75d",
        "0x3565402f2936d3284264f03615d065803330e392",
        "0xafae7ae0a3d54d97f7a618c7525addc2fc4672f8",
        "0x4F93E3CAe3983eCa4d564B5CC3fBB95195b3144D",
        "0x0657A56f4729c9B15AEae201B5F6e862e5461740",
        "0xB741fb856a78c5e8028f54d3a905Adf8068E79A5",
        "0xd9A72fEc8683db0666769D841d6D127F350B4418",
        "0x92f8439ac9b20c45633a252d8270f7f148113b3c",
        "0xce853db3359326db6d03981c9fb42983bbcdd007",
        "0x450a58a6072554ca487bc5af9cbd2e5d5c2cd7d1",
        "0xF6022bF164cf2A29aB4c13aF349913c7715CD537",
        "0xeddd7844be6c9f6bae575a29d4eb9769564aa6fe",
        "0xe782e3bF3A4A3B82521f566f985fB5a42A70C662",
        "0x4c8c69c2262Cb3f132C209889059ca6D2CD5654F"
    ],
    "bitcoin": [
        "1HW6noDiCJRiNY552KSewTgCEn3F8WcG4d",
        "1NWg1Mga4n5CWLwQPrhkQdLJ9fJdJy8zbV"
    ],
    "xrp": ["rpSfQv1xhPpLzt2NUtejNfDy3dtjvthntW"],
    "ardor": [
        "ARDOR-WQLF-GRME-LPBY-67H89",
        "ARDOR-GU9Q-ZQ34-RM3Z-BL55X",
        "ARDOR-TPCB-PJDK-3A3Z-8AEMH"
    ],
    "nem": ["NC6GC3BTGR4NTUXDEDV2WN2OOYHHTSIH4U4GPDM5"],
    "lisk": ["2132294612894392489L"],
    "waves": ["3PKchBBnwAkV1jEzcgZXBaFPQAVvfhSpgd5"],
    "moosecoin": ["14688830650090582803M"]
}

# ETH 价格 (USD)
ETH_PRICE = 2800.0  # 需要实时更新
BTC_PRICE = 65000.0  # 需要实时更新
XRP_PRICE = 0.50  # 需要实时更新

def check_eth_balance(address):
    """查询 ETH 余额 (使用免费的 Cloudflare API)"""
    try:
        url = f"https://cloudflare-eth.com"
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [address, "latest"],
            "id": 1
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if "result" in result and result["result"]:
                balance_wei = int(result["result"], 16)
                balance_eth = balance_wei / 10**18
                return balance_eth
    except Exception as e:
        print(f"  ❌ 查询失败: {e}")
    return 0.0

def check_btc_balance(address):
    """查询 BTC 余额 (使用 blockchain.com API)"""
    try:
        url = f"https://blockchain.info/balance?active={address}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if address in data:
                return data[address]["final_balance"] / 10**8  # 转换为 BTC
    except Exception as e:
        print(f"  ❌ 查询失败: {e}")
    return 0.0

def check_xrp_balance(address):
    """查询 XRP 余额 (使用 xrpscan.com API)"""
    try:
        url = f"https://api.xrpscan.com/api/v1/account/{address}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("Balance", 0) / 1_000_000  # 转换为 XRP
    except Exception as e:
        print(f"  ❌ 查询失败: {e}")
    return 0.0

def query_wallet_balances():
    """查询所有钱包余额"""
    print("=" * 70)
    print(f"🔍 真实钱包余额查询 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    total_usdt = 0.0
    results = {}

    # 查询 ETH 钱包
    print(f"\n💎 Ethereum 钱包 ({len(WALLET_CONFIG['eth'])} 个):")
    eth_total = 0.0
    eth_nonzero = []

    for i, addr in enumerate(WALLET_CONFIG['eth']):
        balance = check_eth_balance(addr)
        eth_total += balance
        if balance > 0:
            eth_nonzero.append({
                "address": addr[:10] + "..." + addr[-8:],
                "balance": balance,
                "value_usd": balance * ETH_PRICE
            })
            print(f"  ✅ [{i+1}] {addr[:10]}...{addr[-8:]}: {balance:.4f} ETH ≈ ${balance * ETH_PRICE:.2f}")
        else:
            print(f"  ⭕ [{i+1}] {addr[:10]}...{addr[-8:]}: 0.0000 ETH")

    eth_value_usd = eth_total * ETH_PRICE
    total_usdt += eth_value_usd
    results["eth"] = {
        "total_eth": eth_total,
        "total_usd": eth_value_usd,
        "nonzero_count": len(eth_nonzero),
        "nonzero_wallets": eth_nonzero
    }

    # 查询 BTC 钱包
    print(f"\n₿ Bitcoin 钱包 ({len(WALLET_CONFIG['bitcoin'])} 个):")
    btc_total = 0.0
    btc_nonzero = []

    for i, addr in enumerate(WALLET_CONFIG['bitcoin']):
        balance = check_btc_balance(addr)
        btc_total += balance
        if balance > 0:
            btc_nonzero.append({
                "address": addr[:10] + "..." + addr[-8:],
                "balance": balance,
                "value_usd": balance * BTC_PRICE
            })
            print(f"  ✅ [{i+1}] {addr}: {balance:.8f} BTC ≈ ${balance * BTC_PRICE:.2f}")
        else:
            print(f"  ⭕ [{i+1}] {addr}: 0.00000000 BTC")

    btc_value_usd = btc_total * BTC_PRICE
    total_usdt += btc_value_usd
    results["btc"] = {
        "total_btc": btc_total,
        "total_usd": btc_value_usd,
        "nonzero_count": len(btc_nonzero),
        "nonzero_wallets": btc_nonzero
    }

    # 查询 XRP 钱包
    print(f"\n🟡 XRP 钱包 ({len(WALLET_CONFIG['xrp'])} 个):")
    xrp_total = 0.0
    for addr in WALLET_CONFIG['xrp']:
        balance = check_xrp_balance(addr)
        xrp_total += balance
        print(f"  {addr}: {balance:.2f} XRP ≈ ${balance * XRP_PRICE:.2f}")

    xrp_value_usd = xrp_total * XRP_PRICE
    total_usdt += xrp_value_usd
    results["xrp"] = {
        "total_xrp": xrp_total,
        "total_usd": xrp_value_usd
    }

    # 其他链 (需要专用API，暂时标记为待查询)
    print(f"\n⏳ 其他链钱包 (需要专用API):")
    print(f"  Ardor: {len(WALLET_CONFIG['ardor'])} 个钱包")
    print(f"  NEM: {len(WALLET_CONFIG['nem'])} 个钱包")
    print(f"  Lisk: {len(WALLET_CONFIG['lisk'])} 个钱包")
    print(f"  Waves: {len(WALLET_CONFIG['waves'])} 个钱包")
    print(f"  MooseCoin: {len(WALLET_CONFIG['moosecoin'])} 个钱包")

    # 总结
    print(f"\n" + "=" * 70)
    print(f"💰 总资产汇总:")
    print(f"  ETH 总计: {eth_total:.4f} ETH ≈ ${eth_value_usd:.2f}")
    print(f"  BTC 总计: {btc_total:.8f} BTC ≈ ${btc_value_usd:.2f}")
    print(f"  XRP 总计: {xrp_total:.2f} XRP ≈ ${xrp_value_usd:.2f}")
    print(f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  🎯 总资产: ${total_usdt:.2f} USD")
    print("=" * 70)

    return results, total_usdt

if __name__ == "__main__":
    results, total_usdt = query_wallet_balances()

    # 保存结果
    output_file = f"/home/admin/Ziwei/data/wallet_balances_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_usdt": total_usdt,
            "eth_price": ETH_PRICE,
            "btc_price": BTC_PRICE,
            "xrp_price": XRP_PRICE,
            "details": results
        }, f, indent=2)

    print(f"\n💾 结果已保存到: {output_file}")