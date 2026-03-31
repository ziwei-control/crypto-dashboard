#!/usr/bin/env python3
"""
Alpha Hunter 邮件通知模块
发现高潜力币时发送邮件通知
"""

import subprocess
import json
from datetime import datetime

# 收件人邮箱
EMAIL_TO = "19922307306@189.cn"

def send_email(subject, body):
    """发送邮件"""
    try:
        # 使用 mail 命令发送
        cmd = f'echo "{body}" | mail -s "{subject}" {EMAIL_TO}'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ 邮件已发送到 {EMAIL_TO}")
            return True
        else:
            print(f"❌ 邮件发送失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 发送邮件出错: {e}")
        return False

def notify_gem_found(gem):
    """发现潜力股时发送通知"""
    subject = f"🚀 发现潜力股: {gem['symbol']} ({gem['chain_name']})"
    
    body = f"""
🎯 Alpha Hunter 发现高潜力早期币！

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 代币信息
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
币种: {gem['symbol']}
名称: {gem.get('name', '未知')}
链: {gem['chain_name']}

💰 价格信息
当前价格: ${gem['price']:.10f}
市值: ${gem['fdv']:,.0f}
流动性: ${gem['liquidity']:,.0f}

📈 潜力分析
涨到 $1 需要: {gem['potential_x']:,.0f} 倍
年龄: {gem['age_hours']:.1f} 小时
评分: {gem['gem_score']}/10

🔗 合约地址
{gem['address']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ 发现时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ 风险提示: 加密货币投资风险极高，请谨慎决策！
"""
    
    return send_email(subject, body)

def notify_multiple_gems(gems):
    """发现多个潜力股时发送汇总通知"""
    if not gems:
        return False
    
    subject = f"🚀 Alpha Hunter 发现 {len(gems)} 个潜力股！"
    
    body = f"""
🎯 Alpha Hunter 早期币发现报告

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 发现时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
发现数量: {len(gems)} 个潜力股
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
    
    for i, g in enumerate(gems[:5], 1):
        body += f"""
[{i}] {g['symbol']} ({g['chain_name']})
    价格: ${g['price']:.10f}
    潜力: {g['potential_x']:,.0f} 倍到 $1
    市值: ${g['fdv']:,.0f}
    流动性: ${g['liquidity']:,.0f}
    年龄: {g['age_hours']:.1f}h
    评分: {g['gem_score']}/10
    地址: {g['address']}

"""
    
    body += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 风险提示: 加密货币投资风险极高，请谨慎决策！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    return send_email(subject, body)

if __name__ == "__main__":
    # 测试
    test_gem = {
        'symbol': 'TEST',
        'name': 'Test Token',
        'chain_name': 'Solana',
        'price': 0.00000123,
        'fdv': 150000,
        'liquidity': 25000,
        'potential_x': 813008,
        'age_hours': 12.5,
        'gem_score': 8,
        'address': 'test123...'
    }
    notify_gem_found(test_gem)
