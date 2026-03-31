#!/usr/bin/env python3
"""
大户新币猎手 - 发现大户买入的新币
核心逻辑：监控大户买入我们不认识的代币 = 早期机会信号
"""

import json
import time
import requests
import urllib.request
from datetime import datetime
import os

# ============== 配置 ==============
RPC_URL = "https://api.mainnet-beta.solana.com"
DEXSCREENER_API = "https://api.dexscreener.com/latest"

# 追踪的大户钱包
WHALE_WALLETS = {
    "Whale_1": "9SLPTL41SPsYkgdsMzdfJsxymEANKr5bYoBsQzJyKpKS",
    "Whale_2": "E2RvJg2myWpKcbkhBuF81gfhYr6KvmNcDbSmr5qnatYy",
    "Whale_3": "u6PJ8DtQuPFnfmwHbGFULQ4u4EgjDiyYKjVEsynXq2w",
    "Whale_4": "4QuB7hY3H512CLG1orbVrA7HTeXbBYCPxBpNfQ6gs5ru",
    "Whale_5": "7TWnq4WeYcwQWBCwKeEX2Q9xqVtthPGkB7adNvueuVuh",
    "Whale_6": "JCNCMFXo5M5qwUPg2Utu1u6YWp3MbygxqBsBeXXJfrw",
}

# 已知的主流代币（这些不算新币）
KNOWN_TOKENS = {
    # Solana 主流
    "So11111111111111111111111111111111111111112": "SOL",
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC",
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCeYBenQNYs": "USDT",
    
    # 老牌 Meme
    "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump": "FART",
    "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm": "WIF",
    "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263": "BONK",
    "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr": "POPCAT",
    
    # 其他主流
    "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN": "JUP",
    "mSoLzYCxHdYgdzU16g5QSh3i5K3h3JZqN8JDeF7GkpD": "mSOL",
    "7dHbWXmci3dT8UFYWYZweBLXgycu7Y3iL6trKn1Y7ARj": "stSOL",
}

# 数据目录
DATA_DIR = "/home/admin/Ziwei/data/whale_hunter"
os.makedirs(DATA_DIR, exist_ok=True)

