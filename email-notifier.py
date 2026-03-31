#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()
# =============================================================================
# 全球战情室 - 邮件通知系统
# 功能：监控所有信号并立即发送邮件到 19922307306@189.cn
# =============================================================================

import smtplib
import json
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# 邮件配置
EMAIL_CONFIG = {
    "smtp_server": "smtp.163.com",
    "smtp_port": 465,
    "sender_email": "pandac00@163.com", 
    "sender_password": os.getenv("SENDER_PASSWORD"),
    "receiver_email": "19922307306@189.cn"
}

def send_alert_email(alert_type, asset_data, signal_data):
    """
    发送警报邮件
    alert_type: 'crypto_30plus', 'stock_10plus', 'social_trend', 'new_listing'
    """
    try:
        # 创建邮件内容
        subject = f"【全球战情室】{get_alert_subject(alert_type, asset_data)}"
        body = create_alert_body(alert_type, asset_data, signal_data)
        
        # 创建邮件对象
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG["sender_email"]
        msg['To'] = EMAIL_CONFIG["receiver_email"] 
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        
        # 发送邮件
        server = smtplib.SMTP_SSL(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"])
        server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
        text = msg.as_string()
        server.sendmail(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["receiver_email"], text)
        server.quit()
        
        print(f"[{datetime.now()}] ✅ 邮件发送成功: {subject}")
        return True
        
    except Exception as e:
        print(f"[{datetime.now()}] ❌ 邮件发送失败: {str(e)}")
        return False

def get_alert_subject(alert_type, asset_data):
    """生成邮件主题"""
    if alert_type == "crypto_30plus":
        return f"🚨 加密货币暴涨暴跌警报: {asset_data.get('symbol', 'Unknown')} {asset_data.get('change_percent', 0):+.1f}%"
    elif alert_type == "stock_10plus":
        return f"📈 股票短期机会: {asset_data.get('symbol', 'Unknown')} 潜在{asset_data.get('potential_gain', 0):.1f}%收益"
    elif alert_type == "social_trend":
        return f"🔥 社交媒体热点: {asset_data.get('trending_topic', 'Unknown')} 关联代币"
    elif alert_type == "new_listing":
        return f"🆕 新股上市机会: {asset_data.get('stock_name', 'Unknown')}"
    else:
        return "🔔 全球战情室警报"

def create_alert_body(alert_type, asset_data, signal_data):
    """创建邮件正文"""
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
        <div style="background-color: white; padding: 20px; border-radius: 10px; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;">
                🌍 全球战情室实时警报
            </h2>
            
            <div style="margin: 20px 0;">
                <h3>📊 资产信息</h3>
                <ul style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
    """
    
    # 添加资产详细信息
    for key, value in asset_data.items():
        if key not in ['raw_data']:
            body += f"<li><strong>{key.replace('_', ' ').title()}:</strong> {value}</li>\n"
    
    body += """
                </ul>
            </div>
            
            <div style="margin: 20px 0;">
                <h3>🎯 交易信号</h3>
                <ul style="background-color: #e8f5e8; padding: 15px; border-radius: 5px;">
    """
    
    # 添加信号信息
    for key, value in signal_data.items():
        body += f"<li><strong>{key.replace('_', ' ').title()}:</strong> {value}</li>\n"
    
    body += f"""
                </ul>
            </div>
            
            <div style="margin: 20px 0; padding: 15px; background-color: #fff3cd; border-radius: 5px; border-left: 4px solid #ffc107;">
                <strong>⏰ 警报时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                <br><strong>📧 接收邮箱:</strong> {EMAIL_CONFIG['receiver_email']}
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                <p>全球战情室 - 24小时自动监控 | 紫微智控系统</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return body

def test_email_system():
    """测试邮件系统"""
    print("🧪 测试邮件通知系统...")
    
    test_asset = {
        "symbol": "BTC",
        "current_price": 50000,
        "change_percent": 35.5,
        "volume": "10B"
    }
    
    test_signal = {
        "signal_type": "BUY",
        "confidence": "HIGH",
        "target_price": 55000,
        "stop_loss": 45000
    }
    
    success = send_alert_email("crypto_30plus", test_asset, test_signal)
    if success:
        print("✅ 邮件系统测试通过！")
    else:
        print("❌ 邮件系统测试失败！")
    
    return success

if __name__ == "__main__":
    test_email_system()