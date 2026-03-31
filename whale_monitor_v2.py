#!/usr/bin/env python3
"""
大户实时监控系统 v2
- 使用公共 RPC + DexScreener API
- 实时监控大户交易
- 钉钉通知
"""

import json
import time
import requests
import urllib.request
from datetime import datetime
from collections import defaultdict
import os

# ============== 配置 ==============
RPC_URL = "https://api.mainnet-beta.solana.com"
DEXSCREENER_API = "https://api.dexscreener.com/latest"

# 追踪的大户钱包
WHALE_WALLETS = {
    "Fartcoin_Whale_1": "9SLPTL41SPsYkgdsMzdfJsxymEANKr5bYoBsQzJyKpKS",
    "Fartcoin_Whale_2": "E2RvJg2myWpKcbkhBuF81gfhYr6KvmNcDbSmr5qnatYy",
    "Fartcoin_Whale_3": "u6PJ8DtQuPFnfmwHbGFULQ4u4EgjDiyYKjVEsynXq2w",
    "Fartcoin_Whale_4": "4QuB7hY3H512CLG1orbVrA7HTeXbBYCPxBpNfQ6gs5ru",
    "Fartcoin_Whale_5": "7TWnq4WeYcwQWBCwKeEX2Q9xqVtthPGkB7adNvueuVuh",
    "Fartcoin_Whale_6": "JCNCMFXo5M5qwUPg2Utu1u6YWp3MbygxqBsBeXXJfrw",
}

# 关注的代币
TOKENS = {
    "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump": {"symbol": "FART", "name": "Fartcoin"},
    "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm": {"symbol": "WIF", "name": "dogwifhat"},
    "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263": {"symbol": "BONK", "name": "Bonk"},
    "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr": {"symbol": "POPCAT", "name": "Popcat"},
}

# 数据目录
DATA_DIR = "/home/admin/Ziwei/data/whale_monitor"
os.makedirs(DATA_DIR, exist_ok=True)

