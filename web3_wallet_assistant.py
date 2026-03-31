#!/usr/bin/env python3
# =============================================================================
# Web3 智能钱包助手 - 多链资产统计系统
# 功能：实时统计 ETH/BTC/XRP/Ardor/NEM/Lisk/Waves 等多链钱包资产
# =============================================================================

import requests
import json
from datetime import datetime
from typing import Dict, List, Tuple
import time

class Web3WalletAssistant:
    """Web3 智能钱包助手"""

    def __init__(self):
        self.wallets = {
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
            "ignis": [  # IGNIS 与 Ardor 共享钱包地址
                "ARDOR-WQLF-GRME-LPBY-67H89",
                "ARDOR-GU9Q-ZQ34-RM3Z-BL55X",
                "ARDOR-TPCB-PJDK-3A3Z-8AEMH"
            ],
            "nem": ["NC6GC3BTGR4NTUXDEDV2WN2OOYHHTSIH4U4GPDM5"],
            "lisk": ["2132294612894392489L"],
            "waves": ["3PKchBBnwAkV1jEzcgZXBaFPQAVvfhSpgd5"],
            "moosecoin": ["14688830650090582803M"]
        }

        self.prices = {}
        self.balances = {}
        self.load_cache()

    def load_cache(self):
        """加载缓存数据"""
        try:
            with open("/home/admin/Ziwei/data/wallet_cache.json", "r") as f:
                cache = json.load(f)
                self.prices = cache.get("prices", {})
        except:
            pass

    def get_crypto_price(self, symbol: str) -> float:
        """获取加密货币实时价格 (USD)"""
        # CoinGecko API (免费，无需 API key)
        # 批量获取所有价格，减少 API 调用
        try:
            ids_map = {
                "ETH": "ethereum",
                "BTC": "bitcoin",
                "XRP": "ripple",
                "ARDOR": "ardor",
                "IGNIS": "ignis",
                "NEM": "nem",
                "LSK": "lisk",
                "WAVES": "waves"
            }

            if symbol in ids_map:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_map[symbol]}&vs_currencies=usd"
                data = requests.get(url, timeout=10).json()
                if ids_map[symbol] in data:
                    return data[ids_map[symbol]]["usd"]
        except Exception as e:
            pass

        # 返回缓存或默认价格
        return self.prices.get(symbol.lower(), 0.0)

    def check_eth_balance(self, address: str) -> float:
        """查询 ETH 余额"""
        try:
            url = "https://cloudflare-eth.com"
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
                    return balance_wei / 10**18
        except Exception as e:
            pass
        return 0.0

    def check_btc_balance(self, address: str) -> float:
        """查询 BTC 余额"""
        try:
            url = f"https://blockchain.info/balance?active={address}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if address in data:
                    return data[address]["final_balance"] / 10**8
        except Exception as e:
            pass
        return 0.0

    def check_xrp_balance(self, address: str) -> float:
        """查询 XRP 余额"""
        try:
            url = f"https://api.xrpscan.com/api/v1/account/{address}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                balance = data.get("Balance", "0")
                if isinstance(balance, str):
                    return float(balance) / 1_000_000
        except Exception as e:
            pass
        return 0.0

    def check_ardor_balance(self, address: str) -> float:
        """查询 Ardor 余额"""
        try:
            url = "https://ardor.jelurida.com/nxt"
            payload = {
                "requestType": "getAccount",
                "account": address
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                balance_nqt = data.get("balanceNQT", "0")
                return int(balance_nqt) / 10**8  # ARDOR
        except Exception as e:
            pass
        return 0.0

    def check_ignis_balance(self, address: str) -> float:
        """查询 IGNIS 余额 (Ardor 子链代币)"""
        try:
            url = "https://ardor.jelurida.com/nxt"
            payload = {
                "requestType": "getAccount",
                "account": address,
                "chain": 2  # chain 2 是 IGNIS
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                balance_nqt = data.get("balanceNQT", "0")
                return int(balance_nqt) / 10**8  # IGNIS
        except Exception as e:
            pass
        return 0.0

    def check_nem_balance(self, address: str) -> float:
        """查询 NEM 余额"""
        try:
            url = f"https://node1.nem.io:7891/account/get?address={address}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("account", {}).get("balance", 0) / 10**6
        except Exception as e:
            pass
        return 0.0

    def check_lisk_balance(self, address: str) -> float:
        """查询 Lisk 余额"""
        try:
            url = "https://api-service.lisk.com/api/v3/accounts/{address}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return float(data["data"]["token"]["balance"]) / 10**8
        except Exception as e:
            pass
        return 0.0

    def check_waves_balance(self, address: str) -> float:
        """查询 Waves 余额"""
        try:
            url = f"https://nodes.wavesnodes.com/addresses/balance/{address}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data["balance"] / 10**8
        except Exception as e:
            pass
        return 0.0

    def scan_all_wallets(self) -> Dict:
        """扫描所有钱包并返回余额"""
        print(f"\n{'='*70}")
        print(f"🔍 Web3 智能钱包助手 - 开始扫描")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")

        results = {}
        total_usd = 0.0

        # 获取所有价格
        print(f"\n💰 获取实时价格...")
        self.prices = {
            "eth": self.get_crypto_price("ETH"),
            "btc": self.get_crypto_price("BTC"),
            "xrp": self.get_crypto_price("XRP"),
            "ardor": self.get_crypto_price("ARDOR"),
            "ignis": self.get_crypto_price("IGNIS"),
            "nem": self.get_crypto_price("NEM"),
            "lisk": self.get_crypto_price("LSK"),
            "waves": self.get_crypto_price("WAVES")
        }

        # 扫描每个链
        chains = {
            "ETH": ("eth", self.check_eth_balance, "ETH"),
            "Bitcoin": ("bitcoin", self.check_btc_balance, "BTC"),
            "XRP": ("xrp", self.check_xrp_balance, "XRP"),
            "Ardor": ("ardor", self.check_ardor_balance, "ARDOR"),
            "IGNIS": ("ignis", self.check_ignis_balance, "IGNIS"),
            "NEM": ("nem", self.check_nem_balance, "XEM"),
            "Lisk": ("lisk", self.check_lisk_balance, "LSK"),
            "Waves": ("waves", self.check_waves_balance, "WAVES")
        }

        for chain_name, (chain_key, check_func, symbol) in chains.items():
            print(f"\n{'─'*70}")
            print(f"🔗 {chain_name} 钱包 ({len(self.wallets[chain_key])} 个)")
            print(f"{'─'*70}")

            chain_total = 0.0
            chain_wallets = []

            for i, addr in enumerate(self.wallets[chain_key]):
                balance = check_func(addr)
                chain_total += balance

                if balance > 0:
                    price = self.prices.get(chain_key, 0)
                    value_usd = balance * price
                    chain_wallets.append({
                        "address": addr[:10] + "..." + addr[-8:] if len(addr) > 18 else addr,
                        "full_address": addr,
                        "balance": balance,
                        "value_usd": value_usd
                    })
                    print(f"  ✅ [{i+1}] {addr[:10]}...{addr[-8:]}: {balance:.6f} {symbol} ≈ ${value_usd:.2f}")
                else:
                    print(f"  ⭕ [{i+1}] {addr[:10]}...{addr[-8:]}: 0.000000 {symbol}")

            chain_value_usd = chain_total * self.prices.get(chain_key, 0)
            total_usd += chain_value_usd

            results[chain_key] = {
                "symbol": symbol,
                "total_balance": chain_total,
                "total_usd": chain_value_usd,
                "price_usd": self.prices.get(chain_key, 0),
                "wallet_count": len(self.wallets[chain_key]),
                "nonzero_count": len(chain_wallets),
                "wallets": chain_wallets
            }

            print(f"\n  📊 {chain_name} 总计: {chain_total:.6f} {symbol} ≈ ${chain_value_usd:.2f}")

        # 汇总
        print(f"\n{'='*70}")
        print(f"💎 资产总览")
        print(f"{'='*70}")

        for chain_key in ["eth", "btc", "xrp", "ardor", "ignis", "nem", "lisk", "waves"]:
            if chain_key in results:
                r = results[chain_key]
                print(f"  {r['symbol']:8s}: {r['total_balance']:>15.6f}  ≈ ${r['total_usd']:>10.2f}")

        print(f"  {'─'*70}")
        print(f"  {'总资产':8s}: {'':>15}  ≈ ${total_usd:>10.2f} USD")
        print(f"{'='*70}")

        # 汇率转换 (CNY)
        try:
            cny_rate = 7.2  # 简化，可从 API 获取
            total_cny = total_usd * cny_rate
            print(f"\n  💴 人民币: ¥{total_cny:,.2f} CNY (汇率: 1 USD = {cny_rate} CNY)")
        except:
            pass

        # 保存缓存
        self.save_cache()

        # 保存结果
        self.save_results(results, total_usd)

        return {"results": results, "total_usd": total_usd}

    def save_cache(self):
        """保存价格缓存"""
        with open("/home/admin/Ziwei/data/wallet_cache.json", "w") as f:
            json.dump({"prices": self.prices, "timestamp": datetime.now().isoformat()}, f, indent=2)

    def save_results(self, results: Dict, total_usd: float):
        """保存扫描结果"""
        output_file = f"/home/admin/Ziwei/data/wallet_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_usd": total_usd,
                "prices": self.prices,
                "balances": results
            }, f, indent=2)

        # 同时更新最新结果文件
        latest_file = "/home/admin/Ziwei/data/wallet_latest.json"
        with open(latest_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_usd": total_usd,
                "prices": self.prices,
                "balances": results
            }, f, indent=2)

        print(f"\n💾 结果已保存: {output_file}")
        print(f"💾 最新结果: {latest_file}")

    def get_summary(self) -> str:
        """获取资产摘要 (用于通知)"""
        if not self.balances:
            return "暂无数据"

        return f"""
📊 Web3 智能钱包助手 - 资产摘要

⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💎 总资产: ${self.balances.get('total_usd', 0):,.2f} USD

详情:
{self.format_chain_summary()}
        """.strip()

    def format_chain_summary(self) -> str:
        """格式化链摘要"""
        lines = []
        results = self.balances.get("results", {})

        for chain_key in ["eth", "btc", "xrp", "ardor", "ignis", "nem", "lisk", "waves"]:
            if chain_key in results:
                r = results[chain_key]
                if r["total_balance"] > 0:
                    lines.append(f"  {r['symbol']:8s}: {r['total_balance']:>12.6f} ≈ ${r['total_usd']:>8.2f}")

        return "\n".join(lines) if lines else "  (无余额)"


if __name__ == "__main__":
    assistant = Web3WalletAssistant()
    result = assistant.scan_all_wallets()

    print(f"\n✅ 扫描完成！")
    print(f"\n{assistant.get_summary()}")