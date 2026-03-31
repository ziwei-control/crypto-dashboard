#!/usr/bin/env python3
"""
早期币发现通知脚本
用于发送高潜力早期币提醒
"""

import json
import urllib.request
import urllib.error
import time
from datetime import datetime
import os
import sys

# 配置
DATA_DIR = '/home/admin/Ziwei/data'
ALERT_FILE = os.path.join(DATA_DIR, 'early_tokens_alerts.json')

def send_dingtalk_alert(message, webhook_url=None):
    """发送钉钉通知"""
    if not webhook_url:
        # 尝试从配置获取
        config_file = '/home/admin/Ziwei/config/trading_config.json'
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
            webhook_url = config.get('notifications', {}).get('dingtalk_webhook', '')
    
    if not webhook_url:
        print("❌ 未配置钉钉 Webhook")
        return False
    
    try:
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": "🚀 高潜力早期币发现",
                "text": message
            }
        }
        
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get('errcode') == 0:
                print("✅ 钉钉通知发送成功")
                return True
            else:
                print(f"❌ 钉钉通知失败: {result}")
                return False
                
    except Exception as e:
        print(f"❌ 发送钉钉通知出错: {e}")
        return False

def format_token_alert(token):
    """格式化代币信息为通知消息"""
    msg = f"""## 🚀 高潜力早期币发现

### {token['symbol']} - {token['name']}

**📅 时间信息**
- 创建时间: {token.get('birth_time', '未知')}
- 存活时间: {token.get('age_str', '未知')}

**💰 价格信息**
- 当前价格: ${token['price_usd']:.10f}
- 流动性: ${token['liquidity']:,.0f}
- 24h成交量: ${token['volume_24h']:,.0f}

**📈 涨跌幅**
- 1小时: {token['change_1h']:+.1f}%
- 6小时: {token['change_6h']:+.1f}%
- 24小时: {token['change_24h']:+.1f}%

**🔗 地址信息**
- 链: {token['chain']}
- 代币合约: `{token['token_address']}`
- 交易池: `{token['pair_address']}`

[点击查看详情]({token['url']})
"""
    return msg

def main():
    """主函数"""
    # 读取最新报告
    report_file = os.path.join(DATA_DIR, 'early_tokens_report.json')
    
    if not os.path.exists(report_file):
        print("❌ 未找到报告文件")
        return 1
    
    with open(report_file, 'r') as f:
        report = json.load(f)
    
    tokens = report.get('tokens', [])
    
    if not tokens:
        print("❌ 没有发现早期币")
        return 0
    
    # 发送每个代币的通知
    for token in tokens:
        msg = format_token_alert(token)
        send_dingtalk_alert(msg)
        time.sleep(1)  # 避免频率限制
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
