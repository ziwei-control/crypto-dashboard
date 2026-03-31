#!/usr/bin/env python3
"""
早期币自动通知系统 v2.0
- 扫描Alpha Hunter报告，发现新币自动推送钉钉
- 补全boosted代币信息
- 包含：出生时间、存活时间、交易地址、合约地址
"""

import json
import urllib.request
import urllib.error
import os
import sys
from datetime import datetime, timedelta

# 配置
DATA_DIR = '/home/admin/Ziwei/data'
ALPHA_HUNTER_DIR = '/home/admin/Ziwei/data/alpha_hunter'
CONFIG_FILE = '/home/admin/Ziwei/config/trading_config.json'
SENT_FILE = '/home/admin/Ziwei/data/sent_tokens.json'
DEXSCREENER_API = 'https://api.dexscreener.com/latest/dex/tokens/'

def get_webhook():
    """获取钉钉Webhook"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return config.get('notifications', {}).get('dingtalk_webhook', '')
    return ''

def send_dingtalk(message, webhook=None):
    """发送钉钉通知"""
    if not webhook:
        webhook = get_webhook()
    if not webhook:
        print("❌ 未配置钉钉Webhook")
        return False
    
    try:
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": "🚀 早期币发现",
                "text": message
            }
        }
        
        req = urllib.request.Request(
            webhook,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            if result.get('errcode') == 0:
                print("✅ 钉钉通知发送成功")
                return True
            else:
                print(f"❌ 钉钉通知失败: {result}")
                return False
    except Exception as e:
        print(f"❌ 发送出错: {e}")
        return False

def get_token_info_from_dexscreener(address):
    """从DexScreener获取代币完整信息"""
    try:
        url = f"{DEXSCREENER_API}{address}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        
        pairs = data.get('pairs', [])
        if not pairs:
            return None
        
        # 取流动性最高的pair
        best_pair = max(pairs, key=lambda p: p.get('liquidity', {}).get('usd', 0))
        
        return {
            'symbol': best_pair.get('baseToken', {}).get('symbol', 'Unknown'),
            'name': best_pair.get('baseToken', {}).get('name', 'Unknown'),
            'price': float(best_pair.get('priceUsd', 0)),
            'liquidity': best_pair.get('liquidity', {}).get('usd', 0),
            'volume_24h': best_pair.get('volume', {}).get('h24', 0),
            'price_change_24h': best_pair.get('priceChange', {}).get('h24', 0),
            'pair_address': best_pair.get('pairAddress', ''),
            'token_address': best_pair.get('baseToken', {}).get('address', address),
            'chain': best_pair.get('chainId', 'unknown'),
            'created_at': best_pair.get('pairCreatedAt', 0),
            'url': f"https://dexscreener.com/{best_pair.get('chainId', 'solana')}/{best_pair.get('pairAddress', '')}"
        }
    except Exception as e:
        print(f"获取代币信息失败 {address}: {e}")
        return None

def load_sent_tokens():
    """加载已发送的代币列表"""
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_sent_tokens(sent):
    """保存已发送的代币列表"""
    with open(SENT_FILE, 'w') as f:
        json.dump(sent, f, indent=2)

def format_age(hours):
    """格式化存活时间"""
    if hours < 1:
        return f"{int(hours * 60)}分钟"
    elif hours < 24:
        return f"{hours:.1f}小时"
    else:
        return f"{hours/24:.1f}天"

def format_timestamp(ts):
    """格式化时间戳"""
    if not ts:
        return "未知"
    dt = datetime.fromtimestamp(ts / 1000)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def format_token_alert(token, extra_info=None):
    """格式化代币通知 - 包含完整信息"""
    
    # 链标识
    chain_emoji = {
        'solana': '🌞',
        'base': '🔵',
        'ethereum': '💎',
        'bsc': '🟡',
        'polygon': '🟣'
    }
    chain = token.get('chain', 'unknown').lower()
    emoji = chain_emoji.get(chain, '🌐')
    
    # 基本信息
    symbol = token.get('symbol', 'Unknown')
    name = token.get('name', symbol)
    price = token.get('price', 0)
    liquidity = token.get('liquidity', 0)
    volume = token.get('volume_24h', 0)
    change_24h = token.get('price_change_24h', 0)
    
    # 地址信息
    token_address = token.get('token_address', token.get('address', ''))
    pair_address = token.get('pair_address', '')
    
    # 时间信息
    created_at = token.get('created_at', 0)
    if created_at:
        birth_time = format_timestamp(created_at)
        age_hours = (datetime.now().timestamp() - created_at / 1000) / 3600
        age_str = format_age(age_hours)
    else:
        age_hours = token.get('age_hours', 0)
        birth_time = token.get('birth_time', '未知')
        age_str = format_age(age_hours)
    
    # 新币标记
    new_badge = "🆕 **新币 (<24h)**" if age_hours < 24 else ""
    
    # 推广标记
    boost_badge = ""
    if extra_info and extra_info.get('boost_amount'):
        boost_badge = f"💰 推广: ${extra_info['boost_amount']}"
    
    # 链接
    url = token.get('url', f"https://dexscreener.com/{chain}/{pair_address}")
    
    msg = f"""## 🚀 早期币发现：{symbol}

### {emoji} {name}

**📅 时间信息**
- 出生时间: {birth_time}
- 存活时间: {age_str}
{new_badge}

