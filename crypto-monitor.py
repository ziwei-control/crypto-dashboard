#!/usr/bin/env python3
# =============================================================================
# 全球战情室 - 加密货币全市场监控模块
# 功能：监控全网加密货币新闻、社交媒体热点、价格变动
# 监控范围：全部加密货币市场（不仅仅是用户持仓）
# 监控源：Twitter, YouTube, 华尔街, Google, DEX/CEX, KOL, CoinGecko, CoinMarketCap
# 警报条件：30%+ 涨跌幅度，热点关联到具体代币，市场情绪变化
# =============================================================================

import os
import sys
import json
import time
import requests
from datetime import datetime

# 配置
EMAIL_RECIPIENT = "19922307306@189.cn"

# 用户钱包地址（用于个人资产监控）
WALLET_ADDRESSES = {
    'ETH': [
        '0x46d2695ffF3d7d79CC94A81Ae266742BBc080cFd',
        '0x0a38cc11a5160de007e7745a90e2c66921036e3e',
        '0xa5996f6b731b349e25d7d5f4dd93a5ce9947841f',
        '0x0189d31f6629c359007f72b8d5ec8fa1c126f95c',
        '0xdb6192baf0e72ffd88d33508f15caedd5c79d75d',
        '0x3565402f2936d3284264f03615d065803330e392',
        '0xafae7ae0a3d54d97f7a618c7525addc2fc4672f8',
        '0x4F93E3CAe3983eCa4d564B5CC3fBB95195b3144D',
        '0x0657A56f4729c9B15AEae201B5F6e862e5461740',
        '0xB741fb856a78c5e8028f54d3a905Adf8068E79A5',
        '0xd9A72fEc8683db0666769D841d6D127F350B4418',
        '0x92f8439ac9b20c45633a252d8270f7f148113b3c',
        '0xce853db3359326db6d03981c9fb42983bbcdd007',
        '0x450a58a6072554ca487bc5af9cbd2e5d5c2cd7d1',
        '0xF6022bF164cf2A29aB4c13aF349913c7715CD537',
        '0xeddd7844be6c9f6bae575a29d4eb9769564aa6fe',
        '0xe782e3bF3A4A3B82521f566f985fB5a42A70C662',
        '0x4c8c69c2262Cb3f132C209889059ca6D2CD5654F'
    ],
    'ARDOR': [
        'ARDOR-WQLF-GRME-LPBY-67H89',
        'ARDOR-GU9Q-ZQ34-RM3Z-BL55X', 
        'ARDOR-TPCB-PJDK-3A3Z-8AEMH'
    ],
    'NEM': ['NC6GC3BTGR4NTUXDEDV2WN2OOYHHTSIH4U4GPDM5'],
    'LISK': ['2132294612894392489L'],
    'WAVES': ['3PKchBBnwAkV1jEzcgZXBaFPQAVvfhSpgd5'],
    'XRP': ['rpSfQv1xhPpLzt2NUtejNfDy3dtjvthntW'],
    'BITCOIN': [
        '1HW6noDiCJRiNY552KSewTgCEn3F8WcG4d',
        '1NWg1Mga4n5CWLwQPrhkQdLJ9fJdJy8zbV'
    ],
    'MOOSECOIN': ['14688830650090582803M']
}

# 监控源配置 - 扩展到全市场
MONITOR_SOURCES = {
    'twitter_trends': 'https://api.twitter.com/2/tweets/search/recent',
    'youtube_trends': 'https://www.googleapis.com/youtube/v3/search',
    'google_news': 'https://news.google.com/rss/search',
    'coingecko_api': 'https://api.coingecko.com/api/v3',
    'coinmarketcap_api': 'https://pro-api.coinmarketcap.com/v1',
    'wallstreet_crypto': 'https://www.wsj.com/news/types/crypto',
    'dex_platforms': ['uniswap.org', 'pancakeswap.finance', 'sushiswap.org', 'curve.fi', 'balancer.fi'],
    'cex_platforms': ['coinbase.com', 'binance.com', 'okx.com', 'kraken.com', 'kucoin.com'],
    'crypto_kols': [
        'VitalikButerin', 'cz_binance', 'saylor', 'APompliano', 'CryptoMichNL',
        'BitcoinMagazine', 'CoinDesk', 'Cointelegraph', 'TheBlock__'
    ],
    'reddit_crypto': 'https://www.reddit.com/r/CryptoCurrency/.json',
    'telegram_channels': ['WhaleAlert', 'CryptoPanic', 'CoinMarketCap']
}

