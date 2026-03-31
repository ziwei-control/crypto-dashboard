#!/usr/bin/env python3
# =============================================================================
# 全球战情室 - 新闻市场影响分析系统
# 紫微智控智能智慧系统
# 功能：分析时效新闻保管库的新闻，预测对加密市场具体币种的价格影响
# =============================================================================

import os
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# 配置
TEMP_NEWS_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "data" / "warroom" / "temp_news"
ANALYSIS_DIR = Path("/home/admin/Ziwei/data/warroom/analysis")
INTEL_DIR = Path("/home/admin/Ziwei/data/intel")

# 币种映射（新闻关键词 → 交易对）
COIN_MAPPING = {
    'BTC': 'BTC/USDT',
    'Bitcoin': 'BTC/USDT',
    'ETH': 'ETH/USDT',
    'Ethereum': 'ETH/USDT',
    'BNB': 'BNB/USDT',
    'XRP': 'XRP/USDT',
    'SOL': 'SOL/USDT',
    'ADA': 'ADA/USDT',
    'DOGE': 'DOGE/USDT',
    'TRX': 'TRX/USDT',
    'AVAX': 'AVAX/USDT',
    'LINK': 'LINK/USDT',
    'MATIC': 'MATIC/USDT',
    'TON': 'TON/USDT',
    'SHIB': 'SHIB/USDT',
    'LTC': 'LTC/USDT',
    'BCH': 'BCH/USDT',
    'UNI': 'UNI/USDT',
    'ATOM': 'ATOM/USDT',
    'DOT': 'DOT/USDT',
}

# 影响程度权重
IMPACT_WEIGHTS = {
    'extremely_positive': 0.15,    # 极大利好 +15%
    'very_positive': 0.08,         # 重大利好 +8%
    'positive': 0.03,              # 利好 +3%
    'neutral': 0.0,                # 中性 0%
    'negative': -0.03,             # 利空 -3%
    'very_negative': -0.08,        # 重大利空 -8%
    'extremely_negative': -0.15,   # 极大利空 -15%
}


