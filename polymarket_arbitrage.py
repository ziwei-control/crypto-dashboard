#!/usr/bin/env python3
"""
=============================================================================
💰 Polymarket 套利策略引擎 v2.0
=============================================================================

套利类型：
1. 跨平台套利（Polymarket vs Manifold vs Metaculus）
2. 跨市场套利（同一事件的不同市场）
3. 时间套利（概率随时间变化）
4. 信息套利（利用信息不对称）

核心公式：
套利利润 = |P1 - P2| * 本金 - 手续费

=============================================================================
"""

import os
import json
import time
import requests
import asyncio
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

# =============================================================================
# 配置
# =============================================================================

BASE_DIR = Path("/home/admin/Ziwei")
DATA_DIR = BASE_DIR / "data"
ARBITRAGE_DIR = DATA_DIR / "arbitrage"
LOG_DIR = DATA_DIR / "logs"

for d in [ARBITRAGE_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 手续费配置
POLYMARKET_FEE = 0.02  # 2%
MANIFOLD_FEE = 0.00   # 0%

# =============================================================================
# 数据获取器
# =============================================================================

class MarketDataFetcher:
    """多平台市场数据获取"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_polymarket_markets(self, limit: int = 50) -> List[Dict]:
        """获取Polymarket市场数据"""
        try:
            # 使用Gamma API
            resp = self.session.get(
                f"https://gamma-api.polymarket.com/markets?limit={limit}&active=true",
                timeout=15
            )
            data = resp.json()
            
            markets = []
            for m in data:
                # 解析价格
                outcome_prices = m.get('outcomePrices', '[]')
                try:
                    prices = json.loads(outcome_prices) if isinstance(outcome_prices, str) else outcome_prices
                    yes_price = float(prices[0]) if prices else 0.5
                except:
                    yes_price = 0.5
                
                markets.append({
                    "platform": "Polymarket",
                    "question": m.get('question', ''),
                    "condition_id": m.get('condition_id', ''),
                    "yes_price": yes_price / 100 if yes_price > 1 else yes_price,  # 归一化到0-1
                    "volume": m.get('volume', 0),
                    "end_date": m.get('end_date_iso', ''),
                    "category": m.get('tags', ['general'])[0] if m.get('tags') else 'general',
                    "url": f"https://polymarket.com/event/{m.get('slug', '')}"
                })
            
            return markets
            
        except Exception as e:
            print(f"   ⚠️ Polymarket获取失败: {e}")
            return []
    
    def get_manifold_markets(self, limit: int = 50) -> List[Dict]:
        """获取Manifold Markets数据"""
        try:
            resp = self.session.get(
                f"https://api.manifold.markets/v0/markets?limit={limit}",
                timeout=15
            )
            data = resp.json()
            
            markets = []
            for m in data:
                prob = m.get('probability', 0.5)
                volume = m.get('volume', 0) or 0
                
                markets.append({
                    "platform": "Manifold",
                    "question": m.get('question', ''),
                    "id": m.get('id', ''),
                    "yes_price": prob,
                    "volume": volume,
                    "category": 'general',
                    "url": f"https://manifold.markets/{m.get('creatorSlug', '')}/{m.get('slug', '')}"
                })
            
            return markets
            
        except Exception as e:
            print(f"   ⚠️ Manifold获取失败: {e}")
            return []
    
    def get_metaculus_questions(self, limit: int = 20) -> List[Dict]:
        """获取Metaculus预测数据"""
        try:
            resp = self.session.get(
                f"https://www.metaculus.com/api2/questions/?limit={limit}&status=open",
                timeout=15
            )
            data = resp.json()
            
            markets = []
            for q in data.get('results', []):
                # Metaculus使用社区预测
                community_pred = q.get('community_prediction', {})
                prob = community_pred.get('mean', 0.5)
                
                markets.append({
                    "platform": "Metaculus",
                    "question": q.get('title', ''),
                    "id": q.get('id', ''),
                    "yes_price": min(0.99, max(0.01, prob)),  # Metaculus可能是连续值
                    "volume": 0,  # Metaculus没有成交量
                    "category": q.get('category', 'general'),
                    "url": f"https://www.metaculus.com/questions/{q.get('id', '')}"
                })
            
            return markets
            
        except Exception as e:
            print(f"   ⚠️ Metaculus获取失败: {e}")
            return []
    
    def get_all_markets(self) -> Dict[str, List[Dict]]:
        """获取所有平台数据"""
        return {
            "polymarket": self.get_polymarket_markets(50),
            "manifold": self.get_manifold_markets(50),
            "metaculus": self.get_metaculus_questions(20)
        }


# =============================================================================
# 套利机会检测器
# =============================================================================

class ArbitrageDetector:
    """套利机会检测"""
    
    def __init__(self, min_edge: float = 0.05, min_volume: float = 1000):
        """
        min_edge: 最小概率差距（默认5%）
        min_volume: 最小成交量（默认$1000）
        """
        self.min_edge = min_edge
        self.min_volume = min_volume
    
    def find_cross_platform_arbitrage(self, markets: Dict[str, List[Dict]]) -> List[Dict]:
        """跨平台套利检测"""
        opportunities = []
        
        # 提取所有市场问题
        all_questions = defaultdict(list)
        
        for platform, platform_markets in markets.items():
            for m in platform_markets:
                # 标准化问题文本
                question_key = self._normalize_question(m['question'])
                all_questions[question_key].append({
                    "platform": platform,
                    "question": m['question'],
                    "yes_price": m['yes_price'],
                    "volume": m['volume'],
                    "url": m['url']
                })
        
        # 寻找同一问题的不同平台定价
        for question_key, platforms_data in all_questions.items():
            if len(platforms_data) >= 2:  # 至少在2个平台存在
                # 按价格排序
                sorted_data = sorted(platforms_data, key=lambda x: x['yes_price'])
                lowest = sorted_data[0]
                highest = sorted_data[-1]
                
                # 计算价差
                price_diff = highest['yes_price'] - lowest['yes_price']
                
                # 检查是否满足最小边缘
                if price_diff >= self.min_edge:
                    # 计算潜在利润
                    # 策略：在低价平台买YES，在高价平台卖YES（或买NO）
                    
                    max_volume = min(float(lowest.get('volume', 0) or 0), float(highest.get('volume', 0) or 0))
                    
                    if max_volume >= self.min_volume:
                        # 计算手续费
                        total_fee = (POLYMARKET_FEE + MANIFOLD_FEE)
                        
                        # 净利润
                        net_profit_pct = price_diff - total_fee
                        
                        if net_profit_pct > 0:
                            opportunities.append({
                                "type": "cross_platform",
                                "question": lowest['question'],
                                "edge": price_diff,
                                "net_profit_pct": net_profit_pct,
                                "buy_platform": lowest['platform'],
                                "buy_price": lowest['yes_price'],
                                "buy_url": lowest['url'],
                                "sell_platform": highest['platform'],
                                "sell_price": highest['yes_price'],
                                "sell_url": highest['url'],
                                "max_volume": max_volume,
                                "strategy": f"在{lowest['platform']}买YES @{lowest['yes_price']:.2f}, 在{highest['platform']}买NO @{1-highest['yes_price']:.2f}",
                                "risk": "低风险（对冲）"
                            })
        
        return sorted(opportunities, key=lambda x: x['edge'], reverse=True)
    
    def find_mispriced_markets(self, markets: Dict[str, List[Dict]]) -> List[Dict]:
        """发现被错误定价的市场"""
        opportunities = []
        
        # 检查Polymarket市场
        for m in markets.get('polymarket', []):
            # 策略1: 极端概率（可能被低估/高估）
            if m['yes_price'] < 0.1:
                opportunities.append({
                    "type": "potential_undervalued",
                    "question": m['question'],
                    "platform": "Polymarket",
                    "yes_price": m['yes_price'],
                    "edge": 0.1 - m['yes_price'],
                    "strategy": "低价市场，可能被低估",
                    "risk": "高风险",
                    "volume": m['volume'],
                    "url": m['url']
                })
            elif m['yes_price'] > 0.9:
                opportunities.append({
                    "type": "potential_overvalued",
                    "question": m['question'],
                    "platform": "Polymarket",
                    "yes_price": m['yes_price'],
                    "edge": m['yes_price'] - 0.9,
                    "strategy": "高价市场，可能被高估",
                    "risk": "高风险",
                    "volume": m['volume'],
                    "url": m['url']
                })
            
            # 策略2: 成交量大但价格稳定（可能有信息优势）
            vol = float(m.get('volume', 0) or 0)
            if vol > 10000:
                # 检查是否有相关信息来源可以提供优势
                pass
        
        return opportunities
    
    def find_time_based_opportunities(self, markets: Dict[str, List[Dict]]) -> List[Dict]:
        """时间套利机会"""
        opportunities = []
        
        for m in markets.get('polymarket', []):
            end_date = m.get('end_date', '')
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    days_left = (end_dt - datetime.now(end_dt.tzinfo)).days
                    
                    # 即将结束的市场可能有波动
                    if 0 < days_left <= 7:
                        opportunities.append({
                            "type": "ending_soon",
                            "question": m['question'],
                            "platform": "Polymarket",
                            "yes_price": m['yes_price'],
                            "days_left": days_left,
                            "strategy": "即将结束，可能有波动",
                            "risk": "中等风险",
                            "volume": m['volume'],
                            "url": m['url']
                        })
                except:
                    pass
        
        return opportunities
    
    def _normalize_question(self, question: str) -> str:
        """标准化问题文本用于匹配"""
        # 移除标点和多余空格
        import re
        q = question.lower()
        q = re.sub(r'[^\w\s]', '', q)
        q = ' '.join(q.split())
        # 只保留关键词
        words = q.split()[:5]  # 前5个词
        return ' '.join(words)


# =============================================================================
# 套利执行器
# =============================================================================

class ArbitrageExecutor:
    """套利执行（模拟+真实）"""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.positions_file = ARBITRAGE_DIR / "positions.json"
        self.trades_file = ARBITRAGE_DIR / "trades.json"
        self.balance_file = ARBITRAGE_DIR / "balance.json"
        
        self._load_state()
    
    def _load_state(self):
        """加载状态"""
        if self.balance_file.exists():
            with open(self.balance_file, 'r') as f:
                self.balance = json.load(f)
        else:
            self.balance = {"cash": 100.0}  # 初始$100
        
        if self.positions_file.exists():
            with open(self.positions_file, 'r') as f:
                self.positions = json.load(f)
        else:
            self.positions = {}
        
        if self.trades_file.exists():
            with open(self.trades_file, 'r') as f:
                self.trades = json.load(f)
        else:
            self.trades = []
    
    def _save_state(self):
        """保存状态"""
        with open(self.balance_file, 'w') as f:
            json.dump(self.balance, f, indent=2)
        with open(self.positions_file, 'w') as f:
            json.dump(self.positions, f, indent=2)
        with open(self.trades_file, 'w') as f:
            json.dump(self.trades, f, indent=2)
    
    def execute_arbitrage(self, opportunity: Dict, amount: float = 10.0) -> Dict:
        """执行套利"""
        if self.dry_run:
            return self._simulate_arbitrage(opportunity, amount)
        else:
            return self._real_arbitrage(opportunity, amount)
    
    def _simulate_arbitrage(self, opportunity: Dict, amount: float) -> Dict:
        """模拟套利"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "opportunity": opportunity,
            "amount": amount,
            "status": "simulated",
            "expected_profit": amount * opportunity['net_profit_pct'] if 'net_profit_pct' in opportunity else 0
        }
        
        # 记录交易
        self.trades.append(result)
        self._save_state()
        
        return result
    
    def _real_arbitrage(self, opportunity: Dict, amount: float) -> Dict:
        """真实套利（需要API配置）"""
        # TODO: 实现真实交易
        return {
            "status": "error",
            "message": "真实交易需要配置API Key"
        }
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            "balance": self.balance['cash'],
            "total_trades": len(self.trades),
            "open_positions": len(self.positions),
            "simulated": self.dry_run
        }