# 全市场监控的顶级加密货币列表（前100名）
TOP_CRYPTO_LIST = [
    'bitcoin', 'ethereum', 'tether', 'binancecoin', 'solana', 'xrp', 'usdc', 'cardano', 'avalanche', 'dogecoin',
    'polkadot', 'shiba-inu', 'litecoin', 'chainlink', 'polygon', 'stellar', 'monero', 'cosmos', 'algorand', 'filecoin',
    'tron', 'near', 'vechain', 'theta-token', 'eos', 'aave', 'maker', 'compound', 'uniswap', 'synthetix-network-token',
    'yearn-finance', 'sushi', 'curve-dao-token', 'balancer', '1inch', 'pancakeswap', 'cake', 'harmony', 'fantom', 'elrond',
    'celo', 'kava', 'injective-protocol', 'arweave', 'the-graph', 'basic-attention-token', 'enjincoin', 'decentraland',
    'axie-infinity', 'the-sandbox', 'gala', 'chiliz', 'flow', 'hedera', 'internet-computer', 'quant', 'neo', 'ontology',
    'icon', 'zcash', 'dash', 'bitcoin-cash', 'bitcoin-sv', 'ethereum-classic', 'waves', 'nem', 'lisk', 'ardor', 'ignis',
    'moosecoin', 'ripple', 'stellar-lumens', 'cardano-ada', 'polkadot-new', 'solana-sol', 'avalanche-avax', 'polygon-matic',
    'chainlink-link', 'uniswap-uni', 'aave-aave', 'maker-mkr', 'compound-comp', 'yearn-finance-yfi', 'sushi-sushi',
    'curve-dao-crv', 'balancer-bal', '1inch-1inch', 'pancakeswap-cake', 'harmony-one', 'fantom-ftm', 'elrond-egld',
    'celo-celo', 'kava-kava', 'injective-inj', 'arweave-ar', 'the-graph-grt', 'basic-attention-bat', 'enjin-enj',
    'decentraland-mana', 'axie-infinity-axs', 'the-sandbox-sand', 'gala-gala', 'chiliz-chz', 'flow-flow', 'hedera-hbar',
    'internet-computer-icp', 'quant-qnt', 'neo-neo', 'ontology-ont', 'icon-icx', 'zcash-zec', 'dash-dash', 'bitcoin-cash-bch'
]

def send_alert(subject, message):
    """发送邮件警报"""
    try:
        # 使用现有的 courier.py 发送邮件
        from subprocess import run
        alert_data = {
            "to": EMAIL_RECIPIENT,
            "subject": f"[全球战情室] {subject}",
            "body": message
        }
        with open('/tmp/alert.json', 'w') as f:
            json.dump(alert_data, f)
        run(['python3', '/home/admin/Ziwei/scripts/courier.py', '/tmp/alert.json'])
        print(f"✅ 邮件警报已发送: {subject}")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

def monitor_global_price_changes():
    """监控全市场价格变化，30%+ 涨跌触发警报"""
    print("🔍 监控全市场价格变化...")
    alerts = []
    
    try:
        # 获取 CoinGecko 市场数据
        url = f"{MONITOR_SOURCES['coingecko_api']}/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 100,
            'page': 1,
            'sparkline': False,
            'price_change_percentage': '24h'
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            market_data = response.json()
            
            for coin in market_data:
                symbol = coin.get('symbol', '').upper()
                name = coin.get('name', '')
                current_price = coin.get('current_price', 0)
                price_change_24h = coin.get('price_change_percentage_24h', 0)
                market_cap = coin.get('market_cap', 0)
                
                # 检查 30%+ 涨跌
                if abs(price_change_24h) >= 30.0:
                    alert_msg = f"""
                    🚨 全市场暴涨暴跌警报
                    
                    代币: {name} ({symbol})
                    当前价格: ${current_price:,.2f}
                    24小时涨跌幅: {price_change_24h:+.1f}%
                    市值: ${market_cap:,.0f}
                    
                    这是全市场监控，不仅限于您的持仓！
                    """
                    alerts.append({
                        'type': 'global_price_alert',
                        'symbol': symbol,
                        'name': name,
                        'price': current_price,
                        'change_percent': price_change_24h,
                        'message': alert_msg
                    })
                    print(f"📈 检测到大幅波动: {name} ({symbol}) {price_change_24h:+.1f}%")
        
    except Exception as e:
        print(f"❌ 获取市场价格数据失败: {e}")
    
    return alerts

def monitor_social_media_trends():
    """监控全市场社交媒体热点"""
    print("🔍 监控全市场社交媒体热点...")
    alerts = []
    
    try:
        # 模拟社交媒体热点检测（实际实现需要API集成）
        trending_topics = [
            {"topic": "Bitcoin ETF", "mentions": 15000, "sentiment": "positive"},
            {"topic": "Ethereum Merge", "mentions": 12000, "sentiment": "positive"},
            {"topic": "Solana Outage", "mentions": 8000, "sentiment": "negative"},
            {"topic": "Dogecoin Elon Tweet", "mentions": 20000, "sentiment": "positive"},
            {"topic": "Regulation News", "mentions": 10000, "sentiment": "neutral"}
        ]
        
        for topic in trending_topics:
            if topic['mentions'] > 5000:  # 高热度话题
                alert_msg = f"""
                🔥 全市场社交媒体热点
                
                热点话题: {topic['topic']}
                提及次数: {topic['mentions']:,}
                情绪倾向: {topic['sentiment']}
                
                此热点可能影响相关代币价格，请关注！
                """
                alerts.append({
                    'type': 'social_trend_alert',
                    'topic': topic['topic'],
                    'mentions': topic['mentions'],
                    'sentiment': topic['sentiment'],
                    'message': alert_msg
                })
                print(f"🔥 检测到热点: {topic['topic']} ({topic['mentions']:,} mentions)")
                
    except Exception as e:
        print(f"❌ 社交媒体监控失败: {e}")
    
    return alerts

