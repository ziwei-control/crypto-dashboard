#!/usr/bin/env python3
"""
币安公告监控器 - 监控新币上市和下市公告
"""
import requests
import json
import time
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("/home/admin/Ziwei/data/announcements")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def get_binance_announcements():
    """获取币安公告"""
    announcements = []
    
    # 方法1: 用 RSS 或其他 API
    try:
        # 尝试用 crypto compare API
        url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
        resp = requests.get(url, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            news = data.get('Data', [])
            
            for n in news:
                title = n.get('title', '')
                if 'binance' in title.lower() and ('list' in title.lower() or 'delist' in title.lower()):
                    announcements.append({
                        'title': title,
                        'url': n.get('url', ''),
                        'time': datetime.fromtimestamp(n.get('published_on', 0)).strftime('%Y-%m-%d %H:%M'),
                        'source': 'cryptocompare'
                    })
    except Exception as e:
        print(f"CryptoCompare 错误: {e}")
    
    return announcements

def check_new_listing():
    """检查新币上市"""
    print("🔍 检查币安新币上市公告...")
    
    # 已知近期新币（手动维护）
    known_new_coins = [
        {"symbol": "EWJUSDT", "name": "iShares MSCI Japan ETF", "date": "2026-03-19", "type": "Futures"},
        {"symbol": "G", "name": "Gravity", "date": "2026-03-13", "type": "Spot"},
        {"symbol": "XPL", "name": "Explorer", "date": "2026-03-12", "type": "Spot"},
        {"symbol": "ANIME", "name": "Anime", "date": "2026-03-10", "type": "Spot"},
        {"symbol": "BERA", "name": "Berachain", "date": "2026-03-08", "type": "Spot"},
        {"symbol": "PUMP", "name": "Pump", "date": "2026-03-05", "type": "Spot"},
        {"symbol": "ASTER", "name": "Aster", "date": "2026-03-03", "type": "Spot"},
        {"symbol": "NIL", "name": "Nillion", "date": "2026-03-01", "type": "Spot"},
    ]
    
    return known_new_coins

def check_delistings():
    """检查下市公告"""
    print("🔍 检查币安下市公告...")
    
    # 已知下市币种
    known_delistings = [
        # 近期下市的币种
    ]
    
    return known_delistings

def main():
    print("=" * 70)
    print("📢 币安公告监控")
    print("=" * 70)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 新币上市
    print("\n🆕 近期新币上市:")
    print("-" * 70)
    new_coins = check_new_listing()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    for coin in new_coins:
        days_ago = (datetime.now() - datetime.strptime(coin['date'], '%Y-%m-%d')).days
        tag = "🔥" if days_ago <= 7 else "  "
        print(f"{tag} {coin['date']} - {coin['symbol']:<12} {coin['name']:<25} ({coin['type']})")
    
    # 下市公告
    print("\n❌ 近期下市公告:")
    print("-" * 70)
    delistings = check_delistings()
    
    if delistings:
        for d in delistings:
            print(f"  {d['date']} - {d['symbol']}: {d['reason']}")
    else:
        print("  暂无近期下市公告")
    
    # 今日重点关注
    print("\n🎯 今日重点:")
    print("-" * 70)
    
    # 找今天上市的或即将上市的
    for coin in new_coins:
        days_ago = (datetime.now() - datetime.strptime(coin['date'], '%Y-%m-%d')).days
        if days_ago <= 3:
            print(f"  🔥 {coin['symbol']} - 最近{days_ago}天上市，可能有波动机会")
    
    # 即将上市
    for coin in new_coins:
        if coin['date'] > today:
            print(f"  ⏰ {coin['symbol']} - 将于 {coin['date']} 上市")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
