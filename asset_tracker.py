#!/usr/bin/env python3
# =============================================================================
# 📊 资产跟踪与报告系统
# 实时追踪资产变化，定期报告盈亏
# =============================================================================

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import subprocess

# =============================================================================
# 配置
# =============================================================================

BASE_DIR = Path("/home/admin/Ziwei")
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = DATA_DIR / "reports"
ASSETS_FILE = DATA_DIR / "assets" / "portfolio.json"
TRADES_FILE = DATA_DIR / "assets" / "trades.json"
DAILY_REPORT_FILE = DATA_DIR / "assets" / "daily_reports.json"

# 报告配置
REPORT_CONFIG = {
    # 报告时间
    "morning_report_time": "08:00",     # 早报时间
    "evening_report_time": "22:00",     # 晚报时间
    "instant_alert_threshold": 10,      # 即时预警阈值（%变化）
    
    # 报告内容
    "include_pending_trades": True,     # 包含待确认交易
    "include_opportunities": True,      # 包含发现的机会
    "include_risk_assessment": True,    # 包含风险评估
    
    # 通知方式
    "notification_methods": ["dingtalk", "email"],
    "dingtalk_webhook": "",  # 钉钉机器人
    "email_recipient": "19922307306@189.cn",
}


# =============================================================================
# 数据结构
# =============================================================================

@dataclass
class AssetSnapshot:
    """资产快照"""
    timestamp: str
    total_value_usd: float
    cash_usd: float
    positions: Dict[str, Dict]  # {symbol: {amount, value, pnl}}
    daily_pnl_usd: float
    daily_pnl_percent: float
    total_pnl_usd: float
    total_pnl_percent: float


@dataclass
class Trade:
    """交易记录"""
    id: str
    timestamp: str
    type: str  # buy, sell
    symbol: str
    amount: float
    price: float
    total_usd: float
    status: str  # pending, confirmed, executed, cancelled
    pnl_usd: Optional[float] = None
    notes: str = ""


@dataclass
class DailyReport:
    """日报"""
    date: str
    morning_snapshot: Optional[Dict]
    evening_snapshot: Optional[Dict]
    trades: List[Dict]
    total_pnl_usd: float
    total_pnl_percent: float
    opportunities: List[Dict]
    alerts: List[Dict]


# =============================================================================
# 资产跟踪器
# =============================================================================

class AssetTracker:
    """资产跟踪器"""
    
    def __init__(self):
        self.ensure_dirs()
        self.load_data()
        self.log("📊 资产跟踪器初始化")
    
    def ensure_dirs(self):
        for d in [REPORTS_DIR, DATA_DIR / "assets"]:
            d.mkdir(parents=True, exist_ok=True)
    
    def load_data(self):
        self.portfolio = self.load_json(ASSETS_FILE, {
            "initial_value_usd": 60,  # 初始资金
            "current_value_usd": 60,
            "cash_usd": 60,
            "positions": {},
            "trades_count": 0,
            "win_count": 0,
            "loss_count": 0,
            "total_pnl_usd": 0,
            "created": datetime.now().isoformat()
        })
        
        self.trades = self.load_json(TRADES_FILE, [])
        self.daily_reports = self.load_json(DAILY_REPORT_FILE, [])
    
    def load_json(self, path: Path, default=None):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default if default else {}
    
    def save_json(self, path: Path, data):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    def log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {msg}")
    
    def get_current_portfolio(self) -> AssetSnapshot:
        """获取当前资产快照"""
        # 这里应该从交易所获取实际数据
        # 模拟数据
        return AssetSnapshot(
            timestamp=datetime.now().isoformat(),
            total_value_usd=self.portfolio["current_value_usd"],
            cash_usd=self.portfolio["cash_usd"],
            positions=self.portfolio["positions"],
            daily_pnl_usd=0,  # 需要计算
            daily_pnl_percent=0,
            total_pnl_usd=self.portfolio["total_pnl_usd"],
            total_pnl_percent=self.portfolio["total_pnl_usd"] / self.portfolio["initial_value_usd"] * 100
        )
    
    def record_trade(self, trade_type: str, symbol: str, amount: float, 
                     price: float, status: str = "pending") -> Trade:
        """记录交易"""
        import hashlib
        import time
        
        trade = Trade(
            id=f"trade_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}",
            timestamp=datetime.now().isoformat(),
            type=trade_type,
            symbol=symbol,
            amount=amount,
            price=price,
            total_usd=amount * price,
            status=status
        )
        
        self.trades.append(asdict(trade))
        self.save_json(TRADES_FILE, self.trades)
        
        return trade
    
    def generate_morning_report(self) -> str:
        """生成早报"""
        snapshot = self.get_current_portfolio()
        
        report = f"""
🌅 早报 - {datetime.now().strftime('%Y-%m-%d %H:%M')}

💰 资产概况
├── 总资产: ${snapshot.total_value_usd:.2f}
├── 可用现金: ${snapshot.cash_usd:.2f}
├── 持仓数量: {len(snapshot.positions)}
└── 总盈亏: ${snapshot.total_pnl_usd:.2f} ({snapshot.total_pnl_percent:+.1f}%)

📊 待处理事项
├── 待确认交易: {len([t for t in self.trades if t['status'] == 'pending'])}
└── 今日机会: 发现中...

⚡ 建议
- 继续观望，等待最佳入场时机
- 关注早期币挖掘结果
"""
        return report
    
    def generate_evening_report(self) -> str:
        """生成晚报"""
        snapshot = self.get_current_portfolio()
        
        today_trades = [t for t in self.trades 
                       if t['timestamp'].startswith(datetime.now().strftime('%Y-%m-%d'))]
        
        report = f"""
🌙 晚报 - {datetime.now().strftime('%Y-%m-%d %H:%M')}

💰 今日总结
├── 资产变化: ${snapshot.daily_pnl_usd:+.2f} ({snapshot.daily_pnl_percent:+.1f}%)
├── 总资产: ${snapshot.total_value_usd:.2f}
└── 总盈亏: ${snapshot.total_pnl_usd:.2f} ({snapshot.total_pnl_percent:+.1f}%)

📈 今日交易
├── 交易次数: {len(today_trades)}
├── 成功: {len([t for t in today_trades if t.get('pnl_usd', 0) > 0])}
└── 失败: {len([t for t in today_trades if t.get('pnl_usd', 0) < 0])}

🎯 明日计划
- 继续监控早期币机会
- 等待系统进化结果
"""
        return report
    
    def generate_instant_alert(self, alert_type: str, message: str, data: Dict = None) -> str:
        """生成即时预警"""
        alert = f"""
⚠️ 即时预警 - {datetime.now().strftime('%H:%M:%S')}

类型: {alert_type}
消息: {message}
"""
        if data:
            alert += f"\n详情: {json.dumps(data, ensure_ascii=False)}"
        
        return alert


