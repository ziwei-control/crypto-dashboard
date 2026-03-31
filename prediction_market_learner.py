#!/usr/bin/env python3
"""
预测市场学习连接器
将预测市场数据与自动学习系统打通
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path

BASE_DIR = Path("/home/admin/Ziwei")
DATA_DIR = BASE_DIR / "data"
PM_DATA_DIR = DATA_DIR / "prediction_market"
LEARNING_DIR = BASE_DIR / "learning" / "prediction_market"


def fetch_hot_markets():
    """获取热门市场数据"""
    print("📡 获取热门市场...")
    
    # Manifold Markets
    resp = requests.get("https://api.manifold.markets/v0/markets?limit=20")
    markets = resp.json()
    
    # 按交易量排序
    by_volume = sorted(markets, key=lambda x: x.get('volume', 0) or 0, reverse=True)
    
    hot_markets = []
    for m in by_volume[:10]:
        hot_markets.append({
            "question": m.get('question', ''),
            "probability": m.get('probability', 0.5),
            "volume": m.get('volume', 0),
            "url": f"https://manifold.markets/{m.get('creatorSlug', '')}/{m.get('slug', '')}"
        })
    
    return hot_markets


def extract_learning_topics(markets):
    """从市场数据提取学习主题"""
    topics = []
    
    for m in markets:
        q = m['question'].lower()
        prob = m['probability']
        volume = m['volume']
        
        # 识别主题类型
        if 'btc' in q or 'bitcoin' in q or 'crypto' in q:
            topics.append({
                "topic": "BTC/加密货币预测",
                "market": m['question'],
                "learning_needed": [
                    "BTC技术分析",
                    "链上数据分析",
                    "宏观经济影响"
                ],
                "priority": 1 if volume > 3000 else 2
            })
        
        elif 'league' in q or 'win' in q or 'match' in q or 'cup' in q:
            topics.append({
                "topic": "体育预测",
                "market": m['question'],
                "learning_needed": [
                    "球队数据分析",
                    "伤病影响评估",
                    "历史对战记录"
                ],
                "priority": 1 if volume > 2000 else 2
            })
        
        elif 'election' in q or 'vote' in q or 'president' in q:
            topics.append({
                "topic": "政治预测",
                "market": m['question'],
                "learning_needed": [
                    "民调数据分析",
                    "选举制度研究",
                    "历史选举模式"
                ],
                "priority": 2
            })
        
        elif 'price' in q or 'stock' in q or 's&p' in q:
            topics.append({
                "topic": "金融预测",
                "market": m['question'],
                "learning_needed": [
                    "技术分析",
                    "基本面分析",
                    "市场情绪分析"
                ],
                "priority": 1 if volume > 1000 else 2
            })
    
    # 去重
    seen = set()
    unique_topics = []
    for t in topics:
        if t['topic'] not in seen:
            seen.add(t['topic'])
            unique_topics.append(t)
    
    return unique_topics


def generate_study_plan(topics):
    """生成学习计划"""
    print("\n📚 生成学习计划...")
    
    plan = {
        "created": datetime.now().isoformat(),
        "total_topics": len(topics),
        "priority_topics": [t for t in topics if t['priority'] == 1],
        "other_topics": [t for t in topics if t['priority'] == 2],
        "study_sequence": []
    }
    
    # 生成学习序列
    sequence = []
    
    for i, topic in enumerate(plan['priority_topics'][:3], 1):
        sequence.append({
            "day": i,
            "topic": topic['topic'],
            "market": topic['market'],
            "tasks": topic['learning_needed'],
            "goal": f"理解{topic['topic']}的关键因素，能做出预测"
        })
    
    plan['study_sequence'] = sequence
    
    return plan


def update_learning_progress(plan):
    """更新学习进度"""
    progress_file = PM_DATA_DIR / "adaptive_learning_progress.json"
    
    PM_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    progress = {
        "last_update": datetime.now().isoformat(),
        "current_plan": plan,
        "completed_topics": [],
        "insights": []
    }
    
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            old_progress = json.load(f)
            progress['completed_topics'] = old_progress.get('completed_topics', [])
            progress['insights'] = old_progress.get('insights', [])
    
    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 学习进度已更新: {progress_file}")
    
    return progress


def main():
    print("=" * 60)
    print("🔗 预测市场学习连接器")
    print("=" * 60)
    
    # 1. 获取热门市场
    markets = fetch_hot_markets()
    print(f"\n📊 获取到 {len(markets)} 个热门市场")
    
    for i, m in enumerate(markets[:5], 1):
        print(f"  {i}. {m['question'][:40]}... (${m['volume']:,.0f})")
    
    # 2. 提取学习主题
    topics = extract_learning_topics(markets)
    print(f"\n🎯 识别出 {len(topics)} 个学习主题:")
    
    for t in topics:
        print(f"  • {t['topic']} (优先级: {t['priority']})")
    
    # 3. 生成学习计划
    plan = generate_study_plan(topics)
    
    print("\n📅 学习序列:")
    for item in plan['study_sequence']:
        print(f"  Day {item['day']}: {item['topic']}")
        print(f"    目标: {item['goal']}")
        print(f"    任务: {', '.join(item['tasks'])}")
    
    # 4. 更新学习进度
    progress = update_learning_progress(plan)
    
    print("\n" + "=" * 60)
    print("✅ 学习连接完成")
    print("=" * 60)
    
    return plan


if __name__ == "__main__":
    main()
