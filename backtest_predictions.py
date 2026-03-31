#!/usr/bin/env python3
"""
回测预测系统准确率
紫微智控智能智慧系统
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import random

INTEL_DIR = Path("/home/admin/Ziwei/data/intel")

# 情感关键词（与系统一致）
POSITIVE_WORDS = [
    'surge', 'soar', 'jump', 'rally', 'gain', 'rise', 'increase', 'bullish',
    'breakthrough', 'milestone', 'partnership', 'adoption', 'upgrade',
    'record', 'high', 'growth', 'profit', 'success', 'positive',
    '暴涨', '飙升', '上涨', '突破', '利好', '合作', '升级', '增长',
    '创纪录', '新高', '成功', '积极', 'tops', 'above', 'climbs', 'hits'
]

NEGATIVE_WORDS = [
    'crash', 'plunge', 'drop', 'fall', 'decline', 'loss', 'bearish',
    'hack', 'attack', 'scam', 'fraud', 'regulation', 'ban', 'warning',
    'risk', 'crisis', 'collapse', 'fail', 'negative',
    '暴跌', '下跌', '崩盘', '黑客', '攻击', '诈骗', '监管', '禁止',
    '警告', '风险', '危机', '失败', '消极', 'dumps', 'tumbles', 'sinks'
]

def analyze_sentiment(text):
    """分析情感得分"""
    text_lower = text.lower()
    positive_count = sum(1 for word in POSITIVE_WORDS if word in text_lower)
    negative_count = sum(1 for word in NEGATIVE_WORDS if word in text_lower)
    
    if positive_count + negative_count == 0:
        return 0, 'neutral'
    
    score = (positive_count - negative_count) / (positive_count + negative_count) * 5
    
    if score >= 2:
        return score, 'bullish'
    elif score <= -2:
        return score, 'bearish'
    else:
        return score, 'neutral'

def load_intel_file(filepath):
    """加载intel文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def run_backtest(sample_size=100, prediction_window_hours=4):
    """
    回测预测准确率
    
    Args:
        sample_size: 采样数量
        prediction_window_hours: 预测窗口（小时）
    """
    print("=" * 60)
    print("🔍 预测系统回测")
    print("=" * 60)
    
    # 获取所有intel文件
    intel_files = sorted(INTEL_DIR.glob("intel_*.json"))
    total_files = len(intel_files)
    
    print(f"\n📊 数据概览：")
    print(f"   总文件数：{total_files}")
    print(f"   时间跨度：{intel_files[0].name} 到 {intel_files[-1].name}")
    print(f"   采样数量：{sample_size}")
    print(f"   预测窗口：{prediction_window_hours} 小时")
    
    # 均匀采样
    step = max(1, total_files // sample_size)
    sampled_files = intel_files[::step][:sample_size]
    
    results = {
        'total': 0,
        'correct': 0,
        'wrong': 0,
        'neutral': 0,
        'bullish_correct': 0,
        'bullish_wrong': 0,
        'bearish_correct': 0,
        'bearish_wrong': 0,
        'details': []
    }
    
    # 预测窗口对应的文件数量（约每小时1个文件）
    window_files = prediction_window_hours
    
    for i, filepath in enumerate(sampled_files):
        if i + window_files >= len(sampled_files):
            break
            
        # 当前数据
        current_data = load_intel_file(filepath)
        if not current_data:
            continue
            
        # 未来数据
        future_data = load_intel_file(sampled_files[i + window_files])
        if not future_data:
            continue
        
        # 提取新闻和价格
        current_prices = current_data.get('prices', {})
        future_prices = future_data.get('prices', {})
        news = current_data.get('news', {})
        
        # 对每个币种进行预测
        for coin in ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE']:
            if coin not in current_prices or coin not in future_prices:
                continue
            
            current_price = current_prices[coin].get('price', 0)
            future_price = future_prices[coin].get('price', 0)
            
            if current_price <= 0:
                continue
            
            # 计算实际价格变化
            actual_change = (future_price - current_price) / current_price * 100
            
            # 分析新闻情感
            coin_news = news.get(coin, [])
            news_text = ' '.join([n.get('title', '') for n in coin_news[:5]])
            sentiment_score, prediction = analyze_sentiment(news_text)
            
            # 判断预测是否正确
            results['total'] += 1
            
            if prediction == 'neutral':
                results['neutral'] += 1
                continue
            
            actual_direction = 'bullish' if actual_change > 0 else 'bearish'
            
            is_correct = prediction == actual_direction
            
            if is_correct:
                results['correct'] += 1
                if prediction == 'bullish':
                    results['bullish_correct'] += 1
                else:
                    results['bearish_correct'] += 1
            else:
                results['wrong'] += 1
                if prediction == 'bullish':
                    results['bullish_wrong'] += 1
                else:
                    results['bearish_wrong'] += 1
            
            # 记录详情
            results['details'].append({
                'coin': coin,
                'time': filepath.name,
                'current_price': current_price,
                'future_price': future_price,
                'actual_change': actual_change,
                'prediction': prediction,
                'sentiment_score': sentiment_score,
                'is_correct': is_correct
            })
    
    # 计算准确率
    total_predictions = results['correct'] + results['wrong']
    accuracy = (results['correct'] / total_predictions * 100) if total_predictions > 0 else 0
    
    print("\n" + "=" * 60)
    print("📈 回测结果")
    print("=" * 60)
    
    print(f"\n📊 总体统计：")
    print(f"   总预测数：{results['total']}")
    print(f"   有效预测（非中性）：{total_predictions}")
    print(f"   中性预测：{results['neutral']}")
    
    print(f"\n🎯 准确率：")
    print(f"   正确：{results['correct']} ({results['correct']/total_predictions*100:.1f}%)")
    print(f"   错误：{results['wrong']} ({results['wrong']/total_predictions*100:.1f}%)")
    print(f"   准确率：{accuracy:.1f}%")
    
    print(f"\n🐂 看涨预测：")
    bullish_total = results['bullish_correct'] + results['bullish_wrong']
    if bullish_total > 0:
        print(f"   正确：{results['bullish_correct']}")
        print(f"   错误：{results['bullish_wrong']}")
        print(f"   准确率：{results['bullish_correct']/bullish_total*100:.1f}%")
    
    print(f"\n🐻 看跌预测：")
    bearish_total = results['bearish_correct'] + results['bearish_wrong']
    if bearish_total > 0:
        print(f"   正确：{results['bearish_correct']}")
        print(f"   错误：{results['bearish_wrong']}")
        print(f"   准确率：{results['bearish_correct']/bearish_total*100:.1f}%")
    
    # 分析错误预测的损失
    print(f"\n💰 如果按预测交易：")
    total_profit = 0
    total_loss = 0
    
    for detail in results['details']:
        if detail['prediction'] != 'neutral':
            change = detail['actual_change']
            if detail['is_correct']:
                # 正确预测：赚取变化幅度
                total_profit += abs(change)
            else:
                # 错误预测：亏损变化幅度
                total_loss += abs(change)
    
    net_result = total_profit - total_loss
    print(f"   总盈利点数：+{total_profit:.2f}%")
    print(f"   总亏损点数：-{total_loss:.2f}%")
    print(f"   净结果：{net_result:+.2f}%")
    
    if total_predictions > 0:
        avg_per_trade = net_result / total_predictions
        print(f"   平均每笔交易：{avg_per_trade:+.2f}%")
    
    # 显示一些具体案例
    print(f"\n📋 具体案例（前10个）：")
    print("-" * 60)
    
    for detail in results['details'][:10]:
        status = "✅" if detail['is_correct'] else "❌"
        print(f"{status} {detail['coin']} | {detail['prediction']:8} | "
              f"${detail['current_price']:.2f} → ${detail['future_price']:.2f} | "
              f"{detail['actual_change']:+.2f}%")
    
    return results

if __name__ == "__main__":
    import sys
    
    sample_size = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    window = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    
    results = run_backtest(sample_size, window)
    
    # 保存结果
    output_file = INTEL_DIR.parent / "backtest_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total': results['total'],
                'correct': results['correct'],
                'wrong': results['wrong'],
                'neutral': results['neutral'],
                'accuracy': results['correct'] / (results['correct'] + results['wrong']) * 100 if (results['correct'] + results['wrong']) > 0 else 0
            },
            'details': results['details'][:100]  # 只保存前100个详情
        }, f, indent=2, default=str)
    
    print(f"\n💾 结果已保存到：{output_file}")