# ============== RPC 调用 ==============
def rpc_call(method, params=[], timeout=30):
    """调用 Solana RPC"""
    data = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(RPC_URL, data=data, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def get_recent_signatures(address, limit=5):
    """获取最近的交易签名"""
    result = rpc_call("getSignaturesForAddress", [address, {"limit": limit}])
    return result.get("result", [])

def get_transaction(sig):
    """获取交易详情"""
    result = rpc_call("getTransaction", [sig, {"encoding": "json", "maxSupportedTransactionVersion": 0}])
    return result.get("result")

# ============== 交易解析 ==============
def parse_transaction(tx_data, wallet_address):
    """解析交易，提取代币变化"""
    if not tx_data:
        return None
    
    meta = tx_data.get("meta", {})
    block_time = tx_data.get("blockTime", 0)
    
    post_balances = meta.get("postTokenBalances", [])
    pre_balances = meta.get("preTokenBalances", [])
    
    changes = []
    
    for post in post_balances:
        mint = post.get("mint", "")
        if mint not in TOKENS:
            continue
            
        post_amt = float(post.get("uiTokenAmount", {}).get("uiAmount", 0) or 0)
        
        # 找到对应的 pre balance
        pre_amt = 0
        for pre in pre_balances:
            if pre.get("mint") == mint and pre.get("ownerIndex") == post.get("ownerIndex"):
                pre_amt = float(pre.get("uiTokenAmount", {}).get("uiAmount", 0) or 0)
                break
        
        diff = post_amt - pre_amt
        if abs(diff) > 0:
            token_info = TOKENS[mint]
            changes.append({
                "token": token_info["symbol"],
                "action": "BUY" if diff > 0 else "SELL",
                "amount": abs(diff),
                "diff": diff
            })
    
    if changes:
        return {
            "time": datetime.fromtimestamp(block_time).strftime("%Y-%m-%d %H:%M:%S") if block_time else "",
            "timestamp": block_time,
            "changes": changes
        }
    return None

# ============== 价格获取 ==============
def get_token_price(token_address):
    """从 DexScreener 获取代币价格"""
    try:
        url = f"{DEXSCREENER_API}/dex/tokens/{token_address}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        if "pairs" in data and data["pairs"]:
            # 取流动性最高的 pair
            pair = sorted(data["pairs"], key=lambda x: x.get("liquidity", {}).get("usd", 0), reverse=True)[0]
            return {
                "price": float(pair.get("priceUsd", 0)),
                "price_native": float(pair.get("priceNative", 0)),
                "liquidity": float(pair.get("liquidity", {}).get("usd", 0)),
                "volume_24h": float(pair.get("volume", {}).get("h24", 0)),
                "price_change_24h": float(pair.get("priceChange", {}).get("h24", 0))
            }
    except Exception as e:
        print(f"获取价格失败: {e}")
    return None

# ============== 钉钉通知 ==============
def send_dingtalk(message):
    """发送钉钉通知"""
    webhook = os.environ.get("DINGTALK_WEBHOOK")
    if not webhook:
        print("未配置钉钉 Webhook")
        return False
    
    try:
        data = {
            "msgtype": "text",
            "text": {"content": message}
        }
        resp = requests.post(webhook, json=data, timeout=10)
        return resp.json().get("errcode") == 0
    except Exception as e:
        print(f"钉钉通知失败: {e}")
        return False

# ============== 记录已处理的交易 ==============
def load_processed_txs():
    """加载已处理的交易"""
    filepath = os.path.join(DATA_DIR, "processed_txs.json")
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return set(json.load(f))
    return set()

def save_processed_txs(txs):
    """保存已处理的交易"""
    filepath = os.path.join(DATA_DIR, "processed_txs.json")
    with open(filepath, "w") as f:
        json.dump(list(txs)[-1000:], f)  # 只保留最近1000条

# ============== 主监控循环 ==============
def monitor_whales(interval=60, once=False):
    """监控大户交易"""
    print("=" * 60)
    print("🐋 大户监控系统启动")
    print("=" * 60)
    print(f"监控钱包: {len(WHALE_WALLETS)} 个")
    print(f"关注代币: {len(TOKENS)} 个")
    print(f"轮询间隔: {interval} 秒")
    print("=" * 60)
    
    processed = load_processed_txs()
    round_num = 0
    
    while True:
        round_num += 1
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 第 {round_num} 轮扫描...")
        
        new_txs = 0
        
        for name, address in WHALE_WALLETS.items():
            try:
                # 获取最近交易
                sigs = get_recent_signatures(address, limit=3)
                
                for sig_data in sigs:
                    sig = sig_data.get("signature", "")
                    
                    if sig in processed:
                        continue
                    
                    # 解析交易
                    tx_data = get_transaction(sig)
                    result = parse_transaction(tx_data, address)
                    
                    if result and result["changes"]:
                        processed.add(sig)
                        new_txs += 1
                        
                        # 构建通知
                        msg_lines = [f"🚨 {name} 有新交易!"]
                        msg_lines.append(f"时间: {result['time']}")
                        
                        for c in result["changes"]:
                            emoji = "🟢" if c["action"] == "BUY" else "🔴"
                            msg_lines.append(f"{emoji} {c['action']} {c['amount']:,.0f} {c['token']}")
                        
                        msg = "\n".join(msg_lines)
                        print(f"\n{msg}")
                        
                        # 发送钉钉通知
                        send_dingtalk(msg)
                    
                    time.sleep(0.5)  # 避免请求过快
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"监控 {name} 失败: {e}")
        
        # 保存已处理的交易
        save_processed_txs(processed)
        
        print(f"\n本轮发现 {new_txs} 笔新交易")
        
        if once:
            break
        
        print(f"等待 {interval} 秒...")
        time.sleep(interval)

# ============== 价格监控 ==============
def monitor_prices():
    """监控代币价格"""
    print("\n" + "=" * 60)
    print("💰 代币价格")
    print("=" * 60)
    
    for address, info in TOKENS.items():
        price_data = get_token_price(address)
        if price_data:
            change_emoji = "📈" if price_data["price_change_24h"] > 0 else "📉"
            print(f"\n{info['symbol']} ({info['name']})")
            print(f"  价格: ${price_data['price']:.8f}")
            print(f"  24h变化: {change_emoji} {price_data['price_change_24h']:.2f}%")
            print(f"  流动性: ${price_data['liquidity']:,.0f}")
            print(f"  24h成交量: ${price_data['volume_24h']:,.0f}")
        time.sleep(0.3)

# ============== 入口 ==============
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--once":
            # 单次扫描
            monitor_whales(once=True)
        elif sys.argv[1] == "--prices":
            # 只看价格
            monitor_prices()
        elif sys.argv[1] == "--interval":
            # 自定义间隔
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            monitor_whales(interval=interval)
    else:
        # 默认：价格 + 监控
        monitor_prices()
        print("\n" + "=" * 60)
        input("按回车开始监控大户交易...")
        monitor_whales()