# =============================================================================
# 主控制器
# =============================================================================

class PolymarketArbitrageEngine:
    """Polymarket套利引擎"""
    
    def __init__(self, dry_run: bool = True):
        self.fetcher = MarketDataFetcher()
        self.detector = ArbitrageDetector(min_edge=0.03, min_volume=500)
        self.executor = ArbitrageExecutor(dry_run=dry_run)
        
        self.log_file = LOG_DIR / "arbitrage.log"
    
    def log(self, msg: str):
        """记录日志"""
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {msg}")
        with open(self.log_file, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    
    def run_scan(self) -> Dict:
        """运行套利扫描"""
        self.log("\n" + "="*60)
        self.log("💰 Polymarket 套利引擎启动")
        self.log("="*60)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "markets": {},
            "opportunities": [],
            "stats": {}
        }
        
        # 1. 获取所有市场数据
        self.log("\n📡 获取市场数据...")
        markets = self.fetcher.get_all_markets()
        
        polymarket_count = len(markets.get('polymarket', []))
        manifold_count = len(markets.get('manifold', []))
        metaculus_count = len(markets.get('metaculus', []))
        
        self.log(f"   Polymarket: {polymarket_count} 个市场")
        self.log(f"   Manifold: {manifold_count} 个市场")
        self.log(f"   Metaculus: {metaculus_count} 个问题")
        
        result['markets'] = {
            "polymarket": polymarket_count,
            "manifold": manifold_count,
            "metaculus": metaculus_count
        }
        
        # 2. 检测套利机会
        self.log("\n🔍 检测套利机会...")
        
        # 跨平台套利
        cross_platform = self.detector.find_cross_platform_arbitrage(markets)
        self.log(f"   跨平台套利: {len(cross_platform)} 个机会")
        
        # 错误定价
        mispriced = self.detector.find_mispriced_markets(markets)
        self.log(f"   潜在错误定价: {len(mispriced)} 个")
        
        # 时间套利
        time_based = self.detector.find_time_based_opportunities(markets)
        self.log(f"   即将结束市场: {len(time_based)} 个")
        
        all_opportunities = cross_platform + mispriced + time_based
        all_opportunities.sort(key=lambda x: x.get('edge', 0), reverse=True)
        
        result['opportunities'] = all_opportunities[:10]  # 返回前10个
        
        # 3. 显示最佳机会
        if all_opportunities:
            self.log("\n🎯 最佳套利机会:")
            for i, opp in enumerate(all_opportunities[:5], 1):
                self.log(f"\n{i}. {opp['question'][:50]}...")
                self.log(f"   类型: {opp['type']}")
                self.log(f"   边缘: {opp.get('edge', 0):.1%}")
                self.log(f"   策略: {opp.get('strategy', 'N/A')}")
                self.log(f"   风险: {opp.get('risk', 'N/A')}")
                
                if opp['type'] == 'cross_platform':
                    self.log(f"   买: {opp['buy_platform']} @{opp['buy_price']:.2f}")
                    self.log(f"   卖: {opp['sell_platform']} @{opp['sell_price']:.2f}")
        else:
            self.log("\n⏳ 暂无符合条件的套利机会")
        
        # 4. 保存结果
        result['stats'] = self.executor.get_stats()
        
        report_file = ARBITRAGE_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(report_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        self.log(f"\n📊 报告已保存: {report_file}")
        
        return result
    
    def get_crypto_markets(self) -> List[Dict]:
        """获取加密货币相关市场（我们的优势领域）"""
        markets = self.fetcher.get_polymarket_markets(100)
        
        crypto_keywords = [
            'bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'solana', 'sol',
            'defi', 'nft', 'token', 'blockchain', 'coin', 'wallet'
        ]
        
        crypto_markets = []
        for m in markets:
            question_lower = m['question'].lower()
            if any(kw in question_lower for kw in crypto_keywords):
                crypto_markets.append(m)
        
        return crypto_markets


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Polymarket套利引擎")
    parser.add_argument("--scan", action="store_true", help="扫描套利机会")
    parser.add_argument("--crypto", action="store_true", help="只看加密货币市场")
    parser.add_argument("--stats", action="store_true", help="查看统计")
    parser.add_argument("--real", action="store_true", help="启用真实交易")
    
    args = parser.parse_args()
    
    engine = PolymarketArbitrageEngine(dry_run=not args.real)
    
    if args.crypto:
        print("\n🌞 加密货币相关市场:")
        crypto = engine.get_crypto_markets()
        for m in crypto[:10]:
            vol = float(m.get('volume', 0) or 0)
            print(f"  • {m['question'][:50]}...")
            print(f"    概率: {m['yes_price']:.0%} | 成交量: ${vol:,.0f}")
    
    elif args.stats:
        stats = engine.executor.get_stats()
        print(f"\n📊 套利统计:")
        print(f"   余额: ${stats['balance']:.2f}")
        print(f"   总交易: {stats['total_trades']}")
        print(f"   持仓: {stats['open_positions']}")
        print(f"   模式: {'模拟' if stats['simulated'] else '真实'}")
    
    else:
        engine.run_scan()