class NewsMarketAnalyzer:
    """新闻市场影响分析器"""
    
    def __init__(self):
        self.ensure_directories()
        self.current_prices = {}
        self.load_current_prices()
    
    def ensure_directories(self):
        """确保目录存在"""
        ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
        (ANALYSIS_DIR / 'reports').mkdir(exist_ok=True)
        (ANALYSIS_DIR / 'predictions').mkdir(exist_ok=True)
    
    def load_current_prices(self):
        """加载当前价格数据"""
        try:
            if INTEL_DIR.exists():
                intel_files = sorted(INTEL_DIR.glob("intel_*.json"), reverse=True)
                if intel_files:
                    with open(intel_files[0], 'r', encoding='utf-8') as f:
                        intel_data = json.load(f)
                    
                    prices = intel_data.get('prices', {})
                    for coin, data in prices.items():
                        symbol = f"{coin}/USDT"
                        self.current_prices[symbol] = data.get('price', 0)
        except Exception as e:
            print(f"⚠️ 加载价格数据失败：{e}")
    
    def analyze_news_sentiment(self, news_title: str, news_content: str = "") -> Dict:
        """
        分析新闻情感（使用紫微智控 AI 系统）
        
        返回：
        {
            'sentiment': 'positive'|'negative'|'neutral',
            'score': -5 to 5,
            'confidence': 0-1,
            'impact_level': 'extremely_positive'|'very_positive'|'positive'|'neutral'|'negative'|'very_negative'|'extremely_negative',
            'keywords': [],
            'summary': ''
        }
        """
        try:
            # 调用紫微智控 AI 分析接口
            # 这里模拟 AI 分析结果，实际应该调用 AI API
            prompt = f"""
作为紫微智控智能智慧系统，请分析以下加密货币新闻的市场影响：

新闻标题：{news_title}
新闻内容：{news_content[:500] if news_content else ''}

请分析：
1. 情感倾向（positive/negative/neutral）
2. 情感得分（-5 到 5，负数为利空，正数为利好）
3. 置信度（0-1）
4. 影响程度（extremely_positive/very_positive/positive/neutral/negative/very_negative/extremely_negative）
5. 关键词（列表）
6. 摘要（100 字以内）
7. 影响的币种（列表）

请以 JSON 格式返回。
"""
            
            # TODO: 调用实际 AI API
            # 这里使用规则匹配模拟分析
            result = self.rule_based_analysis(news_title, news_content)
            
            return result
        
        except Exception as e:
            return {
                'sentiment': 'neutral',
                'score': 0,
                'confidence': 0.5,
                'impact_level': 'neutral',
                'keywords': [],
                'summary': '分析失败',
                'affected_coins': []
            }
    
    def rule_based_analysis(self, title: str, content: str = "") -> Dict:
        """基于规则的情感分析（简化版本）"""
        text = (title + " " + content).lower()
        
        # 利好关键词
        positive_words = [
            'surge', 'soar', 'jump', 'rally', 'gain', 'rise', 'increase', 'bullish',
            'breakthrough', 'milestone', 'partnership', 'adoption', 'upgrade',
            'record', 'high', 'growth', 'profit', 'success', 'positive',
            '暴涨', '飙升', '上涨', '突破', '利好', '合作', '升级', '增长',
            '创纪录', '新高', '成功', '积极'
        ]
        
        # 利空关键词
        negative_words = [
            'crash', 'plunge', 'drop', 'fall', 'decline', 'loss', 'bearish',
            'hack', 'attack', 'scam', 'fraud', 'regulation', 'ban', 'warning',
            'risk', 'crisis', 'collapse', 'fail', 'negative',
            '暴跌', '下跌', '崩盘', '黑客', '攻击', '诈骗', '监管', '禁止',
            '警告', '风险', '危机', '失败', '消极'
        ]
        
        # 计算情感得分
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        # 计算得分（-5 到 5）
        if positive_count + negative_count == 0:
            score = 0
        else:
            score = (positive_count - negative_count) / (positive_count + negative_count) * 5
        
        # 确定情感倾向
        if score >= 3:
            sentiment = 'positive'
            impact_level = 'very_positive' if score >= 4 else 'positive'
        elif score <= -3:
            sentiment = 'negative'
            impact_level = 'very_negative' if score <= -4 else 'negative'
        else:
            sentiment = 'neutral'
            impact_level = 'neutral'
        
        # 提取关键词
        keywords = []
        for word in positive_words + negative_words:
            if word in text and word not in keywords:
                keywords.append(word)
        
        # 识别影响的币种
        affected_coins = []
        for coin in COIN_MAPPING.keys():
            if coin.lower() in text:
                affected_coins.append(coin)
        
        # 生成摘要
        summary = f"分析 {len(keywords)} 个关键词，情感得分 {score:.1f}"
        
        return {
            'sentiment': sentiment,
            'score': round(score, 2),
            'confidence': min(0.9, 0.5 + (positive_count + negative_count) * 0.05),
            'impact_level': impact_level,
            'keywords': keywords[:10],
            'summary': summary,
            'affected_coins': affected_coins[:5]
        }
    
    def calculate_price_impact(self, coin: str, impact_level: str, current_price: float) -> Dict:
        """
        计算价格影响
        
        返回：
        {
            'current_price': float,
            'predicted_price': float,
            'change_percent': float,
            'change_amount': float,
            'support_level': float,
            'resistance_level': float,
            'timeframe': '24h'|'7d'|'30d'
        }
        """
        # 获取影响权重
        weight = IMPACT_WEIGHTS.get(impact_level, 0)
        
        # 计算价格变化
        change_amount = current_price * weight
        predicted_price = current_price + change_amount
        
        # 计算支撑位和阻力位
        if weight > 0:
            # 利好：支撑位为当前价，阻力位为预测价
            support_level = current_price * 0.95
            resistance_level = predicted_price * 1.05
        elif weight < 0:
            # 利空：支撑位为预测价，阻力位为当前价
            support_level = predicted_price * 0.95
            resistance_level = current_price * 1.05
        else:
            # 中性
            support_level = current_price * 0.98
            resistance_level = current_price * 1.02
        
        return {
            'current_price': round(current_price, 2),
            'predicted_price': round(predicted_price, 2),
            'change_percent': round(weight * 100, 2),
            'change_amount': round(change_amount, 2),
            'support_level': round(support_level, 2),
            'resistance_level': round(resistance_level, 2),
            'timeframe': '24h'
        }
    
    def analyze_news_file(self, news_file: Path) -> Dict:
        """分析单个新闻文件"""
        try:
            with open(news_file, 'r', encoding='utf-8') as f:
                news_data = json.load(f)
            
            news_items = news_data.get('news', {})
            analysis_results = {
                'file': news_file.name,
                'analyzed_at': datetime.now().isoformat(),
                'total_news': 0,
                'coin_analysis': {}
            }
            
            # 按币种分析新闻
            for coin, articles in news_items.items():
                if coin not in COIN_MAPPING:
                    continue
                
                coin_results = {
                    'coin': coin,
                    'symbol': COIN_MAPPING[coin],
                    'news_count': len(articles),
                    'avg_sentiment_score': 0,
                    'overall_impact': 'neutral',
                    'price_prediction': {},
                    'key_news': []
                }
                
                # 分析每篇新闻
                sentiment_scores = []
                for article in articles[:5]:  # 只分析前 5 篇
                    title = article.get('title', '')
                    sentiment = self.analyze_news_sentiment(title)
                    sentiment_scores.append(sentiment['score'])
                    
                    if sentiment['score'] != 0:
                        coin_results['key_news'].append({
                            'title': title[:100],
                            'sentiment': sentiment['sentiment'],
                            'score': sentiment['score'],
                            'impact': sentiment['impact_level']
                        })
                
                # 计算平均情感得分
                if sentiment_scores:
                    avg_score = sum(sentiment_scores) / len(sentiment_scores)
                    coin_results['avg_sentiment_score'] = round(avg_score, 2)
                    
                    # 确定整体影响
                    if avg_score >= 3:
                        coin_results['overall_impact'] = 'very_positive'
                    elif avg_score >= 1:
                        coin_results['overall_impact'] = 'positive'
                    elif avg_score <= -3:
                        coin_results['overall_impact'] = 'very_negative'
                    elif avg_score <= -1:
                        coin_results['overall_impact'] = 'negative'
                    else:
                        coin_results['overall_impact'] = 'neutral'
                
                # 计算价格影响
                symbol = COIN_MAPPING[coin]
                current_price = self.current_prices.get(symbol, 0)
                if current_price > 0:
                    coin_results['price_prediction'] = self.calculate_price_impact(
                        coin,
                        coin_results['overall_impact'],
                        current_price
                    )
                
                analysis_results['coin_analysis'][coin] = coin_results
                analysis_results['total_news'] += len(articles)
            
            return analysis_results
        
        except Exception as e:
            return {
                'error': str(e),
                'file': news_file.name
            }
    
    def generate_market_report(self) -> Dict:
        """生成市场分析报告"""
        # 获取最新的暂存新闻文件
        if not TEMP_NEWS_DIR.exists():
            return {'error': '时效新闻保管库不存在'}
        
        news_files = sorted(TEMP_NEWS_DIR.glob("news_*.json"), reverse=True)[:5]
        
        if not news_files:
            return {'error': '暂无新闻数据'}
        
        # 分析所有新闻文件
        all_analysis = []
        for news_file in news_files:
            analysis = self.analyze_news_file(news_file)
            if 'error' not in analysis:
                all_analysis.append(analysis)
        
        # 汇总分析结果
        market_report = {
            'report_time': datetime.now().isoformat(),
            'analyzed_files': len(all_analysis),
            'total_news': sum(a['total_news'] for a in all_analysis),
            'market_overview': {
                'overall_sentiment': 'neutral',
                'bullish_coins': [],
                'bearish_coins': [],
                'neutral_coins': []
            },
            'coin_predictions': {},
            'top_news': [],
            'recommendations': []
        }
        
        # 汇总币种分析
        coin_sentiments = {}
        for analysis in all_analysis:
            for coin, data in analysis.get('coin_analysis', {}).items():
                if coin not in coin_sentiments:
                    coin_sentiments[coin] = []
                coin_sentiments[coin].append(data['avg_sentiment_score'])
        
        # 计算每个币种的总体情感
        for coin, scores in coin_sentiments.items():
            avg_score = sum(scores) / len(scores) if scores else 0
            
            symbol = COIN_MAPPING.get(coin, f"{coin}/USDT")
            current_price = self.current_prices.get(symbol, 0)
            
            if avg_score >= 1:
                market_report['market_overview']['bullish_coins'].append(coin)
                impact = 'positive' if avg_score < 3 else 'very_positive'
            elif avg_score <= -1:
                market_report['market_overview']['bearish_coins'].append(coin)
                impact = 'negative' if avg_score > -3 else 'very_negative'
            else:
                market_report['market_overview']['neutral_coins'].append(coin)
                impact = 'neutral'
            
            # 价格预测
            if current_price > 0:
                price_prediction = self.calculate_price_impact(coin, impact, current_price)
                market_report['coin_predictions'][coin] = {
                    'symbol': symbol,
                    'sentiment_score': round(avg_score, 2),
                    'impact': impact,
                    'price_prediction': price_prediction,
                    'confidence': 'high' if abs(avg_score) >= 3 else 'medium' if abs(avg_score) >= 1 else 'low'
                }
        
        # 生成投资建议
        market_report['recommendations'] = self.generate_recommendations(market_report)
        
        # 保存报告
        report_file = ANALYSIS_DIR / 'reports' / f"market_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(market_report, f, ensure_ascii=False, indent=2)
        
        market_report['report_file'] = str(report_file)
        
        return market_report
    
    def generate_recommendations(self, report: Dict) -> List[Dict]:
        """生成投资建议"""
        recommendations = []
        
        # 看涨币种推荐
        for coin in report['market_overview']['bullish_coins'][:3]:
            pred = report['coin_predictions'].get(coin, {})
            if pred:
                recommendations.append({
                    'type': 'BUY',
                    'coin': coin,
                    'symbol': pred.get('symbol', f"{coin}/USDT"),
                    'reason': f"新闻情感积极 (得分：{pred.get('sentiment_score', 0):.2f})",
                    'target_price': pred.get('price_prediction', {}).get('predicted_price', 0),
                    'confidence': pred.get('confidence', 'medium')
                })
        
        # 看跌币种推荐
        for coin in report['market_overview']['bearish_coins'][:3]:
            pred = report['coin_predictions'].get(coin, {})
            if pred:
                recommendations.append({
                    'type': 'SELL',
                    'coin': coin,
                    'symbol': pred.get('symbol', f"{coin}/USDT"),
                    'reason': f"新闻情感消极 (得分：{pred.get('sentiment_score', 0):.2f})",
                    'target_price': pred.get('price_prediction', {}).get('predicted_price', 0),
                    'confidence': pred.get('confidence', 'medium')
                })
        
        return recommendations
    
    def get_dashboard_data(self) -> Dict:
        """获取 Dashboard 显示数据"""
        report = self.generate_market_report()
        
        if 'error' in report:
            return report
        
        # 格式化 Dashboard 数据
        dashboard_data = {
            'status': 'success',
            'update_time': report['report_time'],
            'summary': {
                'analyzed_news': report['total_news'],
                'bullish_count': len(report['market_overview']['bullish_coins']),
                'bearish_count': len(report['market_overview']['bearish_coins']),
                'neutral_count': len(report['market_overview']['neutral_coins'])
            },
            'top_predictions': [],
            'recommendations': report['recommendations'][:5]
        }
        
        # 选取预测最显著的币种
        predictions = report['coin_predictions']
        sorted_coins = sorted(
            predictions.items(),
            key=lambda x: abs(x[1].get('sentiment_score', 0)),
            reverse=True
        )[:10]
        
        for coin, data in sorted_coins:
            dashboard_data['top_predictions'].append({
                'coin': coin,
                'symbol': data.get('symbol'),
                'sentiment_score': data.get('sentiment_score'),
                'current_price': data.get('price_prediction', {}).get('current_price'),
                'predicted_price': data.get('price_prediction', {}).get('predicted_price'),
                'change_percent': data.get('price_prediction', {}).get('change_percent'),
                'impact': data.get('impact'),
                'confidence': data.get('confidence')
            })
        
        return dashboard_data


