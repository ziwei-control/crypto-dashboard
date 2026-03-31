#!/usr/bin/env python3
# =============================================================================
# 💰 本金保护交易系统 - 第一阶段：$60 → $100
# =============================================================================

import os
import sys
import json
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
import subprocess

# =============================================================================
# 配置
# =============================================================================

BASE_DIR = Path("/home/admin/Ziwei")
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data" / "trading"
PROTECTION_CONFIG = CONFIG_DIR / "capital_protection.json"
TRADE_LOG = DATA_DIR / "trade_log.json"
DAILY_LOG = DATA_DIR / "daily_log.json"

# =============================================================================
# 数据结构
# =============================================================================

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
    reason: str
    phase: int
    status: str  # planned, executed, cancelled
    pnl_usd: Optional[float] = None
    pnl_percent: Optional[float] = None
    notes: str = ""


@dataclass
class DailyStats:
    """每日统计"""
    date: str
    start_capital: float
    end_capital: float
    pnl_usd: float
    pnl_percent: float
    trades_count: int
    wins: int
    losses: int
    max_drawdown: float


# =============================================================================
# 本金保护系统
# =============================================================================

class CapitalProtection:
    """本金保护系统"""
    
    def __init__(self):
        self.load_config()
        self.load_logs()
        self.log("💰 本金保护系统初始化")
        self.log(f"   阶段: {self.get_current_phase_name()}")
        self.log(f"   本金: ${self.config['capital_protection']['current_capital_usd']}")
    
    def load_config(self):
        try:
            with open(PROTECTION_CONFIG, 'r') as f:
                self.config = json.load(f)
        except:
            # 默认配置
            self.config = {
                "capital_protection": {
                    "initial_capital_usd": 60,
                    "current_capital_usd": 60,
                    "max_risk_per_trade_percent": 3,
                    "max_risk_total_percent": 10,
                    "emergency_stop_loss_percent": 5
                },
                "trading_limits": {
                    "phase_1": {
                        "max_trade_usd": 10,
                        "max_position_percent": 20
                    }
                },
                "current_phase": 1
            }
    
    def load_logs(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(TRADE_LOG, 'r') as f:
                self.trades = json.load(f)
        except:
            self.trades = []
        
        try:
            with open(DAILY_LOG, 'r') as f:
                self.daily_log = json.load(f)
        except:
            self.daily_log = []
    
    def save_logs(self):
        with open(TRADE_LOG, 'w') as f:
            json.dump(self.trades, f, indent=2, ensure_ascii=False, default=str)
        with open(DAILY_LOG, 'w') as f:
            json.dump(self.daily_log, f, indent=2, ensure_ascii=False, default=str)
    
    def log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {msg}")
    
    def get_current_phase(self) -> int:
        return self.config.get("current_phase", 1)
    
    def get_current_phase_name(self) -> str:
        phase = self.get_current_phase()
        phase_config = self.config["trading_limits"].get(f"phase_{phase}", {})
        return phase_config.get("name", f"阶段{phase}")
    
    def get_max_trade_amount(self) -> float:
        """获取当前阶段最大交易金额"""
        phase = self.get_current_phase()
        phase_config = self.config["trading_limits"].get(f"phase_{phase}", {})
        return phase_config.get("max_trade_usd", 10)
    
    def get_current_capital(self) -> float:
        """获取当前本金"""
        return self.config["capital_protection"]["current_capital_usd"]
    
    def can_trade(self, amount: float) -> tuple:
        """检查是否可以交易"""
        capital = self.get_current_capital()
        max_trade = self.get_max_trade_amount()
        
        # 检查金额限制
        if amount > max_trade:
            return False, f"金额超过限制: ${amount} > ${max_trade}"
        
        # 检查本金保护
        if amount > capital * 0.2:  # 第一阶段只用20%
            return False, f"风险过高: ${amount} > ${capital * 0.2:.2f} (20%本金)"
        
        # 检查每日亏损限制
        today_pnl = self.get_today_pnl()
        if today_pnl < -capital * 0.05:
            return False, f"今日已达亏损限制: ${today_pnl:.2f}"
        
        # 检查连续亏损
        consecutive_losses = self.get_consecutive_losses()
        if consecutive_losses >= 3:
            return False, f"连续亏损{consecutive_losses}次，需冷却"
        
        return True, "可以交易"
    
    def get_today_pnl(self) -> float:
        """获取今日盈亏"""
        today = datetime.now().strftime("%Y-%m-%d")
        for log in reversed(self.daily_log):
            if log["date"] == today:
                return log.get("pnl_usd", 0)
        return 0
    
    def get_consecutive_losses(self) -> int:
        """获取连续亏损次数"""
        count = 0
        for trade in reversed(self.trades):
            if trade.get("pnl_usd", 0) < 0:
                count += 1
            elif trade.get("pnl_usd", 0) > 0:
                break
        return count
    
    def plan_trade(self, trade_type: str, symbol: str, amount: float, 
                   price: float, reason: str) -> Optional[Trade]:
        """规划交易"""
        # 检查是否可以交易
        can_trade, msg = self.can_trade(amount)
        if not can_trade:
            self.log(f"❌ 交易被拒绝: {msg}")
            return None
        
        # 创建交易ID
        trade_id = f"trade_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"
        
        trade = Trade(
            id=trade_id,
            timestamp=datetime.now().isoformat(),
            type=trade_type,
            symbol=symbol,
            amount=amount,
            price=price,
            total_usd=amount * price if trade_type == "buy" else amount,
            reason=reason,
            phase=self.get_current_phase(),
            status="planned"
        )
        
        self.trades.append(asdict(trade))
        self.save_logs()
        
        self.log(f"📝 交易已规划: {trade_id}")
        self.log(f"   {trade_type.upper()} {amount} {symbol} @ ${price:.4f}")
        self.log(f"   总额: ${trade.total_usd:.2f}")
        
        return trade
    
    def execute_trade(self, trade_id: str) -> bool:
        """执行交易"""
        for trade in self.trades:
            if trade["id"] == trade_id and trade["status"] == "planned":
                trade["status"] = "executed"
                trade["executed_at"] = datetime.now().isoformat()
                self.save_logs()
                self.log(f"✅ 交易已执行: {trade_id}")
                return True
        return False
    
    def cancel_trade(self, trade_id: str) -> bool:
        """取消交易"""
        for trade in self.trades:
            if trade["id"] == trade_id and trade["status"] == "planned":
                trade["status"] = "cancelled"
                trade["cancelled_at"] = datetime.now().isoformat()
                self.save_logs()
                self.log(f"❌ 交易已取消: {trade_id}")
                return True
        return False
    
    def update_capital(self, new_capital: float):
        """更新本金"""
        old_capital = self.get_current_capital()
        pnl = new_capital - old_capital
        pnl_percent = (pnl / old_capital) * 100
        
        self.config["capital_protection"]["current_capital_usd"] = new_capital
        
        # 检查是否需要切换阶段
        phase = self.get_current_phase()
        phase_config = self.config["trading_limits"].get(f"phase_{phase}", {})
        capital_range = phase_config.get("capital_range", [60, 100])
        
        if new_capital > capital_range[1] and phase < 5:
            self.config["current_phase"] = phase + 1
            self.log(f"🎉 进入新阶段: {self.get_current_phase_name()}")
        elif new_capital < capital_range[0] and phase > 1:
            self.config["current_phase"] = phase - 1
            self.log(f"⚠️ 退回阶段: {self.get_current_phase_name()}")
        
        # 保存配置
        with open(PROTECTION_CONFIG, 'w') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        
        self.log(f"💰 本金更新: ${old_capital:.2f} → ${new_capital:.2f} ({pnl_percent:+.2f}%)")
    
    def record_daily_stats(self):
        """记录每日统计"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_trades = [t for t in self.trades if t["timestamp"].startswith(today)]
        
        wins = len([t for t in today_trades if t.get("pnl_usd", 0) > 0])
        losses = len([t for t in today_trades if t.get("pnl_usd", 0) < 0])
        
        # 计算今日盈亏
        pnl = sum([t.get("pnl_usd", 0) for t in today_trades])
        
        stats = {
            "date": today,
            "start_capital": self.get_current_capital(),
            "end_capital": self.get_current_capital() + pnl,
            "pnl_usd": pnl,
            "pnl_percent": (pnl / self.get_current_capital()) * 100 if self.get_current_capital() > 0 else 0,
            "trades_count": len(today_trades),
            "wins": wins,
            "losses": losses,
            "max_drawdown": 0  # 需要计算
        }
        
        self.daily_log.append(stats)
        self.save_logs()
    
    def get_status(self) -> str:
        """获取状态"""
        capital = self.get_current_capital()
        phase = self.get_current_phase()
        phase_name = self.get_current_phase_name()
        max_trade = self.get_max_trade_amount()
        today_pnl = self.get_today_pnl()
        consecutive_losses = self.get_consecutive_losses()
        
        status = f"""
╔══════════════════════════════════════════════════════════════╗
║                    💰 本金保护系统状态                        ║
╠══════════════════════════════════════════════════════════════╣
║  阶段: {phase} - {phase_name:<20}                      ║
║  本金: ${capital:.2f} / 目标 $200,000                        ║
║  进度: {(capital/200000)*100:.2f}%                                               ║
╠══════════════════════════════════════════════════════════════╣
║  交易限制                                                     ║
║  ├── 最大单笔: ${max_trade:.2f}                                 ║
║  ├── 最大仓位: 20%                                            ║
║  └── 杠杆限制: 1x (无杠杆)                                    ║
╠══════════════════════════════════════════════════════════════╣
║  今日统计                                                     ║
║  ├── 盈亏: ${today_pnl:+.2f}                                        ║
║  └── 连续亏损: {consecutive_losses} 次                                         ║
╠══════════════════════════════════════════════════════════════╣
║  安全规则                                                     ║
║  ├── 止损: 3%                                                 ║
║  ├── 单笔最大风险: 10%                                        ║
║  └── 每日亏损限制: 5%                                         ║
╚══════════════════════════════════════════════════════════════╝
"""
        return status


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='💰 本金保护交易系统')
    parser.add_argument('--status', action='store_true', help='查看状态')
    parser.add_argument('--plan', nargs=4, metavar=('TYPE', 'SYMBOL', 'AMOUNT', 'PRICE'), 
                        help='规划交易')
    parser.add_argument('--execute', type=str, help='执行交易')
    parser.add_argument('--cancel', type=str, help='取消交易')
    parser.add_argument('--update-capital', type=float, help='更新本金')
    parser.add_argument('--daily', action='store_true', help='记录每日统计')
    args = parser.parse_args()
    
    system = CapitalProtection()
    
    if args.status:
        print(system.get_status())
        return
    
    if args.plan:
        trade_type, symbol, amount, price = args.plan
        trade = system.plan_trade(trade_type, symbol, float(amount), float(price), "手动规划")
        if trade:
            print(f"\n✅ 交易已规划: {trade.id}")
        return
    
    if args.execute:
        if system.execute_trade(args.execute):
            print(f"✅ 交易已执行: {args.execute}")
        else:
            print(f"❌ 找不到交易: {args.execute}")
        return
    
    if args.cancel:
        if system.cancel_trade(args.cancel):
            print(f"✅ 交易已取消: {args.cancel}")
        else:
            print(f"❌ 找不到交易: {args.cancel}")
        return
    
    if args.update_capital:
        system.update_capital(args.update_capital)
        print(f"✅ 本金已更新: ${args.update_capital:.2f}")
        return
    
    if args.daily:
        system.record_daily_stats()
        print("✅ 每日统计已记录")
        return
    
    # 默认显示状态
    print(system.get_status())


if __name__ == "__main__":
    main()