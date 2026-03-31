#!/usr/bin/env python3
import sys
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import os

def send_email(config_file):
    """从配置文件读取并发送邮件"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        to_email = config.get('to', '')
        subject = config.get('subject', '')
        body = config.get('body', '')

        # 从环境变量读取 SMTP 配置
        smtp_host = os.getenv('SMTP_HOST', 'smtp.qq.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USER', '')
        smtp_password = os.getenv('SMTP_PASSWORD', '')

        if not smtp_user or not smtp_password:
            print("⚠️ 未配置 SMTP 凭证，邮件未发送")
            return False

        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = Header(subject, 'utf-8')

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # 发送邮件
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        print(f"✅ 邮件已发送至: {to_email}")
        return True

    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 courier.py <config_file.json>")
        sys.exit(1)

    send_email(sys.argv[1])