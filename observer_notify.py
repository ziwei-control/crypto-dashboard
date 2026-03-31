#!/usr/bin/env python3
# =============================================================================
# 观察者通知系统 - Observer Notification
# 功能：在需要人类决策时发送通知
# 使用：在需要人类审核的决策前调用
# =============================================================================

import json
from pathlib import Path
from datetime import datetime

Ziwei_DIR = Path("/home/admin/Ziwei")
NOTIFY_LOG = Ziwei_DIR / "data/logs/takeover/notifications.log"

def send_notify(message: str, level: str = "info", requires_action: bool = False):
    """发送通知"""
    
    timestamp = datetime.now().isoformat()
    notify_entry = {
        "timestamp": timestamp,
        "level": level,
        "message": message,
        "requires_action": requires_action,
        "status": "pending"
    }
    
    # 记录到日志
    NOTIFY_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(NOTIFY_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(notify_entry, ensure_ascii=False) + "\n")
    
    # 打印通知
    emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨", "success": "✅"}
    print(f"\n{emoji.get(level, '📢')} [{level.upper()}] {message}")
    
    if requires_action:
        print("   👉 需要人类决策，请等待确认...")
    
    return notify_entry

def request_approval(action_type: str, details: dict) -> dict:
    """请求人类批准"""
    
    message = f"需要批准：{action_type}"
    notify = send_notify(message, level="warning", requires_action=True)
    
    print(f"\n📋 操作详情:")
    for key, value in details.items():
        print(f"   {key}: {value}")
    
    print(f"\n请选择:")
    print("   [1] 批准执行")
    print("   [2] 拒绝")
    print("   [3] 修改后执行")
    
    # 在实际系统中，这里会等待用户输入
    # 现在只是记录请求
    notify["action_type"] = action_type
    notify["details"] = details
    notify["request_time"] = datetime.now().isoformat()
    
    return notify

def main():
    """测试通知系统"""
    print("=" * 70)
    print("🔔 观察者通知系统测试")
    print("=" * 70)
    
    # 测试普通通知
    send_notify("系统正常运行", level="info")
    
    # 测试警告通知
    send_notify("发现潜在问题，需要关注", level="warning")
    
    # 测试批准请求
    request_approval("交易操作", {
        "币种": "ETH",
        "操作": "买入",
        "金额": "$500",
        "理由": "技术面突破"
    })
    
    print("\n" + "=" * 70)
    print("✅ 通知系统测试完成")

if __name__ == "__main__":
    main()
