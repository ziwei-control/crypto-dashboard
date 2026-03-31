#!/usr/bin/env python3
"""
Meme币狙击手 - 实时监控新上线代币
高风险！仅用于小额测试
"""

import requests
import json
import time
from datetime import datetime

class MemeSniper:
    def __init__(self):
        self.dex_url = "https://api.dexscreener.com/latest/dex"
        self.min_liquidity = 500  # 最小流动性$500
        self.max_age_hours = 1     # 最大上线时间1小时
        
    def scan_new_tokens(self, chain='solana'):
        """扫描新代币"""
        print(f"\n🔍 扫描 {chain} 链新代币...")
        
        try:
            # 获取代币列表
            url = f"{self.dex_url}/tokens/search?q={chain}"
            resp = requests.get(
                f"https://api.dexscreener.com/token-boosts/top/v1",
                timeout=10
            )
            
            if resp.status_code == 200:
                tokens = resp.json()
                return tokens
        except Exception as e:
            print(f"扫描失败: {e}")
            return []
        
        return []
    
    def scan_pump_fun(self):
        """扫描pump.fun新币"""
        print("\n🔥 扫描 pump.fun 新币...")
        
        # 使用 DexScreener API
        try:
            # 获取Solana上的新币
            resp = requests.get(
                "https://api.dexscreener.com/latest/dex/search?q=solana",
                timeout=10
            )
            
            if resp.status_code == 200:
                data = resp.json()
                pairs = data.get('pairs', [])
                
                # 筛选新币
                new_tokens = []
                for pair in pairs[:20]:
                    created = pair.get('pairCreatedAt', 0)
                    if created:
                        age = (time.time() * 1000 - created) / 1000 / 3600  # 小时
                        if age < self.max_age_hours:
                            liquidity = pair.get('liquidity', {}).get('usd', 0)
                            if liquidity >= self.min_liquidity:
                                new_tokens.append({
                                    'symbol': pair.get('baseToken', {}).get('symbol', 'Unknown'),
                                    'address': pair.get('baseToken', {}).get('address', ''),
                                    'price': pair.get('priceUsd', '0'),
                                    'liquidity': liquidity,
                                    'age_hours': round(age, 2),
                                    'url': f"https://dexscreener.com/solana/{pair.get('pairAddress', '')}"
                                })
                
                return new_tokens
        except Exception as e:
            print(f"扫描失败: {e}")
            return []
    
    def display_opportunities(self, tokens):
        """显示机会"""
        print("\n" + "="*60)
        print(f"🎯 发现 {len(tokens)} 个新币机会")
        print("="*60)
        
        for i, t in enumerate(tokens[:10], 1):
            print(f"\n{i}. {t['symbol']}")
            print(f"   价格: ${t['price']}")
            print(f"   流动性: ${t['liquidity']:.0f}")
            print(f"   上线: {t['age_hours']}小时前")
            print(f"   链接: {t['url']}")
        
        # 保存
        with open('/home/admin/Ziwei/data/meme_opportunities.json', 'w') as f:
            json.dump(tokens, f, indent=2)
        
        print(f"\n✅ 已保存到: /home/admin/Ziwei/data/meme_opportunities.json")

    def run(self):
        """运行狙击"""
        print("="*60)
        print(f"🎲 Meme币狙击手 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*60)
        
        print("\n⚠️  风险警告:")
        print("   - 这是赌博，不是投资")
        print("   - 建议投入: $5-10")
        print("   - 做好100%亏损的准备")
        
        tokens = self.scan_pump_fun()
        self.display_opportunities(tokens)
        
        print("\n" + "="*60)
        print("📝 购买方法:")
        print("   1. 打开 Jupiter: https://jup.ag")
        print("   2. 粘贴代币地址")
        print("   3. 小额购买 ($5-10)")
        print("   4. 设置止损 (跌50%卖出)")
        print("="*60)

if __name__ == '__main__':
    sniper = MemeSniper()
    sniper.run()