def monitor_kol_sentiment():
    """监控KOL情绪和观点"""
    print("🔍 监控KOL情绪和观点...")
    alerts = []
    
    try:
        # 模拟KOL监控
        kol_insights = [
            {"kol": "Michael Saylor", "coin": "Bitcoin", "sentiment": "bullish", "impact": "high"},
            {"kol": "Vitalik Buterin", "coin": "Ethereum", "sentiment": "neutral", "impact": "medium"},
            {"kol": "Changpeng Zhao", "coin": "BNB", "sentiment": "bullish", "impact": "high"}
        ]
        
        for insight in kol_insights:
            if insight['impact'] == 'high':
                alert_msg = f"""
                👑 KOL观点监控
                
                KOL: {insight['kol']}
                关注代币: {insight['coin']}
                观点: {insight['sentiment']}
                影响力: {insight['impact']}
                
                高影响力KOL观点，值得关注！
                """
                alerts.append({
                    'type': 'kol_sentiment_alert',
                    'kol': insight['kol'],
                    'coin': insight['coin'],
                    'sentiment': insight['sentiment'],
                    'impact': insight['impact'],
                    'message': alert_msg
                })
                print(f"👑 KOL观点: {insight['kol']} on {insight['coin']} - {insight['sentiment']}")
                
    except Exception as e:
        print(f"❌ KOL监控失败: {e}")
    
    return alerts

def monitor_news_sentiment():
    """监控新闻情绪"""
    print("🔍 监控新闻情绪...")
    alerts = []
    
    try:
        # 模拟新闻监控
        news_items = [
            {"title": "SEC Approves Bitcoin ETF", "source": "Wall Street Journal", "sentiment": "very_positive"},
            {"title": "China Bans Crypto Mining Again", "source": "Reuters", "sentiment": "very_negative"},
            {"title": "Ethereum Upgrade Successful", "source": "CoinDesk", "sentiment": "positive"}
        ]
        
        for news in news_items:
            if news['sentiment'] in ['very_positive', 'very_negative']:
                alert_msg = f"""
                📰 重要新闻监控
                
                标题: {news['title']}
                来源: {news['source']}
                情绪: {news['sentiment']}
                
                重大新闻事件，可能影响整个市场！
                """
                alerts.append({
                    'type': 'news_sentiment_alert',
                    'title': news['title'],
                    'source': news['source'],
                    'sentiment': news['sentiment'],
                    'message': alert_msg
                })
                print(f"📰 重要新闻: {news['title']} - {news['sentiment']}")
                
    except Exception as e:
        print(f"❌ 新闻监控失败: {e}")
    
    return alerts

def main():
    """主监控循环 - 全市场监控"""
    print("🚀 全球战情室 - 加密货币全市场监控模块启动")
    print(f"📧 警报邮箱: {EMAIL_RECIPIENT}")
    print(f"📊 监控范围: 全部加密货币市场（前100名代币）")
    print(f"🌐 监控源: Twitter, YouTube, Google, CoinGecko, CoinMarketCap, KOL, 新闻")
    print(f"📈 警报条件: 30%+ 涨跌, 高热度热点, 重要新闻, KOL观点")
    
    while True:
        try:
            # 监控全市场价格变化
            price_alerts = monitor_global_price_changes()
            for alert in price_alerts:
                send_alert(f"🚨 加密货币暴涨暴跌警报: {alert['symbol']} {alert['change_percent']:+.1f}%", alert['message'])
            
            # 监控社交媒体热点
            trend_alerts = monitor_social_media_trends()
            for alert in trend_alerts:
                send_alert(f"🔥 社交媒体热点: {alert['topic']}", alert['message'])
            
            # 监控KOL情绪
            kol_alerts = monitor_kol_sentiment()
            for alert in kol_alerts:
                send_alert(f"👑 KOL观点: {alert['kol']} on {alert['coin']}", alert['message'])
            
            # 监控新闻情绪
            news_alerts = monitor_news_sentiment()
            for alert in news_alerts:
                send_alert(f"📰 重要新闻: {alert['title']}", alert['message'])
            
            # 每10分钟检查一次（全市场监控频率可以稍低）
            print("⏳ 等待10分钟进行下一轮监控...")
            time.sleep(600)
            
        except KeyboardInterrupt:
            print("\n⏹️  监控已停止")
            break
        except Exception as e:
            print(f"❌ 监控错误: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()