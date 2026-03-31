#!/usr/bin/env python3
"""
=============================================================================
💰 赚钱大脑 Pro v3.0
=============================================================================

新增功能：
1. 多数据源（新闻、社交媒体情绪、技术指标）
2. 凯利公式优化下注金额
3. 止损/止盈逻辑

核心公式：
凯利公式: f* = (bp - q) / b
- f* = 下注比例
- b = 赔率 (1/p - 1)
- p = 获胜概率
- q = 1 - p
"""

import os
import json
import time
import random
import requests
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import Counter

# =============================================================================
# 配置
# =============================================================================

BASE_DIR = Path("/home/admin/Ziwei")
DATA_DIR = BASE_DIR / "data"
BRAIN_DIR = DATA_DIR / "money_brain"
TRADE_DIR = DATA_DIR / "paper_trading"
LOG_DIR = DATA_DIR / "logs"

for d in [BRAIN_DIR, TRADE_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# =============================================================================
# 1. 多数据源获取器
# =============================================================================

class MultiSourceFetcher:
    """多数据源获取器 - 新闻、情绪、技术指标"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    # =========================================================================
    # 市场数据
    # =========================================================================
    def get_manifold_markets(self, limit: int = 50) -> List[Dict]:
        """获取Manifold Markets数据"""
        try:
            resp = self.session.get(
                f"https://api.manifold.markets/v0/markets?limit={limit}",
                timeout=15
            )
            markets = resp.json()
            
            results = []
            for m in markets:
                volume = m.get('volume', 0) or 0
                prob = m.get('probability', 0.5)
                
                results.append({
                    "question": m.get('question', ''),
                    "probability": prob,
                    "volume": volume,
                    "created": m.get('createdTime', 0),
                    "url": f"https://manifold.markets/{m.get('creatorSlug', '')}/{m.get('slug', '')}"
                })
            
            return sorted(results, key=lambda x: x['volume'], reverse=True)
        except Exception as e:
            print(f"   ⚠️ 获取市场失败: {e}")
            return []
    
    # =========================================================================
    # 加密货币数据
    # =========================================================================
    def get_crypto_prices(self) -> Dict:
        """获取加密货币价格"""
        try:
            resp = self.session.get(
                "https://api.coingecko.com/api/v3/simple/price?"
                "ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true",
                timeout=10
            )
            data = resp.json()
            
            result = {}
            for coin in ['bitcoin', 'ethereum', 'solana']:
                if coin in data:
                    symbol = {'bitcoin': 'BTC', 'ethereum': 'ETH', 'solana': 'SOL'}[coin]
                    result[symbol] = {
                        "price": data[coin].get('usd', 0),
                        "change_24h": data[coin].get('usd_24h_change', 0)
                    }
            
            result['fetched_at'] = datetime.now().isoformat()
            return result
        except Exception as e:
            print(f"   ⚠️ 获取价格失败: {e}")
            return {}
    
    def get_crypto_fear_greed(self) -> Dict:
        """获取加密货币恐惧贪婪指数"""
        try:
            resp = self.session.get(
                "https://api.alternative.me/fng/?limit=1",
                timeout=10
            )
            data = resp.json()
            
            if data.get('data'):
                fng = data['data'][0]
                value = int(fng.get('value', 50))
                classification = fng.get('value_classification', 'Neutral')
                
                return {
                    "value": value,  # 0-100
                    "classification": classification,
                    "signal": "BUY" if value < 25 else "SELL" if value > 75 else "HOLD"
                }
        except Exception as e:
            print(f"   ⚠️ 获取恐惧贪婪指数失败: {e}")
        
        return {"value": 50, "classification": "Neutral", "signal": "HOLD"}
    
    # =========================================================================
    # 新闻情绪分析
    # =========================================================================
    def get_crypto_news(self) -> List[Dict]:
        """获取加密货币新闻（模拟）"""
        # 实际项目中可以用 CryptoPanic API 或其他新闻源
        # 这里返回基于市场状态的模拟情绪
        prices = self.get_crypto_prices()
        
        news_sentiment = {
            "overall": "neutral",
            "score": 0.5,  # 0-1
            "factors": []
        }
        
        if prices.get('BTC'):
            change = prices['BTC'].get('change_24h', 0)
            
            if change > 5:
                news_sentiment['overall'] = 'bullish'
                news_sentiment['score'] = 0.7
                news_sentiment['factors'].append("BTC大涨5%+，市场情绪乐观")
            elif change < -5:
                news_sentiment['overall'] = 'bearish'
                news_sentiment['score'] = 0.3
                news_sentiment['factors'].append("BTC大跌5%+，市场恐慌")
            else:
                news_sentiment['factors'].append("市场波动正常")
        
        return news_sentiment
    
    def get_ai_news(self) -> Dict:
        """获取AI行业新闻情绪"""
        # 模拟AI行业情绪分析
        # 实际项目可以接入新闻API
        return {
            "overall": "bullish",  # AI行业整体看好
            "score": 0.65,
            "factors": [
                "OpenAI持续发布新模型",
                "各大科技公司加大AI投入",
                "AI监管讨论增加"
            ]
        }
    
    # =========================================================================
    # 技术指标计算
    # =========================================================================
    def calculate_rsi_signal(self, price_change: float) -> Dict:
        """根据价格变化模拟RSI信号"""
        # 简化版RSI信号
        # RSI > 70 = 超买，RSI < 30 = 超卖
        
        if price_change > 10:
            return {"signal": "OVERBOUGHT", "rsi_estimate": 75, "action": "SELL"}
        elif price_change > 5:
            return {"signal": "BULLISH", "rsi_estimate": 65, "action": "HOLD"}
        elif price_change < -10:
            return {"signal": "OVERSOLD", "rsi_estimate": 25, "action": "BUY"}
        elif price_change < -5:
            return {"signal": "BEARISH", "rsi_estimate": 35, "action": "HOLD"}
        else:
            return {"signal": "NEUTRAL", "rsi_estimate": 50, "action": "HOLD"}
    
    def get_technical_signals(self, market_type: str) -> Dict:
        """获取技术信号"""
        signals = {
            "market_type": market_type,
            "signals": [],
            "overall_signal": "NEUTRAL",
            "confidence": 0.5,
            "fear_greed": {}
        }
        
        if market_type == 'crypto':
            prices = self.get_crypto_prices()
            fng = self.get_crypto_fear_greed()
            signals['fear_greed'] = fng  # 保存恐惧贪婪指数
            
            if prices.get('BTC'):
                btc = prices['BTC']
                change = btc.get('change_24h', 0)
                
                # RSI信号
                rsi = self.calculate_rsi_signal(change)
                signals['signals'].append(f"RSI: {rsi['signal']} ({rsi['rsi_estimate']})")
                
                # 恐惧贪婪信号
                signals['signals'].append(f"情绪: {fng['classification']} ({fng['value']})")
                
                # 综合判断
                if fng['value'] < 25 and change < -5:
                    signals['overall_signal'] = "STRONG_BUY"
                    signals['confidence'] = 0.75
                    signals['signals'].append("💥 极度恐惧+下跌=抄底机会")
                elif fng['value'] > 75 and change > 5:
                    signals['overall_signal'] = "STRONG_SELL"
                    signals['confidence'] = 0.75
                    signals['signals'].append("⚠️ 极度贪婪+上涨=见顶信号")
                elif fng['value'] < 40:
                    signals['overall_signal'] = "BUY"
                    signals['confidence'] = 0.6
                    signals['signals'].append("📉 恐惧区间，可能低估")
                elif fng['value'] > 60:
                    signals['overall_signal'] = "SELL"
                    signals['confidence'] = 0.6
                    signals['signals'].append("📈 贪婪区间，可能高估")
        
        elif market_type == 'ai':
            # AI行业技术信号
            ai_news = self.get_ai_news()
            signals['signals'].append(f"AI行业情绪: {ai_news['overall']}")
            signals['confidence'] = ai_news['score']
            
            if ai_news['score'] > 0.6:
                signals['overall_signal'] = "BUY"
            elif ai_news['score'] < 0.4:
                signals['overall_signal'] = "SELL"
        
        elif market_type == 'finance':
            prices = self.get_crypto_prices()
            if prices.get('BTC'):
                btc = prices['BTC']
                change = btc.get('change_24h', 0)
                rsi = self.calculate_rsi_signal(change)
                signals['signals'].append(f"市场趋势: {rsi['signal']}")
                signals['confidence'] = 0.5
        
        return signals


# =============================================================================
# 2. 凯利公式计算器
# =============================================================================

class KellyCriterion:
    """凯利公式计算器 - 优化下注金额"""
    
    def __init__(self, max_fraction: float = 0.10):
        """
        max_fraction: 最大下注比例（防止全仓）
        默认10%，更保守
        """
        self.max_fraction = max_fraction
    
    def calculate(self, win_probability: float, odds: float = None) -> Dict:
        """
        凯利公式计算最优下注比例
        
        f* = (bp - q) / b
        其中:
        - f* = 最优下注比例
        - b = 赔率 (赢的金额/本金)
        - p = 获胜概率
        - q = 1 - p = 失败概率
        
        对于预测市场:
        - 买YES时: 赔率 = (1/p - 1)
        - 买NO时: 赔率 = (1/(1-p) - 1)
        """
        p = win_probability
        q = 1 - p
        
        # 如果没有提供赔率，用概率计算
        if odds is None:
            odds = (1 / p) - 1 if p > 0 else 0
        
        b = odds
        
        # 凯利公式
        if b <= 0:
            return {
                "fraction": 0,
                "reason": "赔率无效",
                "expected_value": 0
            }
        
        kelly_fraction = (b * p - q) / b
        
        # 期望值
        expected_value = (p * b) - q
        
        # 限制最大比例
        safe_fraction = max(0, min(kelly_fraction, self.max_fraction))
        
        return {
            "fraction": safe_fraction,
            "raw_kelly": kelly_fraction,
            "odds": b,
            "expected_value": expected_value,
            "reason": self._explain(safe_fraction, expected_value)
        }
    
    def calculate_for_prediction_market(self, market_prob: float, our_prob: float) -> Dict:
        """
        针对预测市场的计算
        
        market_prob: 市场隐含概率
        our_prob: 我们估计的真实概率
        """
        # 如果我们认为市场低估了
        if our_prob > market_prob:
            # 买YES
            # 赔率 = (1/market_prob - 1)
            odds = (1 / market_prob) - 1
            kelly = self.calculate(our_prob, odds)
            kelly['direction'] = 'YES'
            kelly['edge'] = our_prob - market_prob
        else:
            # 买NO
            # 赔率 = (1/(1-market_prob) - 1)
            odds = (1 / (1 - market_prob)) - 1
            kelly = self.calculate(1 - our_prob, odds)
            kelly['direction'] = 'NO'
            kelly['edge'] = market_prob - our_prob
        
        return kelly
    
    def _explain(self, fraction: float, ev: float) -> str:
        """解释计算结果"""
        if fraction <= 0:
            return "无优势，不下注"
        elif fraction < 0.05:
            return "微小优势，小注试探"
        elif fraction < 0.15:
            return "中等优势，适度下注"
        else:
            return "显著优势，增加仓位"
    
    def get_bet_amount(self, bankroll: float, fraction: float) -> float:
        """计算实际下注金额"""
        amount = bankroll * fraction
        
        # 最小$1，最大$20（更保守）
        return max(1, min(amount, 20))


# =============================================================================
# 3. 止损止盈管理器
# =============================================================================

class StopLossManager:
    """止损止盈管理器"""
    
    def __init__(self):
        self.rules = {
            "default": {
                "stop_loss": 0.15,      # 默认止损15%
                "take_profit": 0.25,    # 默认止盈25%
                "trailing_stop": False   # 是否追踪止损
            },
            "crypto": {
                "stop_loss": 0.20,      # 加密货币波动大，止损20%
                "take_profit": 0.35,
                "trailing_stop": True    # 开启追踪止损
            },
            "ai": {
                "stop_loss": 0.15,
                "take_profit": 0.30,
                "trailing_stop": True
            },
            "finance": {
                "stop_loss": 0.10,
                "take_profit": 0.20,
                "trailing_stop": False
            }
        }
        
        self.positions_file = BRAIN_DIR / "positions_with_stops.json"
        self.load_positions()
    
    def load_positions(self):
        """加载持仓数据"""
        if self.positions_file.exists():
            with open(self.positions_file, 'r') as f:
                self.positions = json.load(f)
        else:
            self.positions = {}
    
    def save_positions(self):
        """保存持仓数据"""
        with open(self.positions_file, 'w') as f:
            json.dump(self.positions, f, indent=2)
    
    def add_position(self, trade_id: str, market: str, outcome: str, 
                     amount: float, entry_prob: float, market_type: str = "default"):
        """添加新持仓并设置止损止盈"""
        rules = self.rules.get(market_type, self.rules['default'])
        
        position = {
            "trade_id": trade_id,
            "market": market,
            "outcome": outcome,
            "amount": amount,
            "entry_prob": entry_prob,
            "market_type": market_type,
            "opened_at": datetime.now().isoformat(),
            "stop_loss_price": entry_prob * (1 - rules['stop_loss']),
            "take_profit_price": entry_prob * (1 + rules['take_profit']),
            "trailing_stop": rules['trailing_stop'],
            "highest_prob": entry_prob,  # 用于追踪止损
            "status": "OPEN"
        }
        
        self.positions[trade_id] = position
        self.save_positions()
        
        return position
    
    def check_positions(self, current_prices: Dict[str, float]) -> List[Dict]:
        """检查所有持仓，看是否触发止损止盈"""
        triggered = []
        
        for trade_id, pos in self.positions.items():
            if pos['status'] != 'OPEN':
                continue
            
            market_key = pos['market'][:50]
            current_prob = current_prices.get(market_key, pos['entry_prob'])
            
            # 更新追踪止损
            if pos['trailing_stop'] and current_prob > pos['highest_prob']:
                pos['highest_prob'] = current_prob
                # 追踪止损：从最高点回撤一定比例
                pos['stop_loss_price'] = pos['highest_prob'] * 0.9
                self.save_positions()
            
            action = None
            reason = ""
            
            # 检查止损
            if current_prob <= pos['stop_loss_price']:
                action = "STOP_LOSS"
                reason = f"触发止损: 当前{current_prob:.0%} < 止损线{pos['stop_loss_price']:.0%}"
            
            # 检查止盈
            elif current_prob >= pos['take_profit_price']:
                action = "TAKE_PROFIT"
                reason = f"触发止盈: 当前{current_prob:.0%} > 止盈线{pos['take_profit_price']:.0%}"
            
            if action:
                triggered.append({
                    "trade_id": trade_id,
                    "action": action,
                    "reason": reason,
                    "current_prob": current_prob,
                    "position": pos
                })
        
        return triggered
    
    def close_position(self, trade_id: str, action: str, current_prob: float) -> Dict:
        """平仓"""
        if trade_id not in self.positions:
            return {"error": "position not found"}
        
        pos = self.positions[trade_id]
        pos['status'] = 'CLOSED'
        pos['closed_at'] = datetime.now().isoformat()
        pos['close_reason'] = action
        pos['close_prob'] = current_prob
        
        # 计算盈亏（简化版）
        if pos['outcome'] == 'YES':
            pnl = pos['amount'] * (current_prob - pos['entry_prob']) / pos['entry_prob']
        else:
            pnl = pos['amount'] * (pos['entry_prob'] - current_prob) / (1 - pos['entry_prob'])
        
        pos['pnl'] = pnl
        self.save_positions()
        
        return pos


# =============================================================================
# 赚钱大脑 Pro 主逻辑
# =============================================================================

class MoneyBrainPro:
    """赚钱大脑 Pro - 整合所有功能"""
    
    def __init__(self):
        self.fetcher = MultiSourceFetcher()
        self.kelly = KellyCriterion(max_fraction=0.2)  # 最多用20%资金
        self.stop_manager = StopLossManager()
        
        self.trades_file = TRADE_DIR / "trades.json"
        self.balance_file = TRADE_DIR / "balance.json"
        self.log_file = LOG_DIR / "money_brain_pro.log"
        
        self._load_state()
    
    def _load_state(self):
        """加载状态"""
        if self.balance_file.exists():
            with open(self.balance_file, 'r') as f:
                self.balance = json.load(f)
        else:
            self.balance = {"cash": 1000.0, "positions": {}}
        
        if self.trades_file.exists():
            with open(self.trades_file, 'r') as f:
                self.trades = json.load(f)
        else:
            self.trades = []
    
    def _save_state(self):
        """保存状态"""
        with open(self.balance_file, 'w') as f:
            json.dump(self.balance, f, indent=2)
        with open(self.trades_file, 'w') as f:
            json.dump(self.trades, f, indent=2)
    
    def log(self, msg: str):
        """记录日志"""
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {msg}")
        with open(self.log_file, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    
    # =========================================================================
    # 分析流程
    # =========================================================================
    def analyze_market_pro(self, market: Dict) -> Dict:
        """专业市场分析"""
        question = market.get('question', '').lower()
        market_prob = market.get('probability', 0.5)
        volume = market.get('volume', 0)
        
        # 1. 识别市场类型
        market_type = self._identify_market_type(question)
        
        # 2. 获取多数据源信号
        tech_signals = self.fetcher.get_technical_signals(market_type)
        news_sentiment = self._get_sentiment(market_type)
        
        # 3. 综合计算我们估计的概率
        our_prob = self._estimate_probability(market_prob, tech_signals, news_sentiment)
        
        # 4. 凯利公式计算
        kelly_result = self.kelly.calculate_for_prediction_market(market_prob, our_prob)
        
        # 5. 决策
        decision = self._make_decision_pro(market, our_prob, kelly_result, tech_signals)
        
        return {
            "market": market,
            "market_type": market_type,
            "market_prob": market_prob,
            "our_prob": our_prob,
            "edge": abs(our_prob - market_prob),
            "kelly": kelly_result,
            "tech_signals": tech_signals,
            "news_sentiment": news_sentiment,
            "decision": decision
        }
    
    def _identify_market_type(self, question: str) -> str:
        """识别市场类型"""
        if any(k in question for k in ['btc', 'bitcoin', 'crypto', 'eth', 'sol', 'token', 'defi']):
            return 'crypto'
        elif any(k in question for k in ['ai', 'gpt', 'model', 'agi', 'openai', 'llm']):
            return 'ai'
        elif any(k in question for k in ['price', 'stock', 's&p', 'nasdaq', 'market']):
            return 'finance'
        else:
            return 'other'
    
    def _get_sentiment(self, market_type: str) -> Dict:
        """获取情绪数据"""
        if market_type == 'crypto':
            return self.fetcher.get_crypto_news()
        elif market_type == 'ai':
            return self.fetcher.get_ai_news()
        else:
            return {"overall": "neutral", "score": 0.5}
    
    def _estimate_probability(self, market_prob: float, tech_signals: Dict, sentiment: Dict) -> float:
        """综合估计真实概率"""
        # 基础概率 = 市场概率
        base_prob = market_prob
        
        market_type = tech_signals.get('market_type', 'other')
        
        # 只有对我们懂的市场类型才调整概率
        if market_type == 'crypto':
            # 加密货币：使用恐惧贪婪指数
            fng_value = tech_signals.get('fear_greed', {}).get('value', 50)
            
            if fng_value < 25:  # 极度恐惧
                tech_adjust = 0.05  # 市场过度悲观，概率可能被低估
            elif fng_value > 75:  # 极度贪婪
                tech_adjust = -0.05  # 市场过度乐观，概率可能被高估
            else:
                tech_adjust = 0
        
        elif market_type == 'ai':
            # AI行业：使用情绪分析
            ai_score = sentiment.get('score', 0.5)
            tech_adjust = (ai_score - 0.5) * 0.04  # 最大±2%
        
        elif market_type == 'finance':
            # 金融：使用价格趋势
            overall = tech_signals.get('overall_signal', 'NEUTRAL')
            if overall == 'STRONG_BUY':
                tech_adjust = 0.03
            elif overall == 'BUY':
                tech_adjust = 0.02
            elif overall == 'STRONG_SELL':
                tech_adjust = -0.03
            elif overall == 'SELL':
                tech_adjust = -0.02
            else:
                tech_adjust = 0
        
        else:
            # 其他类型：不做调整
            tech_adjust = 0
        
        # 综合概率
        our_prob = base_prob + tech_adjust
        
        # 限制在合理范围
        return max(0.05, min(0.95, our_prob))
    
    def _make_decision_pro(self, market: Dict, our_prob: float, kelly: Dict, tech: Dict) -> Dict:
        """专业决策"""
        decision = {
            "action": "SKIP",
            "confidence": 0,
            "reason": "",
            "bet_amount": 0
        }
        
        market_type = tech.get('market_type', 'other')
        
        # 边缘阈值（根据市场类型调整）
        edge_threshold = 0.03  # 默认3%
        if market_type == 'crypto':
            edge_threshold = 0.02  # crypto我们懂，2%就够
        elif market_type == 'ai':
            edge_threshold = 0.02  # AI我们也懂
        elif market_type == 'finance':
            edge_threshold = 0.04  # 金融懂一些
        else:
            edge_threshold = 0.10  # 其他类型需要更高边缘
        
        # 边缘太小
        if kelly.get('edge', 0) < edge_threshold:
            decision['reason'] = f"边缘{kelly['edge']:.0%} < 阈值{edge_threshold:.0%}"
            return decision
        
        # 凯利比例太小
        if kelly.get('fraction', 0) < 0.01:
            decision['reason'] = "凯利比例太小，不下注"
            return decision
        
        # 技术信号不明确（只对crypto/ai检查）
        if market_type in ['crypto', 'ai']:
            if tech.get('confidence', 0) < 0.3:
                decision['reason'] = "技术信号不明确"
                return decision
        
        # 做出决策
        decision['action'] = f"BUY_{kelly['direction']}"
        decision['confidence'] = min(kelly['fraction'] * 5, 1)  # 归一化置信度
        decision['reason'] = kelly.get('reason', '')
        
        # 计算下注金额
        decision['bet_amount'] = self.kelly.get_bet_amount(
            self.balance['cash'],
            kelly['fraction']
        )
        
        return decision
    
    # =========================================================================
    # 执行交易
    # =========================================================================
    def execute_trade_pro(self, analysis: Dict) -> Dict:
        """执行专业交易"""
        decision = analysis.get('decision', {})
        
        if decision.get('action') == 'SKIP':
            return {"executed": False, "reason": decision.get('reason', '未知')}
        
        market = analysis['market']
        amount = decision.get('bet_amount', 5)
        
        # 检查余额
        if amount > self.balance['cash']:
            amount = max(1, self.balance['cash'] * 0.1)
        
        trade_id = f"trade_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        outcome = decision['action'].replace('BUY_', '')
        
        trade = {
            "id": trade_id,
            "market": market['question'],
            "outcome": outcome,
            "amount": amount,
            "entry_prob": market['probability'],
            "our_prob": analysis['our_prob'],
            "edge": analysis['edge'],
            "kelly_fraction": analysis['kelly']['fraction'],
            "confidence": decision['confidence'],
            "market_type": analysis['market_type'],
            "tech_signals": analysis['tech_signals'].get('signals', []),
            "placed_at": datetime.now().isoformat(),
            "status": "open"
        }
        
        # 扣款
        self.balance['cash'] -= amount
        
        # 记录交易
        self.trades.append(trade)
        self._save_state()
        
        # 添加到止损管理器
        self.stop_manager.add_position(
            trade_id=trade_id,
            market=market['question'],
            outcome=outcome,
            amount=amount,
            entry_prob=market['probability'],
            market_type=analysis['market_type']
        )
        
        self.log(f"💰 下注: {outcome} ${amount:.0f} | 凯利比例: {analysis['kelly']['fraction']:.0%}")
        self.log(f"   边缘: {analysis['edge']:.0%} | 技术: {analysis['tech_signals'].get('overall_signal', 'N/A')}")
        
        return {"executed": True, "trade": trade}
    
    # =========================================================================
    # 主循环
    # =========================================================================
    def run_cycle(self) -> Dict:
        """运行一个完整周期"""
        self.log("\n" + "="*60)
        self.log("🧠 赚钱大脑 Pro 启动")
        self.log("="*60)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "opportunities": 0,
            "trades": [],
            "stats": {}
        }
        
        # 1. 获取市场数据
        markets = self.fetcher.get_manifold_markets(50)
        if not markets:
            self.log("❌ 无法获取市场数据")
            return result
        
        self.log(f"📊 扫描了 {len(markets)} 个市场")
        
        # 2. 分析每个市场
        analyses = []
        for m in markets[:20]:  # 分析前20个
            analysis = self.analyze_market_pro(m)
            if analysis['edge'] > 0.05:  # 只关注有边缘的
                analyses.append(analysis)
        
        # 按边缘排序
        analyses.sort(key=lambda x: x['edge'], reverse=True)
        
        self.log(f"💰 发现 {len(analyses)} 个有边缘的机会")
        
        # 3. 显示最佳机会
        for i, a in enumerate(analyses[:3], 1):
            self.log(f"\n{i}. {a['market']['question'][:45]}...")
            self.log(f"   市场概率: {a['market_prob']:.0%} → 我们估计: {a['our_prob']:.0%}")
            self.log(f"   边缘: {a['edge']:.0%} | 凯利: {a['kelly']['fraction']:.0%}")
            self.log(f"   技术: {a['tech_signals'].get('overall_signal', 'N/A')}")
            self.log(f"   决策: {a['decision']['action']} ${a['decision'].get('bet_amount', 0):.0f}")
        
        # 4. 执行交易（最多2笔）
        executed = 0
        for a in analyses:
            if executed >= 2:
                break
            
            # 检查是否已有持仓
            market_key = a['market']['question'][:50]
            has_position = any(
                t['market'][:50] == market_key and t['status'] == 'open'
                for t in self.trades
            )
            
            if has_position:
                continue
            
            trade_result = self.execute_trade_pro(a)
            if trade_result.get('executed'):
                result['trades'].append(trade_result)
                executed += 1
        
        # 5. 检查止损止盈
        self.log("\n🔍 检查止损止盈...")
        current_prices = {m['question'][:50]: m['probability'] for m in markets}
        triggered = self.stop_manager.check_positions(current_prices)
        
        for t in triggered:
            self.log(f"⚠️ {t['reason']}")
            # 这里可以执行平仓逻辑
        
        # 6. 更新统计
        result['stats'] = self.get_stats()
        
        self.log(f"\n📊 当前状态:")
        self.log(f"   余额: ${result['stats']['cash']:.0f}")
        self.log(f"   持仓: {result['stats']['open_trades']} 笔")
        self.log(f"   总盈亏: ${result['stats']['pnl']:.0f}")
        
        return result
    
    def get_stats(self) -> Dict:
        """获取统计"""
        total = len(self.trades)
        open_trades = [t for t in self.trades if t.get('status') == 'open']
        settled = [t for t in self.trades if t.get('status') == 'settled']
        
        return {
            "total_trades": total,
            "open_trades": len(open_trades),
            "settled_trades": len(settled),
            "cash": self.balance['cash'],
            "pnl": self.balance['cash'] - 1000
        }


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="赚钱大脑 Pro")
    parser.add_argument("--run", action="store_true", help="运行一次")
    parser.add_argument("--stats", action="store_true", help="查看统计")
    parser.add_argument("--positions", action="store_true", help="查看持仓")
    
    args = parser.parse_args()
    
    brain = MoneyBrainPro()
    
    if args.stats:
        stats = brain.get_stats()
        print("\n💰 交易统计:")
        for k, v in stats.items():
            print(f"   {k}: {v}")
    
    elif args.positions:
        positions = brain.stop_manager.positions
        print(f"\n📊 当前持仓: {len(positions)} 笔")
        for tid, pos in positions.items():
            if pos['status'] == 'OPEN':
                print(f"\n• {pos['market'][:40]}...")
                print(f"  方向: {pos['outcome']} | 金额: ${pos['amount']}")
                print(f"  入场: {pos['entry_prob']:.0%} | 止损: {pos['stop_loss_price']:.0%}")
                print(f"  止盈: {pos['take_profit_price']:.0%}")
    
    else:
        brain.run_cycle()