# ============== RPC 调用 ==============
def rpc_call(method, params=[], timeout=30):
    data = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(RPC_URL, data=data, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def get_recent_signatures(address, limit=10):
    result = rpc_call("getSignaturesForAddress", [address, {"limit": limit}])
    return result.get("result", [])

def get_transaction(sig):
    result = rpc_call("getTransaction", [sig, {"encoding": "json", "maxSupportedTransactionVersion": 0}])
    return result.get("result")

# ============== 代币信息获取 ==============
def get_token_info(mint):
    """从 DexScreener 获取代币信息"""
    try:
        url = f"{DEXSCREENER_API}/dex/tokens/{mint}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        if "pairs" in data and data["pairs"]:
            # 取 Solana 链上流动性最高的 pair
            sol_pairs = [p for p in data["pairs"] if p.get("chainId") == "solana"]
            if not sol_pairs:
                sol_pairs = data["pairs"]
            
            pair = sorted(sol_pairs, key=lambda x: x.get("liquidity", {}).get("usd", 0), reverse=True)[0]
            
            return {
                "symbol": pair.get("baseToken", {}).get("symbol", "UNKNOWN"),
                "name": pair.get("baseToken", {}).get("name", "Unknown"),
                "price": float(pair.get("priceUsd", 0) or 0),
                "liquidity": float(pair.get("liquidity", {}).get("usd", 0) or 0),
                "volume_24h": float(pair.get("volume", {}).get("h24", 0) or 0),
                "price_change_24h": float(pair.get("priceChange", {}).get("h24", 0) or 0),
                "pair_address": pair.get("pairAddress", ""),
                "created_at": pair.get("pairCreatedAt", 0)
            }
    except Exception as e:
        print(f"  获取代币信息失败: {e}")
    return None

# ============== 交易解析 ==============
def parse_transaction(tx_data):
    """解析交易，提取所有代币变化"""
    if not tx_data:
        return None
    
    meta = tx_data.get("meta", {})
    block_time = tx_data.get("blockTime", 0)
    
    post_balances = meta.get("postTokenBalances", [])
    pre_balances = meta.get("preTokenBalances", [])
    
    changes = []
    
    for post in post_balances:
        mint = post.get("mint", "")
        post_amt = float(post.get("uiTokenAmount", {}).get("uiAmount", 0) or 0)
        
        pre_amt = 0
        for pre in pre_balances:
            if pre.get("mint") == mint and pre.get("ownerIndex") == post.get("ownerIndex"):
                pre_amt = float(pre.get("uiTokenAmount", {}).get("uiAmount", 0) or 0)
                break
        
        diff = post_amt - pre_amt
        if abs(diff) > 0:
            is_known = mint in KNOWN_TOKENS
            changes.append({
                "mint": mint,
                "action": "BUY" if diff > 0 else "SELL",
                "amount": abs(diff),
                "diff": diff,
                "is_new_token": not is_known,
                "known_symbol": KNOWN_TOKENS.get(mint, "")
            })
    
    if changes:
        return {
            "time": datetime.fromtimestamp(block_time).strftime("%Y-%m-%d %H:%M:%S") if block_time else "",
            "timestamp": block_time,
            "changes": changes
        }
    return None

# ============== 记录已处理 ==============
def load_processed():
    filepath = os.path.join(DATA_DIR, "processed.json")
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return set(json.load(f))
    return set()

def save_processed(data):
    filepath = os.path.join(DATA_DIR, "processed.json")
    with open(filepath, "w") as f:
        json.dump(list(data)[-500:], f)

def load_discovered_tokens():
    """加载已发现的新币"""
    filepath = os.path.join(DATA_DIR, "discovered_tokens.json")
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return {}

def save_discovered_tokens(data):
    filepath = os.path.join(DATA_DIR, "discovered_tokens.json")
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

# ============== 钉钉通知 ==============
def send_dingtalk(message):
    webhook = os.environ.get("DINGTALK_WEBHOOK")
    if not webhook:
        return False
    try:
        data = {"msgtype": "text", "text": {"content": message}}
        resp = requests.post(webhook, json=data, timeout=10)
        return resp.json().get("errcode") == 0
    except:
        return False

# ============== 主监控 ==============
def hunt_new_tokens(once=False, interval=120):
    """猎杀新币：监控大户买入新代币"""
    
    print("=" * 70)
    print("🎯 大户新币猎手启动")
    print("=" * 70)
    print(f"监控钱包: {len(WHALE_WALLETS)} 个")
    print(f"已知代币: {len(KNOWN_TOKENS)} 个")
    print(f"目标: 发现大户买入的新币 🚀")
    print("=" * 70)
    
    processed = load_processed()
    discovered = load_discovered_tokens()
    round_num = 0
    
    while True:
        round_num += 1
        print(f"\n{'='*60}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 第 {round_num} 轮猎杀...")
        print("=" * 60)
        
        new_finds = 0
        
        for name, address in WHALE_WALLETS.items():
            try:
                print(f"\n🔍 扫描 {name}...")
                
                sigs = get_recent_signatures(address, limit=5)
                
                for sig_data in sigs:
                    sig = sig_data.get("signature", "")
                    
                    if sig in processed:
                        continue
                    
                    tx_data = get_transaction(sig)
                    result = parse_transaction(tx_data)
                    
                    if result and result["changes"]:
                        processed.add(sig)
                        
                        # 检查是否有新币买入
                        for change in result["changes"]:
                            if change["action"] == "BUY" and change["is_new_token"]:
                                new_finds += 1
                                mint = change["mint"]
                                amount = change["amount"]
                                
                                print(f"\n{'🚨'*30}")
                                print(f"🎯 发现新币买入！")
                                print(f"   大户: {name}")
                                print(f"   时间: {result['time']}")
                                print(f"   代币: {mint}")
                                print(f"   数量: {amount:,.0f}")
                                print(f"{'🚨'*30}")
                                
                                # 获取代币信息
                                print(f"\n📊 获取代币信息...")
                                token_info = get_token_info(mint)
                                
                                if token_info:
                                    print(f"   名称: {token_info['symbol']} - {token_info['name']}")
                                    print(f"   价格: ${token_info['price']:.10f}")
                                    print(f"   流动性: ${token_info['liquidity']:,.0f}")
                                    print(f"   24h成交量: ${token_info['volume_24h']:,.0f}")
                                    
                                    # 计算买入金额
                                    buy_usd = amount * token_info['price'] if token_info['price'] > 0 else 0
                                    print(f"   买入金额: ~${buy_usd:,.0f}")
                                    
                                    # 保存发现
                                    discovered[mint] = {
                                        "symbol": token_info['symbol'],
                                        "name": token_info['name'],
                                        "price": token_info['price'],
                                        "liquidity": token_info['liquidity'],
                                        "discovered_by": name,
                                        "discovered_at": result['time'],
                                        "buy_amount": amount,
                                        "buy_usd": buy_usd
                                    }
                                    save_discovered_tokens(discovered)
                                    
                                    # 发送通知
                                    msg = f"""🚨 发现大户买新币！

大户: {name}
代币: {token_info['symbol']} ({token_info['name']})
价格: ${token_info['price']:.10f}
流动性: ${token_info['liquidity']:,.0f}
买入: {amount:,.0f} (~${buy_usd:,.0f})

合约: {mint}
时间: {result['time']}"""
                                    send_dingtalk(msg)
                                else:
                                    print(f"   ⚠️ 无法获取代币信息，可能太新或非 DEX 代币")
                            
                            elif change["action"] == "SELL" and not change["is_new_token"]:
                                # 已知代币的卖出也记录一下
                                print(f"   📉 卖出 {change['known_symbol']}: {change['amount']:,.0f}")
                    
                    time.sleep(0.5)
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   扫描 {name} 失败: {e}")
        
        save_processed(processed)
        
        print(f"\n📊 本轮发现 {new_finds} 个新币买入")
        
        if once:
            break
        
        print(f"\n⏳ 等待 {interval} 秒后继续...")
        time.sleep(interval)

# ============== 查看已发现的新币 ==============
def show_discovered():
    """显示已发现的新币"""
    discovered = load_discovered_tokens()
    
    if not discovered:
        print("暂未发现新币")
        return
    
    print("=" * 70)
    print("🎯 已发现的新币")
    print("=" * 70)
    
    for mint, info in discovered.items():
        print(f"\n🪙 {info['symbol']} - {info['name']}")
        print(f"   价格: ${info['price']:.10f}")
        print(f"   流动性: ${info['liquidity']:,.0f}")
        print(f"   发现者: {info['discovered_by']}")
        print(f"   买入: {info['buy_amount']:,.0f} (~${info['buy_usd']:,.0f})")
        print(f"   合约: {mint}")

# ============== 入口 ==============
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--once":
            hunt_new_tokens(once=True)
        elif sys.argv[1] == "--show":
            show_discovered()
        elif sys.argv[1] == "--interval":
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 120
            hunt_new_tokens(interval=interval)
    else:
        hunt_new_tokens()