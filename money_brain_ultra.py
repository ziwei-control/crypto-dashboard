#!/usr/bin/env python3
"""
=============================================================================
💰 赚钱大脑 Ultra - 新闻 + 技术指标 + 邮件通知
=============================================================================

新增功能：
1. 真实新闻API (CryptoPanic风格)
2. 更多技术指标 (RSI, MACD, 布林带, 成交量)
3. 邮件通知系统

=============================================================================
"""

import os
import json
import time
import random
import requests
import math
import smtplib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
# 1. 真实新闻获取器
# =============================================================================

class RealNewsFetcher:
    """真实新闻获取 - 多源聚合"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 新闻缓存
        self.cache_file = BRAIN_DIR / "news_cache.json"
        self.cache_duration = 300  # 5分钟缓存
    
    def get_crypto_news(self) -> List[Dict]:
        """获取加密货币新闻"""
        news = []
        
        # 方法1: CryptoPanic API (如果有key)
        # 方法2: 从RSS抓取
        # 方法3: 模拟新闻（用于测试）
        
        try:
            # 尝试从CryptoCompare获取新闻
            resp = self.session.get(
                "https://min-api.cryptocompare.com/data/v2/news/?lang=EN&limit=10",
                timeout=10
            )
            data = resp.json()
            
            if data.get('Data'):
                for article in data['Data'][:10]:
                    news.append({
                        "title": article.get('title', ''),
                        "source": article.get('source', ''),
                        "url": article.get('url', ''),
                        "published": datetime.fromtimestamp(article.get('published_on', 0)).isoformat(),
                        "categories": article.get('categories', '').split('|'),
                        "sentiment": self._analyze_sentiment(article.get('title', ''))
                    })
        except Exception as e:
            print(f"   ⚠️ 新闻获取失败: {e}")
            # 使用模拟新闻
            news = self._get_mock_news()
        
        return news
    
    def get_ai_news(self) -> List[Dict]:
        """获取AI行业新闻"""
        news = []
        
        try:
            # 从HackerNews获取AI相关
            resp = self.session.get(
                "https://hn.algolia.com/api/v1/search?query=AI%20OR%20GPT%20OR%20LLM&tags=story&hitsPerPage=10",
                timeout=10
            )
            data = resp.json()
            
            if data.get('hits'):
                for hit in data['hits'][:10]:
                    news.append({
                        "title": hit.get('title', ''),
                        "source": "HackerNews",
                        "url": hit.get('url', f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"),
                        "published": datetime.fromtimestamp(hit.get('created_at_i', 0)).isoformat(),
                        "sentiment": self._analyze_sentiment(hit.get('title', ''))
                    })
        except Exception as e:
            print(f"   ⚠️ AI新闻获取失败: {e}")
            news = self._get_mock_ai_news()
        
        return news
    
    def _analyze_sentiment(self, text: str) -> str:
        """简单情绪分析"""
        text = text.lower()
        
        bullish_words = ['surge', 'rally', 'gain', 'rise', 'bull', 'breakthrough', 'adopt', 'launch', 'success']
        bearish_words = ['crash', 'drop', 'fall', 'bear', 'ban', 'hack', 'scam', 'regulation', 'concern']
        
        bullish_count = sum(1 for w in bullish_words if w in text)
        bearish_count = sum(1 for w in bearish_words if w in text)
        
        if bullish_count > bearish_count:
            return 'bullish'
        elif bearish_count > bullish_count:
            return 'bearish'
        else:
            return 'neutral'
    
    def _get_mock_news(self) -> List[Dict]:
        """模拟新闻（备用）"""
        return [
            {
                "title": "Bitcoin ETF sees record inflows",
                "source": "Mock",
                "sentiment": "bullish",
                "categories": ["Bitcoin", "ETF"]
            },
            {
                "title": "Fed signals potential rate cuts",
                "source": "Mock", 
                "sentiment": "bullish",
                "categories": ["Macro", "Fed"]
            }
        ]
    
    def _get_mock_ai_news(self) -> List[Dict]:
        """模拟AI新闻（备用）"""
        return [
            {
                "title": "OpenAI releases new model",
                "source": "Mock",
                "sentiment": "bullish"
            }
        ]
    
    def get_aggregated_sentiment(self, news_list: List[Dict]) -> Dict:
        """聚合新闻情绪"""
        if not news_list:
            return {"score": 0.5, "direction": "neutral"}
        
        sentiments = [n.get('sentiment', 'neutral') for n in news_list]
        
        bullish = sentiments.count('bullish')
        bearish = sentiments.count('bearish')
        total = len(sentiments)
        
        # 情绪得分 0-1
        score = 0.5 + (bullish - bearish) / (total * 2)
        score = max(0, min(1, score))
        
        if score > 0.6:
            direction = "bullish"
        elif score < 0.4:
            direction = "bearish"
        else:
            direction = "neutral"
        
        return {
            "score": score,
            "direction": direction,
            "bullish_count": bullish,
            "bearish_count": bearish,
            "total": total
        }


# =============================================================================
# 2. 技术指标计算器
# =============================================================================

class TechnicalIndicators:
    """技术指标计算器 - RSI, MACD, 布林带, 成交量"""
    
    def __init__(self):
        self.cache = {}
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> Dict:
        """计算RSI"""
        if len(prices) < period + 1:
            return {"value": 50, "signal": "NEUTRAL"}
        
        # 计算价格变化
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # 分离涨跌
        gains = [c if c > 0 else 0 for c in changes[-period:]]
        losses = [-c if c < 0 else 0 for c in changes[-period:]]
        
        # 平均涨跌
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        # 信号判断
        if rsi > 70:
            signal = "OVERBOUGHT"
        elif rsi < 30:
            signal = "OVERSOLD"
        else:
            signal = "NEUTRAL"
        
        return {
            "value": round(rsi, 2),
            "signal": signal,
            "period": period
        }
    
    def calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """计算MACD"""
        if len(prices) < slow + signal:
            return {"macd": 0, "signal": 0, "histogram": 0, "trend": "NEUTRAL"}
        
        # EMA计算
        def ema(data, period):
            multiplier = 2 / (period + 1)
            ema_val = data[0]
            for price in data[1:]:
                ema_val = (price - ema_val) * multiplier + ema_val
            return ema_val
        
        # MACD线
        ema_fast = ema(prices[-(slow+signal):], fast)
        ema_slow = ema(prices[-(slow+signal):], slow)
        macd_line = ema_fast - ema_slow
        
        # 信号线（简化）
        signal_line = macd_line * 0.8  # 简化计算
        
        # 柱状图
        histogram = macd_line - signal_line
        
        # 趋势判断
        if histogram > 0 and macd_line > 0:
            trend = "BULLISH"
        elif histogram < 0 and macd_line < 0:
            trend = "BEARISH"
        else:
            trend = "NEUTRAL"
        
        return {
            "macd": round(macd_line, 4),
            "signal": round(signal_line, 4),
            "histogram": round(histogram, 4),
            "trend": trend
        }
    
    def calculate_bollinger(self, prices: List[float], period: int = 20, std_dev: float = 2) -> Dict:
        """计算布林带"""
        if len(prices) < period:
            return {"upper": 0, "middle": 0, "lower": 0, "position": "MIDDLE"}
        
        recent = prices[-period:]
        middle = sum(recent) / period
        
        # 标准差
        variance = sum((p - middle) ** 2 for p in recent) / period
        std = variance ** 0.5
        
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        current = prices[-1]
        
        # 位置判断
        if current >= upper:
            position = "UPPER"
        elif current <= lower:
            position = "LOWER"
        else:
            position = "MIDDLE"
        
        return {
            "upper": round(upper, 2),
            "middle": round(middle, 2),
            "lower": round(lower, 2),
            "current": round(current, 2),
            "position": position,
            "bandwidth": round((upper - lower) / middle * 100, 2)
        }
    
    def calculate_volume_profile(self, volumes: List[float]) -> Dict:
        """计算成交量概况"""
        if not volumes:
            return {"average": 0, "trend": "NEUTRAL"}
        
        avg = sum(volumes) / len(volumes)
        recent_avg = sum(volumes[-5:]) / min(5, len(volumes)) if len(volumes) >= 5 else avg
        
        if recent_avg > avg * 1.5:
            trend = "INCREASING"
        elif recent_avg < avg * 0.5:
            trend = "DECREASING"
        else:
            trend = "STABLE"
        
        return {
            "average": round(avg, 2),
            "recent_average": round(recent_avg, 2),
            "trend": trend
        }
    
    def get_full_analysis(self, symbol: str, prices: List[float], volumes: List[float] = None) -> Dict:
        """获取完整技术分析"""
        analysis = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "indicators": {}
        }
        
        # RSI
        analysis['indicators']['rsi'] = self.calculate_rsi(prices)
        
        # MACD
        analysis['indicators']['macd'] = self.calculate_macd(prices)
        
        # 布林带
        analysis['indicators']['bollinger'] = self.calculate_bollinger(prices)
        
        # 成交量
        if volumes:
            analysis['indicators']['volume'] = self.calculate_volume_profile(volumes)
        
        # 综合信号
        signals = []
        
        rsi_signal = analysis['indicators']['rsi']['signal']
        if rsi_signal == "OVERSOLD":
            signals.append("RSI超卖→买入信号")
        elif rsi_signal == "OVERBOUGHT":
            signals.append("RSI超买→卖出信号")
        
        macd_trend = analysis['indicators']['macd']['trend']
        if macd_trend == "BULLISH":
            signals.append("MACD看涨")
        elif macd_trend == "BEARISH":
            signals.append("MACD看跌")
        
        bb_position = analysis['indicators']['bollinger']['position']
        if bb_position == "LOWER":
            signals.append("触及布林下轨→可能反弹")
        elif bb_position == "UPPER":
            signals.append("触及布林上轨→可能回调")
        
        analysis['signals'] = signals
        
        # 综合评分 (-100 到 100)
        score = 0
        score += (50 - analysis['indicators']['rsi']['value'])  # RSI低分高
        score += 20 if macd_trend == "BULLISH" else -20 if macd_trend == "BEARISH" else 0
        score += 15 if bb_position == "LOWER" else -15 if bb_position == "UPPER" else 0
        
        analysis['score'] = max(-100, min(100, score))
        
        if score > 30:
            analysis['recommendation'] = "BUY"
        elif score < -30:
            analysis['recommendation'] = "SELL"
        else:
            analysis['recommendation'] = "HOLD"
        
        return analysis


# =============================================================================
# 3. 邮件通知系统
# =============================================================================

class EmailNotifier:
    """邮件通知系统"""
    
    def __init__(self):
        # 邮箱配置
        self.smtp_server = "smtp.163.com"
        self.smtp_port = 465
        self.sender = "pandac00@163.com"
        
        # 获取密码
        self.password = self._get_email_password()
        self.recipient = "19922307306@189.cn"
    
    def _get_email_password(self) -> str:
        """获取邮箱密码"""
        try:
            # 从加密存储获取
            import subprocess
            result = subprocess.run(
                ["python3", "/home/admin/Ziwei/scripts/secure_key_storage.py", "get", "EMAIL_PASSWORD", "email"],
                capture_output=True,
                text=True,
                env={**os.environ, "ZIWEI_KEY_PASSWORD": "mimajiushimima"}
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        # 备用：直接使用（实际项目中应该加密）
        return "your_email_password"  # 需要配置
    
    def send_trade_notification(self, trade_info: Dict) -> bool:
        """发送交易通知"""
        subject = f"💰 交易通知: {trade_info.get('action', 'TRADE')}"
        
        body = f"""
