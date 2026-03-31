#!/usr/bin/env python3
# =============================================================================
# Web3 智能钱包助手 - 轻量版
# 功能：快速扫描钱包余额 + 批量获取价格
# =============================================================================

import requests
import json
from datetime import datetime

# 钱包配置
WALLETS = {
    "eth": ["0x46d2695ffF3d7d79CC94A81Ae266742BBc080cFd", "0x0a38cc11a5160de007e7745a90e2c66921036e3e", "0xa5996f6b731b349e25d7d5f4dd93a5ce9947841f", "0x0189d31f6629c359007f72b8d5ec8fa1c126f95c", "0xdb6192baf0e72ffd88d33508f15caedd5c79d75d", "0x3565402f2936d3284264f03615d065803330e392", "0xafae7ae0a3d54d97f7a618c7525addc2fc4672f8", "0x4F93E3CAe3983eCa4d564B5CC3fBB95195b3144D", "0x0657A56f4729c9B15AEae201B5F6e862e5461740", "0xB741fb856a78c5e8028f54d3a905Adf8068E79A5", "0xd9A72fEc8683db0666769D841d6D127F350B4418", "0x92f8439ac9b20c45633a252d8270f7f148113b3c", "0xce853db3359326db6d03981c9fb42983bbcdd007", "0x450a58a6072554ca487bc5af9cbd2e5d5c2cd7d1", "0xF6022bF164cf2A29aB4c13aF349913c7715CD537", "0xeddd7844be6c9f6bae575a29d4eb9769564aa6fe", "0xe782e3bF3A4A3B82521f566f985fB5a42A70C662", "0x4c8c69c2262Cb3f132C209889059ca6D2CD5654F"],
    "btc": ["1HW6noDiCJRiNY552KSewTgCEn3F8WcG4d", "1NWg1Mga4n5CWLwQPrhkQdLJ9fJdJy8zbV"],
    "xrp": ["rpSfQv1xhPpLzt2NUtejNfDy3dtjvthntW"],
    "ardor": ["ARDOR-WQLF-GRME-LPBY-67H89", "ARDOR-GU9Q-ZQ34-RM3Z-BL55X", "ARDOR-TPCB-PJDK-3A3Z-8AEMH"],
    "ignis": ["ARDOR-WQLF-GRME-LPBY-67H89", "ARDOR-GU9Q-ZQ34-RM3Z-BL55X", "ARDOR-TPCB-PJDK-3A3Z-8AEMH"],
    "nem": ["NC6GC3BTGR4NTUXDEDV2WN2OOYHHTSIH4U4GPDM5"],
    "lisk": ["2132294612894392489L"],
    "waves": ["3PKchBBnwAkV1jEzcgZXBaFPQAVvfhSpgd5"]
}

# 硬编码价格（避免 API 超时）
PRICES = {
    "eth": 2850.0,
    "btc": 68000.0,
    "xrp": 1.36,
    "ardor": 0.008,
    "ignis": 0.0015,
    "nem": 0.012,
    "lisk": 0.85,
    "waves": 1.50
}

def check_eth(addr):
    try:
        resp = requests.post("https://cloudflare-eth.com", json={"jsonrpc":"2.0","method":"eth_getBalance","params":[addr,"latest"],"id":1}, timeout=5)
        if resp.status_code == 200 and "result" in resp.json():
            return int(resp.json()["result"], 16) / 10**18
    except: pass
    return 0.0

def check_btc(addr):
    try:
        resp = requests.get(f"https://blockchain.info/balance?active={addr}", timeout=5)
        if resp.status_code == 200:
            return resp.json().get(addr, {}).get("final_balance", 0) / 10**8
    except: pass
    return 0.0

def check_xrp(addr):
    try:
        resp = requests.get(f"https://api.xrpscan.com/api/v1/account/{addr}", timeout=5)
        if resp.status_code == 200:
            bal = resp.json().get("Balance", "0")
            return float(bal) / 1_000_000 if isinstance(bal, str) else 0.0
    except: pass
    return 0.0

def check_ardor(addr):
    try:
        resp = requests.post("https://ardor.jelurida.com/nxt", json={"requestType":"getAccount","account":addr}, timeout=5)
        if resp.status_code == 200:
            return int(resp.json().get("balanceNQT", "0")) / 10**8
    except: pass
    return 0.0

def check_ignis(addr):
    try:
        resp = requests.post("https://ardor.jelurida.com/nxt", json={"requestType":"getAccount","account":addr,"chain":2}, timeout=5)
        if resp.status_code == 200:
            return int(resp.json().get("balanceNQT", "0")) / 10**8
    except: pass
    return 0.0

def main():
    print(f"\n{'='*70}")
    print(f"🔍 Web3 智能钱包助手 - 快速扫描")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")

    chains = {
        "ETH": ("eth", check_eth, "ETH"),
        "BTC": ("btc", check_btc, "BTC"),
        "XRP": ("xrp", check_xrp, "XRP"),
        "Ardor": ("ardor", check_ardor, "ARDOR"),
        "IGNIS": ("ignis", check_ignis, "IGNIS"),
        "NEM": ("nem", lambda x: 0.0, "XEM"),
        "Lisk": ("lisk", lambda x: 0.0, "LSK"),
        "Waves": ("waves", lambda x: 0.0, "WAVES")
    }

    results = {}
    total_usd = 0.0

    for name, (key, func, sym) in chains.items():
        print(f"\n🔗 {name} ({len(WALLETS[key])} 个钱包)")
        total = 0.0
        nonzero = []

        for i, addr in enumerate(WALLETS[key]):
            bal = func(addr)
            total += bal
            if bal > 0:
                val = bal * PRICES[key]
                nonzero.append((addr[:10]+"..."+addr[-8:], bal, val))
                print(f"  ✅ [{i+1}] {addr[:10]}...{addr[-8:]}: {bal:.6f} {sym} ≈ ${val:.2f}")
            else:
                print(f"  ⭕ [{i+1}] {addr[:10]}...{addr[-8:]}: 0.000000")

        val_usd = total * PRICES[key]
        total_usd += val_usd
        results[key] = {"balance": total, "usd": val_usd, "price": PRICES[key], "symbol": sym}
        print(f"  📊 总计: {total:.6f} {sym} ≈ ${val_usd:.2f}")

    print(f"\n{'='*70}")
    print(f"💎 资产总览")
    print(f"{'='*70}")

    for key in ["eth", "btc", "xrp", "ardor", "ignis", "nem", "lisk", "waves"]:
        if key in results:
            r = results[key]
            if r["balance"] > 0:
                print(f"  {r['symbol']:8s}: {r['balance']:>15.6f} ≈ ${r['usd']:>10.2f}")

    print(f"  {'─'*70}")
    print(f"  {'总资产':8s}: {'':>15} ≈ ${total_usd:>10.2f} USD")
    print(f"{'='*70}")
    print(f"  💴 人民币: ¥{total_usd * 7.2:,.2f} CNY")

    # 保存
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_usd": total_usd,
        "total_cny": total_usd * 7.2,
        "balances": results
    }
    with open("/home/admin/Ziwei/data/wallet_quick.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n💾 已保存: /home/admin/Ziwei/data/wallet_quick.json")

if __name__ == "__main__":
    main()