def main():
    """主函数"""
    import sys
    
    print("=" * 70)
    print("🌍 全球战情室 - 新闻市场影响分析系统")
    print("🤖 紫微智控智能智慧系统")
    print("=" * 70)
    print()
    
    analyzer = NewsMarketAnalyzer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'analyze':
            # 分析新闻
            print("📊 分析新闻市场影响...")
            report = analyzer.generate_market_report()
            
            if 'error' in report:
                print(f"❌ {report['error']}")
            else:
                print(f"✅ 分析完成")
                print(f"   分析新闻：{report['total_news']} 条")
                print(f"   看涨币种：{len(report['market_overview']['bullish_coins'])}")
                print(f"   看跌币种：{len(report['market_overview']['bearish_coins'])}")
                print(f"   中性币种：{len(report['market_overview']['neutral_coins'])}")
                print(f"   报告文件：{report.get('report_file')}")
        
        elif command == 'dashboard':
            # 获取 Dashboard 数据
            print("📈 获取 Dashboard 数据...")
            data = analyzer.get_dashboard_data()
            print(json.dumps(data, ensure_ascii=False, indent=2))
        
        elif command == 'predict':
            # 预测特定币种
            if len(sys.argv) > 2:
                coin = sys.argv[2]
                print(f"🔮 预测 {coin} 价格走势...")
                
                report = analyzer.generate_market_report()
                if coin in report.get('coin_predictions', {}):
                    pred = report['coin_predictions'][coin]
                    print(f"币种：{coin}")
                    print(f"交易对：{pred.get('symbol')}")
                    print(f"情感得分：{pred.get('sentiment_score'):.2f}")
                    print(f"影响程度：{pred.get('impact')}")
                    print(f"当前价格：${pred.get('price_prediction', {}).get('current_price'):,.2f}")
                    print(f"预测价格：${pred.get('price_prediction', {}).get('predicted_price'):,.2f}")
                    print(f"变化幅度：{pred.get('price_prediction', {}).get('change_percent'):+.2f}%")
                    print(f"置信度：{pred.get('confidence')}")
                else:
                    print(f"❌ 未找到 {coin} 的预测数据")
            else:
                print("用法：python3 news_market_analyzer.py predict <COIN>")
        
        else:
            print(f"❌ 未知命令：{command}")
            print("\n可用命令:")
            print("  analyze   - 分析新闻市场影响")
            print("  dashboard - 获取 Dashboard 数据")
            print("  predict   - 预测特定币种价格")
    else:
        # 默认执行分析
        print("🔄 执行完整市场分析...")
        print()
        
        report = analyzer.generate_market_report()
        
        if 'error' in report:
            print(f"❌ {report['error']}")
        else:
            print(f"✅ 分析完成")
            print()
            print(f"📊 市场概览:")
            print(f"   分析新闻：{report['total_news']} 条")
            print(f"   看涨币种：{', '.join(report['market_overview']['bullish_coins'][:5])}")
            print(f"   看跌币种：{', '.join(report['market_overview']['bearish_coins'][:5])}")
            print()
            print(f"💡 投资建议:")
            for rec in report['recommendations'][:3]:
                print(f"   {rec['type']} {rec['symbol']} - {rec['reason']}")


if __name__ == '__main__':
    main()