# =============================================================================
# 交易确认系统
# =============================================================================

class TradeConfirmation:
    """交易确认系统"""
    
    def __init__(self, asset_tracker: AssetTracker):
        self.tracker = asset_tracker
        self.pending_confirmations = []
        self.load_pending()
    
    def load_pending(self):
        """加载待确认交易"""
        for trade in self.tracker.trades:
            if trade['status'] == 'pending':
                self.pending_confirmations.append(trade)
    
    def create_confirmation_request(self, trade: Trade, reason: str) -> Dict:
        """创建确认请求"""
        request = {
            "id": trade.id,
            "timestamp": datetime.now().isoformat(),
            "trade": asdict(trade),
            "reason": reason,
            "status": "waiting",
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            "confirmation_methods": {
                "dingtalk": "回复 '确认 {trade.id}' 或 '取消 {trade.id}'",
                "email": "回复邮件确认或取消",
                "direct": "运行命令确认"
            }
        }
        
        return request
    
    def generate_confirmation_message(self, request: Dict) -> str:
        """生成确认消息"""
        trade = request['trade']
        
        message = f"""
🔔 交易确认请求

📋 交易详情:
├── 类型: {trade['type'].upper()}
├── 币种: {trade['symbol']}
├── 数量: {trade['amount']}
├── 价格: ${trade['price']:.4f}
└── 总额: ${trade['total_usd']:.2f}

📝 原因: {request['reason']}

⏰ 有效期: 24小时内

✅ 确认方式:
1. 钉钉回复: "确认 {trade['id']}"
2. 钉钉回复: "取消 {trade['id']}"
3. 命令确认:
   python3 scripts/asset_tracker.py --confirm {trade['id']}
   python3 scripts/asset_tracker.py --cancel {trade['id']}
"""
        return message
    
    def confirm_trade(self, trade_id: str) -> bool:
        """确认交易"""
        for trade in self.tracker.trades:
            if trade['id'] == trade_id and trade['status'] == 'pending':
                trade['status'] = 'confirmed'
                self.tracker.save_json(TRADES_FILE, self.tracker.trades)
                self.log(f"✅ 交易已确认: {trade_id}")
                return True
        return False
    
    def cancel_trade(self, trade_id: str) -> bool:
        """取消交易"""
        for trade in self.tracker.trades:
            if trade['id'] == trade_id and trade['status'] == 'pending':
                trade['status'] = 'cancelled'
                self.tracker.save_json(TRADES_FILE, self.tracker.trades)
                self.log(f"❌ 交易已取消: {trade_id}")
                return True
        return False
    
    def log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {msg}")


# =============================================================================
# 通知系统
# =============================================================================

