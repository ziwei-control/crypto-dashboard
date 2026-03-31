#!/usr/bin/env python3
"""
币安新币上市监控系统
监控即将上线的新币，提醒交易机会

部署方式：
nohup python3 new_listing_monitor.py > new_listing.log 2>&1 &
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("/home/admin/Ziwei/data/new_listing")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 历史新币数据（用于学习）
LISTING_HISTORY = []

def get_binance_announcements():
    """获取币安公告"""
    try:
        # 币安公告API
        url = "https://www.binance.com/bapi/composite/v1/public/cms/article/catalog/list/query"
        payload = {
            "type": 1,
            "catalogId": 48,  # 新币上线公告分类
            "page": 1,
            "pageSize": 10
        }
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
        
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        data = resp.json()
        
        articles = data.get('data', {}).get('articles', [])
        
        results = []
        for article in articles:
            title = article.get('title', '')
            # 检查是否是新币上线公告
            if 'Will List' in title or '上线' in title or 'List' in title:
                results.append({
                    'title': title,
                    'id': article.get('id'),
                    'releaseDate': article.get('releaseDate'),
                    'url': f"https://www.binance.com/zh-CN/support/announcement/{article.get('id')}"
                })
        
        return results
    except Exception as e:
        print(f"获取公告失败: {e}")
        return []

def parse_listing_info(title):
    """从公告标题解析新币信息"""
    # 示例: "Binance Will List XYZ (XYZ)"
    # 示例: "币安将上线 ABC (ABC)"
    
    import re
    
    # 匹配模式
    patterns = [
        r'Will List (\w+)',
        r'上线 (\w+)',
        r'List (\w+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    
    return None

def get_symbol_info(symbol):
    """获取交易对信息"""
    try:
        url = f"https://api.binance.com/api/v3/exchangeInfo?symbol={symbol}USDT"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        
        if 'symbols' in data:
            return data['symbols'][0]
        return None
    except:
        return None

def calculate_opportunity_score(symbol):
    """
    计算新币机会评分
    
    评分因素：
    - 是否 Launchpad 项目
    - 社区热度
    - 项目背景
    """
    # 这里简化处理，实际需要更多数据
    score = 50  # 基础分
    
    # 已知热门项目加分
    hot_projects = ['TON', 'ZK', 'ZRO', 'NOT', 'DOGS']
    if symbol in hot_projects:
        score += 30
    
    return score

def generate_trading_signal(symbol, listing_time):
    """生成交易信号"""
    
    score = calculate_opportunity_score(symbol)
    
    signal = {
        'symbol': symbol,
        'pair': f"{symbol}USDT",
        'listing_time': listing_time,
        'score': score,
        'recommendation': '',
        'strategy': ''
    }
    
    if score >= 70:
        signal['recommendation'] = '🟢 高机会'
        signal['strategy'] = """
推荐策略：
1. 开盘前5分钟准备
2. 开盘后等3-5分钟
3. 分批买入（30% + 30% + 40%）
4. 止损 -15%，止盈 +30%
"""
    elif score >= 50:
        signal['recommendation'] = '🟡 中等机会'
        signal['strategy'] = """
推荐策略：
1. 开盘后观望10分钟
2. 根据走势决定
3. 仓位控制在50%以内
"""
    else:
        signal['recommendation'] = '🔴 低机会'
        signal['strategy'] = """
建议：不参与
风险大于收益
"""
    
    return signal

def monitor_loop(check_interval=300):
    """监控循环"""
    
    print("=" * 60)
    print("🚀 币安新币上市监控系统")
    print("=" * 60)
    print(f"检查间隔: {check_interval}秒")
    print("=" * 60)
    
    known_listings = set()
    
    while True:
        try:
            print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 检查新币公告...")
            
            announcements = get_binance_announcements()
            
            new_found = False
            for ann in announcements:
                symbol = parse_listing_info(ann['title'])
                
                if symbol and symbol not in known_listings:
                    known_listings.add(symbol)
                    new_found = True
                    
                    print("\n" + "🚨" * 30)
                    print(f"📢 发现新币上线公告!")
                    print(f"   币种: {symbol}")
                    print(f"   公告: {ann['title']}")
                    print(f"   链接: {ann['url']}")
                    print("🚨" * 30)
                    
                    # 生成交易信号
                    signal = generate_trading_signal(symbol, ann['releaseDate'])
                    print(f"\n📊 交易信号:")
                    print(f"   评分: {signal['score']}/100")
                    print(f"   建议: {signal['recommendation']}")
                    print(signal['strategy'])
                    
                    # 保存信号
                    with open(DATA_DIR / f"{symbol}_{datetime.now().strftime('%Y%m%d')}.json", 'w') as f:
                        json.dump(signal, f, indent=2)
            
            if not new_found:
                print("   无新币上线公告")
            
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            print("\n监控已停止")
            break
        except Exception as e:
            print(f"错误: {e}")
            time.sleep(60)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'check':
        # 单次检查
        announcements = get_binance_announcements()
        print("\n📢 近期公告:")
        for ann in announcements[:5]:
            symbol = parse_listing_info(ann['title'])
            print(f"   - {ann['title']}")
            if symbol:
                print(f"     币种: {symbol}")
    else:
        # 持续监控
        monitor_loop()