交易详情：
-------------------
市场: {trade_info.get('market', 'N/A')}
方向: {trade_info.get('outcome', 'N/A')}
金额: ${trade_info.get('amount', 0):.2f}
概率: {trade_info.get('probability', 0):.0%}
置信度: {trade_info.get('confidence', 0):.0%}

原因: {trade_info.get('reason', 'N/A')}

时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-------------------
"""
        
        return self._send_email(subject, body)
    
    def send_opportunity_alert(self, opportunities: List[Dict]) -> bool:
        """发送机会警报"""
        if not opportunities:
            return False
        
        subject = f"🔥 发现 {len(opportunities)} 个交易机会"
        
        body = "交易机会：\n" + "="*50 + "\n\n"
        
        for i, opp in enumerate(opportunities[:5], 1):
            body += f"{i}. {opp.get('market', 'N/A')[:50]}\n"
            body += f"   边缘: {opp.get('edge', 0):.0%}\n"
            body += f"   建议: {opp.get('recommendation', 'N/A')}\n"
            body += f"   原因: {opp.get('reason', 'N/A')}\n\n"
        
        return self._send_email(subject, body)
    
    def send_daily_report(self, stats: Dict) -> bool:
        """发送每日报告"""
        subject = f"📊 每日报告 - {datetime.now().strftime('%Y-%m-%d')}"
        
        body = f"""
