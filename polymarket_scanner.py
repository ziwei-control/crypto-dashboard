#!/usr/bin/env python3
"""
Polymarket 套利扫描器
实时监控预测市场机会
"""

import requests
import json
from datetime import datetime

class PolymarketScanner:
    def __init__(self):
        self.base_url = "https://clob.polymarket.com"
        
    def get_markets(self):
        """获取所有市场"""
        try:
            resp = requests.get(f"{self.base_url}/markets", timeout=10)
            return resp.json()
        except Exception as e:
            print(f"获取市场失败: {e}")
            return []
    
    def get_prices(self, condition_id):
        """获取市场价格"""
        try:
            resp = requests.get(
                f"{self.base_url}/price",
                params={"token_ids": condition_id},
                timeout=10
            )
            return resp.json()
        except:
            return None
    
    def analyze_market(self, market):
        """分析市场是否有套利机会"""
        question = market.get('question', '')
        
        # 筛选加密货币相关
        crypto_keywords = ['bitcoin', 'btc', 'eth', 'ethereum', 'solana', 'sol', 
                          'crypto', 'price', '$100k', '$150k', 'ath']
        
        is_crypto = any(kw in question.lower() for kw in crypto_keywords)
        
        if is_crypto:
            return {
                'question': question[:80],
                'is_crypto': True,
                'market_id': market.get('condition_id', '')
            }
        return None
    
    def scan(self):
        """扫描机会"""
        print("="*60)
        print(f"🎯 Polymarket 套利扫描 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*60)
        
        markets = self.get_markets()
        print(f"\n📊 找到 {len(markets)} 个市场")
        
        crypto_markets = []
        for m in markets:
            analyzed = self.analyze_market(m)
            if analyzed:
                crypto_markets.append(analyzed)
        
        print(f"\n🪙 加密货币相关: {len(crypto_markets)} 个\n")
        
        for i, m in enumerate(crypto_markets[:10], 1):
            print(f"{i}. {m['question']}")
        
        # 保存结果
        with open('/home/admin/Ziwei/data/polymarket_markets.json', 'w') as f:
            json.dump(crypto_markets, f, indent=2)
        
        print(f"\n✅ 已保存到: /home/admin/Ziwei/data/polymarket_markets.json")
        
        return crypto_markets

if __name__ == '__main__':
    scanner = PolymarketScanner()
    scanner.scan()
