#!/usr/bin/env python3
"""
智能止盈止损分析器
结合新闻、时政、情绪、技术分析动态计算清仓/斩仓价格

核心逻辑：
1. 新闻情绪 → 调整止盈空间
2. 市场趋势 → 调整止损位置
3. 技术支撑位 → 确定止损底线
4. 资金流向 → 判断离场时机
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass

# ============================================================
# 配置
# ============================================================

# 数据源
INTEL_DIR = Path("/home/admin/Ziwei/data/intel")
MEME_DATA = Path("/home/admin/Ziwei/products/meme-monitor/data/latest_analysis.json")
BINANCE_API = "https://api.binance.com"

# 币种分类
MAINSTREAM_COINS = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA']
MEME_COINS = ['DOGE', 'SHIB', 'PEPE', 'WIF', 'BONK', 'FLOKI']
NEW_COINS = {
    'G': '2026-03-13',
    'XPL': '2026-03-12',
    'ANIME': '2026-03-10',
    'CFG': '2026-03-15',
}

# ============================================================
# 数据类
# ============================================================

@dataclass
class SmartExit:
    """智能止盈止损"""
    symbol: str
    current_price: float
    
    # 止盈
    take_profit_price: float
    take_profit_pct: float
    take_profit_reason: str
    
    # 止损
    stop_loss_price: float
    stop_loss_pct: float
    stop_loss_reason: str
    
    # 分析
    news_sentiment: str      # bullish/bearish/neutral
    market_trend: str        # uptrend/downtrend/sideways
    technical_signal: str    # strong/weak/neutral
    risk_level: str          # low/medium/high
    
    # 建议
    action: str              # HOLD/TAKE_PROFIT/STOP_LOSS/URGENT_EXIT
    summary: str

# ============================================================
# 核心类
# ============================================================

class SmartExitAnalyzer:
    """智能止盈止损分析器"""
    
    def __init__(self):
        self.intel_data = self._load_latest_intel()
        self.meme_data = self._load_meme_data()
        
        print("=" * 70)
        print("🧠 智能止盈止损分析器")
        print("=" * 70)
        print("   数据源: 新闻 + 情绪 + 技术 + 资金流")
        print("=" * 70)
    
    def _load_latest_intel(self) -> dict:
        """加载最新情报"""
        try:
            files = sorted(INTEL_DIR.glob("intel_*.json"), reverse=True)
            if files:
                with open(files[0]) as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def _load_meme_data(self) -> dict:
        """加载 Meme 策略数据"""
        try:
            with open(MEME_DATA) as f:
                return json.load(f)
        except:
            return {}
    
    def _get_price_data(self, symbol: str) -> dict:
        """获取价格数据"""
        try:
            resp = requests.get(f"{BINANCE_API}/api/v3/ticker/24hr?symbol={symbol}USDT")
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        return {}
    
    def _analyze_news_sentiment(self, symbol: str) -> tuple:
        """分析新闻情绪"""
        # 从情报数据中获取
        news = self.intel_data.get('news', {}).get(symbol, [])
        
        if not news:
            return "neutral", 50, "无相关新闻"
        
        # 简单关键词分析
        bullish_words = ['bull', 'surge', 'rally', 'gain', 'buy', 'up', 'high', 'positive', 'growth']
        bearish_words = ['bear', 'crash', 'drop', 'sell', 'down', 'low', 'negative', 'decline', 'loss']
        
        bullish_count = 0
        bearish_count = 0
        
        for article in news[:5]:  # 分析最近5条
            title = article.get('title', '').lower()
            for word in bullish_words:
                if word in title:
                    bullish_count += 1
            for word in bearish_words:
                if word in title:
                    bearish_count += 1
        
        total = bullish_count + bearish_count
        if total == 0:
            return "neutral", 50, "新闻情绪中性"
        
        bullish_pct = bullish_count / total * 100
        
        if bullish_pct >= 70:
            return "bullish", bullish_pct, f"新闻偏多({bullish_pct:.0f}%利好)"
        elif bullish_pct >= 55:
            return "slightly_bullish", bullish_pct, f"新闻偏多({bullish_pct:.0f}%利好)"
        elif bullish_pct <= 30:
            return "bearish", bullish_pct, f"新闻偏空({100-bullish_pct:.0f}%利空)"
        elif bullish_pct <= 45:
            return "slightly_bearish", bullish_pct, f"新闻偏空({100-bullish_pct:.0f}%利空)"
        else:
            return "neutral", bullish_pct, "新闻情绪中性"
    
    def _analyze_market_trend(self, symbol: str) -> tuple:
        """分析市场趋势"""
        # 从 Meme 数据获取
        overview = self.meme_data.get('market_overview', {})
        trend = overview.get('trend', 'NEUTRAL')
        sentiment = overview.get('sentiment', 'NEUTRAL')
        
        # 从策略信号获取
        strategy = None
        for s in self.meme_data.get('strategy_signals', []):
            if s['symbol'] == symbol:
                strategy = s
                break
        
        if strategy:
            signal = strategy.get('signal', '')
            score = strategy.get('score', 0)
            
            if 'BUY' in signal and score > 15:
                return "uptrend", "上涨趋势，策略信号积极"
            elif 'BUY' in signal:
                return "slight_uptrend", "小幅上涨，策略信号谨慎"
            elif 'SELL' in signal:
                return "downtrend", "下跌趋势，策略信号消极"
        
        # 从情绪排名获取
        for s in overview.get('top_sentiment', []):
            if s['symbol'] == symbol:
                score = s['score']
                label = s['label']
                if label == 'bullish' and score >= 6:
                    return "uptrend", f"情绪高涨(评分{score})"
                elif label == 'bullish':
                    return "slight_uptrend", f"情绪偏多(评分{score})"
                elif label == 'bearish':
                    return "downtrend", f"情绪偏空(评分{score})"
        
        return "sideways", "震荡整理"
    
    def _analyze_technical(self, symbol: str, price_data: dict) -> tuple:
        """技术分析"""
        if not price_data:
            return "neutral", "无技术数据"
        
        try:
            price = float(price_data['lastPrice'])
            high = float(price_data['highPrice'])
            low = float(price_data['lowPrice'])
            open_p = float(price_data['openPrice'])
            volume = float(price_data['quoteVolume'])
            change = float(price_data['priceChangePercent'])
            
            # 价格位置
            position = (price - low) / (high - low) * 100 if high != low else 50
            
            # 波动率
            volatility = (high - low) / open_p * 100 if open_p > 0 else 0
            
            # 技术评分
            score = 50
            
            # 位置评估
            if position <= 20:
                score += 20  # 低位，有支撑
                pos_note = "低位有支撑"
            elif position >= 80:
                score -= 15  # 高位，有压力
                pos_note = "高位有压力"
            else:
                pos_note = "位置适中"
            
            # 趋势评估
            if 3 <= change <= 10:
                score += 15  # 健康上涨
            elif change > 15:
                score -= 10  # 过热
            
            # 成交量
            if volume > 100_000_000:
                score += 10
            
            if score >= 70:
                return "strong", f"技术强 | {pos_note} | 波动{volatility:.1f}%"
            elif score >= 50:
                return "neutral", f"技术中性 | {pos_note} | 波动{volatility:.1f}%"
            else:
                return "weak", f"技术弱 | {pos_note} | 波动{volatility:.1f}%"
                
        except:
            return "neutral", "技术分析失败"
    
    def _calculate_smart_exit(self, symbol: str, entry_price: float, 
                                quantity: float) -> SmartExit:
        """计算智能止盈止损"""
        
        # 获取数据
        price_data = self._get_price_data(symbol)
        current_price = float(price_data.get('lastPrice', entry_price))
        
        # 分析各维度
        news_sentiment, news_score, news_reason = self._analyze_news_sentiment(symbol)
        market_trend, trend_reason = self._analyze_market_trend(symbol)
        technical, tech_reason = self._analyze_technical(symbol, price_data)
        
        # ============================================================
        # 动态止损计算
        # ============================================================
        
        # 基础止损（根据币种类型）
        is_new = symbol in NEW_COINS and (datetime.now() - datetime.strptime(NEW_COINS[symbol], '%Y-%m-%d')).days <= 7
        is_meme = symbol in MEME_COINS
        is_main = symbol in MAINSTREAM_COINS
        
        if is_new:
            base_stop_pct = 0.15
            stop_reason = "新币基础止损15%"
        elif is_meme:
            base_stop_pct = 0.08
            stop_reason = "Meme基础止损8%"
        elif is_main:
            base_stop_pct = 0.05
            stop_reason = "主流币基础止损5%"
        else:
            base_stop_pct = 0.06
            stop_reason = "默认基础止损6%"
        
        # 根据新闻情绪调整
        if news_sentiment == "bearish":
            base_stop_pct -= 0.02  # 利空，止损收紧
            stop_reason += " | 新闻利空收紧"
        elif news_sentiment == "bullish":
            base_stop_pct += 0.01  # 利好，止损放宽
            stop_reason += " | 新闻利好放宽"
        
        # 根据市场趋势调整
        if market_trend == "downtrend":
            base_stop_pct -= 0.02  # 下跌趋势，止损收紧
            stop_reason += " | 趋势向下收紧"
        elif market_trend == "uptrend":
            base_stop_pct += 0.02  # 上涨趋势，止损放宽
            stop_reason += " | 趋势向上放宽"
        
        # 根据技术信号调整
        if technical == "weak":
            base_stop_pct -= 0.01
            stop_reason += " | 技术弱收紧"
        elif technical == "strong":
            base_stop_pct += 0.01
            stop_reason += " | 技术强放宽"
        
        # 限制止损范围
        base_stop_pct = max(0.03, min(0.20, base_stop_pct))
        
        # 计算止损价
        stop_loss_price = entry_price * (1 - base_stop_pct)
        
        # ============================================================
        # 动态止盈计算
        # ============================================================
        
        # 基础止盈
        base_profit_pct = 0.08
        profit_reason = "基础止盈8%"
        
        # 根据情绪调整
        if news_sentiment == "bullish" and news_score >= 70:
            base_profit_pct += 0.04  # 强利好，提高止盈空间
            profit_reason = "新闻利好，止盈提高至12%"
        elif news_sentiment == "slightly_bullish":
            base_profit_pct += 0.02
            profit_reason = "新闻偏多，止盈提高至10%"
        elif news_sentiment == "bearish":
            base_profit_pct -= 0.02  # 利空，降低止盈目标
            profit_reason = "新闻利空，止盈降至6%"
        
        # 根据趋势调整
        if market_trend == "uptrend":
            base_profit_pct += 0.02
            profit_reason += " | 趋势向上"
        elif market_trend == "downtrend":
            base_profit_pct -= 0.02
            profit_reason += " | 趋势向下"
        
        # 根据技术调整
        if technical == "strong":
            base_profit_pct += 0.02
            profit_reason += " | 技术强"
        
        # 限制止盈范围
        base_profit_pct = max(0.05, min(0.20, base_profit_pct))
        
        # 计算止盈价
        take_profit_price = entry_price * (1 + base_profit_pct)
        
        # ============================================================
        # 风险评估
        # ============================================================
        
        risk_factors = []
        if news_sentiment in ["bearish", "slightly_bearish"]:
            risk_factors.append("新闻利空")
        if market_trend in ["downtrend"]:
            risk_factors.append("趋势向下")
        if technical == "weak":
            risk_factors.append("技术弱")
        
        if len(risk_factors) >= 2:
            risk_level = "high"
        elif len(risk_factors) == 1:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # ============================================================
        # 操作建议
        # ============================================================
        
        pnl_pct = (current_price / entry_price - 1) * 100
        
        if current_price <= stop_loss_price:
            action = "STOP_LOSS"
            summary = f"触发止损！建议立即卖出，避免更大亏损。"
        elif current_price >= take_profit_price:
            action = "TAKE_PROFIT"
            summary = f"达到止盈目标！建议卖出锁定利润。"
        elif risk_level == "high" and pnl_pct < 0:
            action = "URGENT_EXIT"
            summary = f"高风险信号：{', '.join(risk_factors)}。建议考虑离场。"
        elif pnl_pct <= -base_stop_pct * 0.7:
            action = "WARNING"
            summary = f"接近止损线，请密切关注。"
        else:
            action = "HOLD"
            summary = f"持有中，PnL: {pnl_pct:+.2f}%"
        
        return SmartExit(
            symbol=symbol,
            current_price=current_price,
            take_profit_price=take_profit_price,
            take_profit_pct=base_profit_pct * 100,
            take_profit_reason=profit_reason,
            stop_loss_price=stop_loss_price,
            stop_loss_pct=base_stop_pct * 100,
            stop_loss_reason=stop_reason,
            news_sentiment=news_sentiment,
            market_trend=market_trend,
            technical_signal=technical,
            risk_level=risk_level,
            action=action,
            summary=summary,
        )
    
    def analyze(self, symbol: str, entry_price: float = None, quantity: float = 1):
        """分析单个币种"""
        print(f"\n{'='*70}")
        print(f"📊 {symbol} 智能止盈止损分析")
        print(f"{'='*70}")
        
        # 获取当前价格
        price_data = self._get_price_data(symbol)
        current_price = float(price_data.get('lastPrice', 0))
        
        if current_price <= 0:
            print("❌ 无法获取价格数据")
            return None
        
        if entry_price is None:
            entry_price = current_price
            print(f"   当前价格: ${current_price:.6f} (假设入场价)")
        else:
            pnl = (current_price / entry_price - 1) * 100
            print(f"   入场价格: ${entry_price:.6f}")
            print(f"   当前价格: ${current_price:.6f} ({pnl:+.2f}%)")
        
        result = self._calculate_smart_exit(symbol, entry_price, quantity)
        
        print(f"\n【新闻情绪】")
        print(f"   {result.news_sentiment} - {self._sentiment_emoji(result.news_sentiment)}")
        print(f"   新闻分析: {news_reason if 'news_reason' in dir() else '综合评估'}")
        
        print(f"\n【市场趋势】")
        print(f"   {result.market_trend} - {self._trend_emoji(result.market_trend)}")
        
        print(f"\n【技术信号】")
        print(f"   {result.technical_signal} - {self._tech_emoji(result.technical_signal)}")
        
        print(f"\n【风险评估】")
        print(f"   风险等级: {result.risk_level.upper()} - {self._risk_emoji(result.risk_level)}")
        
        print(f"\n【智能止盈】")
        print(f"   目标价格: ${result.take_profit_price:.6f}")
        print(f"   止盈比例: +{result.take_profit_pct:.1f}%")
        print(f"   计算依据: {result.take_profit_reason}")
        
        print(f"\n【智能止损】")
        print(f"   斩仓价格: ${result.stop_loss_price:.6f}")
        print(f"   止损比例: -{result.stop_loss_pct:.1f}%")
        print(f"   计算依据: {result.stop_loss_reason}")
        
        print(f"\n【操作建议】")
        action_emoji = self._action_emoji(result.action)
        print(f"   {action_emoji} {result.action}")
        print(f"   {result.summary}")
        
        return result
    
    def _sentiment_emoji(self, sentiment: str) -> str:
        mapping = {
            "bullish": "😊 利好",
            "slightly_bullish": "🙂 偏多",
            "neutral": "😐 中性",
            "slightly_bearish": "😟 偏空",
            "bearish": "😰 利空",
        }
        return mapping.get(sentiment, "❓")
    
    def _trend_emoji(self, trend: str) -> str:
        mapping = {
            "uptrend": "📈 上涨",
            "slight_uptrend": "↗️ 小涨",
            "sideways": "➡️ 震荡",
            "slight_downtrend": "↘️ 小跌",
            "downtrend": "📉 下跌",
        }
        return mapping.get(trend, "❓")
    
    def _tech_emoji(self, tech: str) -> str:
        mapping = {
            "strong": "💪 强",
            "neutral": "📊 中性",
            "weak": "⚠️ 弱",
        }
        return mapping.get(tech, "❓")
    
    def _risk_emoji(self, risk: str) -> str:
        mapping = {
            "low": "🟢 低风险",
            "medium": "🟡 中风险",
            "high": "🔴 高风险",
        }
        return mapping.get(risk, "❓")
    
    def _action_emoji(self, action: str) -> str:
        mapping = {
            "HOLD": "✋",
            "TAKE_PROFIT": "💰",
            "STOP_LOSS": "🚨",
            "URGENT_EXIT": "🆘",
            "WARNING": "⚠️",
        }
        return mapping.get(action, "❓")

# ============================================================
# 主函数
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="智能止盈止损分析器")
    parser.add_argument("symbol", nargs="?", default="DOGE", help="币种符号")
    parser.add_argument("--entry", type=float, help="入场价格")
    parser.add_argument("--quantity", type=float, default=1, help="数量")
    
    args = parser.parse_args()
    
    analyzer = SmartExitAnalyzer()
    analyzer.analyze(args.symbol.upper(), args.entry, args.quantity)

if __name__ == "__main__":
    main()