每日交易报告
===================

账户状态：
- 余额: ${stats.get('cash', 0):.2f}
- 持仓: {stats.get('open_trades', 0)} 笔
- 盈亏: ${stats.get('pnl', 0):.2f}

交易统计：
- 总交易: {stats.get('total_trades', 0)} 笔
- 胜率: {stats.get('win_rate', 0):.0%}

市场情绪：
- 新闻情绪: {stats.get('news_sentiment', 'N/A')}
- 技术信号: {stats.get('tech_signal', 'N/A')}

===================
报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return self._send_email(subject, body)
    
    def _send_email(self, subject: str, body: str) -> bool:
        """发送邮件"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = self.recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender, self.password)
                server.send_message(msg)
            
            print(f"   ✅ 邮件已发送: {subject}")
            return True
            
        except Exception as e:
            print(f"   ⚠️ 邮件发送失败: {e}")
            return False


# =============================================================================
# 4. 整合所有功能的主系统
# =============================================================================

class MoneyBrainUltra:
    """赚钱大脑 Ultra - 整合新闻+技术+通知"""
    
    def __init__(self):
        self.news_fetcher = RealNewsFetcher()
        self.tech_analyzer = TechnicalIndicators()
        self.emailer = EmailNotifier()
        
        self.trades_file = TRADE_DIR / "trades.json"
        self.balance_file = TRADE_DIR / "balance.json"
        self.log_file = LOG_DIR / "money_brain_ultra.log"
        
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
    
    def run_analysis(self) -> Dict:
        """运行完整分析"""
        self.log("\n" + "="*60)
        self.log("🧠 赚钱大脑 Ultra 启动")
        self.log("="*60)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "news": {},
            "technical": {},
            "opportunities": [],
            "trades": []
        }
        
        # 1. 获取新闻
        self.log("\n📰 获取新闻...")
        crypto_news = self.news_fetcher.get_crypto_news()
        ai_news = self.news_fetcher.get_ai_news()
        
        crypto_sentiment = self.news_fetcher.get_aggregated_sentiment(crypto_news)
        ai_sentiment = self.news_fetcher.get_aggregated_sentiment(ai_news)
        
        result['news'] = {
            "crypto": {
                "count": len(crypto_news),
                "sentiment": crypto_sentiment
            },
            "ai": {
                "count": len(ai_news),
                "sentiment": ai_sentiment
            }
        }
        
        self.log(f"   加密新闻: {len(crypto_news)}条, 情绪: {crypto_sentiment['direction']}")
        self.log(f"   AI新闻: {len(ai_news)}条, 情绪: {ai_sentiment['direction']}")
        
        # 2. 获取价格并计算技术指标
        self.log("\n📊 计算技术指标...")
        prices = self._get_mock_prices()  # 实际应该获取真实价格
        
        btc_analysis = self.tech_analyzer.get_full_analysis("BTC", prices)
        eth_analysis = self.tech_analyzer.get_full_analysis("ETH", [p * 0.05 for p in prices])
        
        result['technical'] = {
            "BTC": btc_analysis,
            "ETH": eth_analysis
        }
        
        self.log(f"   BTC: RSI={btc_analysis['indicators']['rsi']['value']}, "
                f"MACD={btc_analysis['indicators']['macd']['trend']}, "
                f"建议={btc_analysis['recommendation']}")
        self.log(f"   ETH: RSI={eth_analysis['indicators']['rsi']['value']}, "
                f"MACD={eth_analysis['indicators']['macd']['trend']}, "
                f"建议={eth_analysis['recommendation']}")
        
        # 3. 综合决策
        self.log("\n🎯 综合决策...")
        decision = self._make_decision(result)
        
        if decision['action'] != 'HOLD':
            result['trades'].append(decision)
            self.log(f"   💰 决策: {decision['action']} ${decision.get('amount', 0)}")
            
            # 发送邮件通知
            if decision.get('amount', 0) > 10:
                self.emailer.send_trade_notification(decision)
        else:
            self.log(f"   ⏸️ 决策: {decision['reason']}")
        
        # 4. 保存结果
        self._save_state()
        
        return result
    
    def _get_mock_prices(self) -> List[float]:
        """获取模拟价格数据（实际应该获取真实历史价格）"""
        base = 90000
        prices = []
        for i in range(30):
            change = random.uniform(-0.02, 0.02)
            base = base * (1 + change)
            prices.append(base)
        return prices
    
    def _make_decision(self, analysis: Dict) -> Dict:
        """综合决策"""
        # 获取各种信号
        crypto_sentiment = analysis['news']['crypto']['sentiment']['score']
        ai_sentiment = analysis['news']['ai']['sentiment']['score']
        btc_signal = analysis['technical']['BTC']['score']
        
        # 综合评分
        combined_score = (
            (crypto_sentiment - 0.5) * 100 +  # 新闻情绪
            btc_signal * 0.5                   # 技术信号
        )
        
        # 决策
        if combined_score > 30:
            return {
                "action": "BUY",
                "amount": min(20, self.balance['cash'] * 0.1),
                "reason": f"综合评分{combined_score:.0f}>30，看涨",
                "confidence": min(0.8, combined_score / 100)
            }
        elif combined_score < -30:
            return {
                "action": "SELL",
                "amount": min(20, self.balance['cash'] * 0.1),
                "reason": f"综合评分{combined_score:.0f}<-30，看跌",
                "confidence": min(0.8, -combined_score / 100)
            }
        else:
            return {
                "action": "HOLD",
                "reason": f"综合评分{combined_score:.0f}在中间区间，观望"
            }
    
    def send_daily_report(self):
        """发送每日报告"""
        stats = {
            "cash": self.balance['cash'],
            "open_trades": len([t for t in self.trades if t.get('status') == 'open']),
            "total_trades": len(self.trades),
            "pnl": self.balance['cash'] - 1000
        }
        
        # 获取新闻情绪
        crypto_news = self.news_fetcher.get_crypto_news()
        sentiment = self.news_fetcher.get_aggregated_sentiment(crypto_news)
        stats['news_sentiment'] = sentiment['direction']
        
        self.emailer.send_daily_report(stats)


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="赚钱大脑 Ultra")
    parser.add_argument("--run", action="store_true", help="运行分析")
    parser.add_argument("--report", action="store_true", help="发送每日报告")
    parser.add_argument("--test-email", action="store_true", help="测试邮件")
    
    args = parser.parse_args()
    
    brain = MoneyBrainUltra()
    
    if args.test_email:
        print("测试邮件发送...")
        brain.emailer.send_trade_notification({
            "action": "TEST",
            "market": "测试市场",
            "outcome": "YES",
            "amount": 10,
            "probability": 0.6,
            "confidence": 0.7,
            "reason": "测试邮件通知"
        })
    
    elif args.report:
        brain.send_daily_report()
    
    else:
        brain.run_analysis()