class NotificationSystem:
    """通知系统"""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def send_dingtalk(self, message: str) -> bool:
        """发送钉钉通知"""
        webhook = self.config.get("dingtalk_webhook", "")
        if not webhook:
            print("⚠️ 钉钉Webhook未配置")
            return False
        
        try:
            import requests
            response = requests.post(
                webhook,
                json={"msgtype": "text", "text": {"content": message}},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 钉钉通知失败: {e}")
            return False
    
    def send_email(self, subject: str, body: str) -> bool:
        """发送邮件通知"""
        recipient = self.config.get("email_recipient", "")
        if not recipient:
            print("⚠️ 邮件收件人未配置")
            return False
        
        try:
            # 使用现有的邮件发送脚本
            subprocess.run([
                "python3", "/root/.copaw/bin/send_email.py",
                "--to", recipient,
                "--subject", subject,
                "--body", body
            ], timeout=30)
            return True
        except Exception as e:
            print(f"❌ 邮件通知失败: {e}")
            return False
    
    def notify(self, message: str, methods: List[str] = None, 
               subject: str = "CoPaw 通知") -> Dict:
        """发送通知"""
        if methods is None:
            methods = self.config.get("notification_methods", ["email"])
        
        results = {}
        
        if "dingtalk" in methods:
            results["dingtalk"] = self.send_dingtalk(message)
        
        if "email" in methods:
            results["email"] = self.send_email(subject, message)
        
        return results


# =============================================================================
# 报告调度器
# =============================================================================

class ReportScheduler:
    """报告调度器"""
    
    def __init__(self):
        self.tracker = AssetTracker()
        self.confirmation = TradeConfirmation(self.tracker)
        self.notifier = NotificationSystem(REPORT_CONFIG)
        self.last_morning = None
        self.last_evening = None
    
    def check_and_send_reports(self):
        """检查并发送报告"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_date = now.strftime("%Y-%m-%d")
        
        # 早报
        morning_time = REPORT_CONFIG["morning_report_time"]
        if current_time >= morning_time and self.last_morning != current_date:
            report = self.tracker.generate_morning_report()
            self.notifier.notify(report, subject="🌅 CoPaw 早报")
            self.last_morning = current_date
            print(f"✅ 早报已发送")
        
        # 晚报
        evening_time = REPORT_CONFIG["evening_report_time"]
        if current_time >= evening_time and self.last_evening != current_date:
            report = self.tracker.generate_evening_report()
            self.notifier.notify(report, subject="🌙 CoPaw 晚报")
            self.last_evening = current_date
            print(f"✅ 晚报已发送")
    
    def send_confirmation_request(self, trade: Trade, reason: str):
        """发送确认请求"""
        request = self.confirmation.create_confirmation_request(trade, reason)
        message = self.confirmation.generate_confirmation_message(request)
        
        # 通过所有渠道发送
        self.notifier.notify(
            message, 
            methods=["dingtalk", "email"],
            subject=f"🔔 交易确认 - {trade.symbol}"
        )
        
        return request


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='📊 资产跟踪与报告')
    parser.add_argument('--morning', action='store_true', help='生成早报')
    parser.add_argument('--evening', action='store_true', help='生成晚报')
    parser.add_argument('--status', action='store_true', help='查看资产状态')
    parser.add_argument('--confirm', type=str, help='确认交易ID')
    parser.add_argument('--cancel', type=str, help='取消交易ID')
    parser.add_argument('--pending', action='store_true', help='查看待确认交易')
    args = parser.parse_args()
    
    tracker = AssetTracker()
    
    if args.morning:
        print(tracker.generate_morning_report())
        return
    
    if args.evening:
        print(tracker.generate_evening_report())
        return
    
    if args.status:
        snapshot = tracker.get_current_portfolio()
        print(f"\n💰 资产状态:")
        print(f"   总资产: ${snapshot.total_value_usd:.2f}")
        print(f"   现金: ${snapshot.cash_usd:.2f}")
        print(f"   总盈亏: ${snapshot.total_pnl_usd:.2f} ({snapshot.total_pnl_percent:+.1f}%)")
        return
    
    if args.confirm:
        confirmation = TradeConfirmation(tracker)
        if confirmation.confirm_trade(args.confirm):
            print(f"✅ 交易已确认: {args.confirm}")
        else:
            print(f"❌ 找不到待确认交易: {args.confirm}")
        return
    
    if args.cancel:
        confirmation = TradeConfirmation(tracker)
        if confirmation.cancel_trade(args.cancel):
            print(f"✅ 交易已取消: {args.cancel}")
        else:
            print(f"❌ 找不到待取消交易: {args.cancel}")
        return
    
    if args.pending:
        pending = [t for t in tracker.trades if t['status'] == 'pending']
        print(f"\n📋 待确认交易: {len(pending)}")
        for t in pending:
            print(f"   {t['id']}: {t['type']} {t['amount']} {t['symbol']} @ ${t['price']:.4f}")
        return
    
    # 默认显示状态
    print(tracker.generate_morning_report())


if __name__ == "__main__":
    main()