**💰 价格数据**
- 当前价格: ${price:.10f}
- 流动性: ${liquidity:,.0f}
- 24h成交量: ${volume:,.0f}

**📈 涨跌幅**
- 24小时: **{change_24h:+.1f}%**

**🔗 地址信息**
- 合约地址: `{token_address}`
- 交易地址: `{pair_address}`
- [查看DexScreener]({url})

{boost_badge}

**⚠️ 风险提示**
- 新币风险高，可能归零
- 建议小额试探，严格止损

**📌 关键词**: 早期
"""
    return msg

def scan_and_notify():
    """扫描报告并发送通知"""
    webhook = get_webhook()
    if not webhook:
        print("❌ 未配置Webhook，退出")
        return 1
    
    sent = load_sent_tokens()
    sent_count = 0
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 扫描最新的Alpha Hunter报告
    report_files = sorted(
        [f for f in os.listdir(ALPHA_HUNTER_DIR) if f.startswith('report_') and f.endswith('.json')],
        reverse=True
    )[:1]  # 只检查最新报告
    
    for report_file in report_files:
        filepath = os.path.join(ALPHA_HUNTER_DIR, report_file)
        with open(filepath, 'r') as f:
            report = json.load(f)
        
        # ========== 1. 处理新币 (tokens) ==========
        tokens = report.get('tokens', [])
        for token in tokens:
            address = token.get('address', '')
            symbol = token.get('symbol', '')
            
            # 只通知新币 (age < 24h)
            age = token.get('age_hours', 999)
            if age >= 24:
                continue
            
            # 检查是否已发送
            key = f"{today}_{address}"
            if key in sent:
                continue
            
            # 检查流动性
            liquidity = token.get('liquidity', 0)
            if liquidity < 10000:
                continue
            
            # 补全信息
            if not token.get('pair_address'):
                info = get_token_info_from_dexscreener(address)
                if info:
                    token.update(info)
            
            # 发送通知
            msg = format_token_alert(token)
            if send_dingtalk(msg, webhook):
                sent[key] = {
                    'symbol': symbol,
                    'address': address,
                    'sent_at': datetime.now().isoformat(),
                    'price': token.get('price'),
                    'liquidity': liquidity
                }
                sent_count += 1
        
        # ========== 2. 处理推广代币 (boosted) ==========
        boosted = report.get('boosted', [])
        for token in boosted[:5]:  # 只处理前5个高推广
            address = token.get('address', '')
            boost_amount = token.get('boost_amount', 0)
            
            # 只通知高推广 ($200+)
            if boost_amount < 200:
                continue
            
            # 检查是否已发送
            key = f"boosted_{today}_{address}"
            if key in sent:
                continue
            
            # 从DexScreener获取完整信息
            info = get_token_info_from_dexscreener(address)
            if not info:
                print(f"⚠️ 无法获取 {address} 信息，跳过")
                continue
            
            # 检查流动性
            if info.get('liquidity', 0) < 10000:
                continue
            
            # 发送通知
            msg = format_token_alert(info, {'boost_amount': boost_amount})
            if send_dingtalk(msg, webhook):
                sent[key] = {
                    'symbol': info.get('symbol', 'Unknown'),
                    'address': address,
                    'sent_at': datetime.now().isoformat(),
                    'boost_amount': boost_amount,
                    'price': info.get('price'),
                    'liquidity': info.get('liquidity')
                }
                sent_count += 1
    
    # 保存发送记录
    if sent_count > 0:
        # 清理7天前的记录
        cutoff = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        sent = {k: v for k, v in sent.items() if k[:10] > cutoff}
        save_sent_tokens(sent)
        print(f"✅ 发送了 {sent_count} 条通知")
    else:
        print("ℹ️ 没有新的早期币需要通知")
    
    return 0

def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description='早期币自动通知系统 v2.0')
    parser.add_argument('--run', action='store_true', help='运行扫描并发送通知')
    parser.add_argument('--test', action='store_true', help='发送测试通知')
    parser.add_argument('--status', action='store_true', help='查看状态')
    parser.add_argument('--clear', action='store_true', help='清除发送记录（测试用）')
    args = parser.parse_args()
    
    if args.test:
        msg = """## 🔔 早期币发现系统测试

**✅ 系统状态**
- Alpha Hunter: 运行中
- 钉钉通知: 已配置
- 扫描频率: 每10分钟

**🎯 监控条件**
- 新币年龄: < 24小时
- 最小流动性: $10,000
- 高推广金额: $200+

**📋 通知内容**
- 出生时间 ✓
- 存活时间 ✓
- 合约地址 ✓
- 交易地址 ✓

**📌 关键词**: 早期
"""
        send_dingtalk(msg)
        return 0
    
    if args.status:
        sent = load_sent_tokens()
        today = datetime.now().strftime('%Y-%m-%d')
        today_count = len([k for k in sent.keys() if k.startswith(today)])
        print(f"📊 状态:")
        print(f"  - 今日已发送: {today_count} 条")
        print(f"  - 历史记录: {len(sent)} 条")
        return 0
    
    if args.clear:
        if os.path.exists(SENT_FILE):
            os.remove(SENT_FILE)
            print("✅ 发送记录已清除")
        return 0
    
    return scan_and_notify()

if __name__ == '__main__':
    sys.exit(main())