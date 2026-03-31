#!/usr/bin/env python3
# =============================================================================
# 💰 真实交易系统 v1.0 - 从 $60 到 $200,000
# 
# 特点：
# 1. 本金保护第一
# 2. 止盈止损严格执行
# 3. 小仓位测试，有效才加仓
# 4. 每笔交易有逻辑
# =============================================================================

import os
import sys
import json
import time
import hmac
import hashlib
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict

# =============================================================================
# 配置
# =============================================================================

BASE_DIR = Path("/home/admin/Ziwei")
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data" / "real_trading"
LOG_DIR = DATA_DIR / "logs"

# 安全配置
SAFETY_CONFIG = {
    "initial_capital": 60,           # 初始本金
    "test_amount": 10,               # 第一笔测试金额
    "max_position_percent": 20,      # 最大仓位比例
    "stop_loss_percent": 3,          # 止损 3%
    "take_profit_percent": 5,        # 止盈 5%
    "max_daily_loss_percent": 5,     # 每日最大亏损
    "max_consecutive_losses": 3,     # 连续亏损次数限制
    "trade_cooldown_minutes": 5,     # 交易冷却时间
    "confirm_threshold_usd": 20,     # 需要确认的金额阈值
}

# =============================================================================
# 数据结构
# =============================================================================

@dataclass
class Position:
    """持仓"""
    symbol: str
    amount: float
    entry_price: float
    entry_time: str
    stop_loss: float
    take_profit: float
    status: str  # open, closed
    pnl_usd: Optional[float] = None
    pnl_percent: Optional[float] = None
    close_time: Optional[str] = None
    close_price: Optional[float] = None


@dataclass
class Trade:
    """交易记录"""
    id: str
    timestamp: str
    type: str  buy, sell
    symbol: str
    amount: float
    price: float
    total_usd: float
    status: str  # pending, confirmed, executed, cancelled
    reason: str
    notes: str = ""


# =============================================================================
# 真实交易系统
# =============================================================================

class RealTradingSystem:
    """真实交易系统"""
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.safety = SAFETY_CONFIG
        
        # 数据
        self.capital = self.safety["initial_capital"]
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.daily_pnl = 0
        self.consecutive_losses = 0
        self.last_trade_time = None
        
        # 确保目录存在
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        # 加载状态
        self.load_state()
        
        self.log("💰 真实交易系统初始化")
        self.log(f"   本金: ${self.capital:.2f}")
    
    def log(self, msg: str):
        """日志"""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] {msg}")
        
        # 写入日志文件
        log_file = LOG_DIR / f"trading_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] {msg}\n")
    
    def load_state(self):
        """加载状态"""
        state_file = DATA_DIR / "state.json"
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
                self.capital = state.get("capital", self.safety["initial_capital"])
                self.positions = {k: Position(**v) for k, v in state.get("positions", {}).items()}
                self.daily_pnl = state.get("daily_pnl", 0)
                self.consecutive_losses = state.get("consecutive_losses", 0)
        except:
            pass
    
    def save_state(self):
        """保存状态"""
        state_file = DATA_DIR / "state.json"
        state = {
            "capital": self.capital,
            "positions": {k: asdict(v) for k, v in self.positions.items()},
            "daily_pnl": self.daily_pnl,
            "consecutive_losses": self.consecutive_losses,
            "last_update": datetime.now().isoformat()
        }
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2, ensure_ascii=False, default=str)
    
    def get_price(self, symbol: str) -> Optional[float]:
        """获取实时价格"""
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return float(response.json()['price'])
        except Exception as e:
            self.log(f"❌ 获取价格失败: {e}")
        return None
    
    def can_trade(self, amount: float) -> tuple:
        """检查是否可以交易"""
        # 1. 检查金额限制
        max_trade = self.capital * (self.safety["max_position_percent"] / 100)
        if amount > max_trade:
            return False, f"金额超过最大仓位限制: ${amount:.2f} > ${max_trade:.2f}"
        
        # 2. 检查资金是否足够
        if amount > self.capital:
            return False, f"资金不足: ${amount:.2f} > ${self.capital:.2f}"
        
        # 3. 检查每日亏损限制
        if self.daily_pnl < -self.capital * (self.safety["max_daily_loss_percent"] / 100):
            return False, f"已达每日亏损限制"
        
        # 4. 检查连续亏损
        if self.consecutive_losses >= self.safety["max_consecutive_losses"]:
            return False, f"连续亏损{self.consecutive_losses}次，需冷却"
        
        # 5. 检查冷却时间
        if self.last_trade_time:
            cooldown = timedelta(minutes=self.safety["trade_cooldown_minutes"])
            if datetime.now() - self.last_trade_time < cooldown:
                return False, f"交易冷却中"
        
        return True, "可以交易"
    
    def calculate_stop_loss_take_profit(self, price: float, is_long: bool = True) -> tuple:
        """计算止损止盈价格"""
        if is_long:
            stop_loss = price * (1 - self.safety["stop_loss_percent"] / 100)
            take_profit = price * (1 + self.safety["take_profit_percent"] / 100)
        else:
            stop_loss = price * (1 + self.safety["stop_loss_percent"] / 100)
            take_profit = price * (1 - self.safety["take_profit_percent"] / 100)
        
        return stop_loss, take_profit
    
    def plan_buy(self, symbol: str, amount: float, reason: str) -> Optional[Trade]:
        """规划买入"""
        # 检查是否可以交易
        can_trade, msg = self.can_trade(amount)
        if not can_trade:
            self.log(f"❌ 买入被拒绝: {msg}")
            return None
        
        # 获取当前价格
        price = self.get_price(symbol)
        if not price:
            self.log(f"❌ 无法获取 {symbol} 价格")
            return None
        
        # 计算止损止盈
        stop_loss, take_profit = self.calculate_stop_loss_take_profit(price)
        
        # 创建交易ID
        trade_id = f"buy_{symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 创建交易
        trade = Trade(
            id=trade_id,
            timestamp=datetime.now().isoformat(),
            type="buy",
            symbol=symbol,
            amount=amount / price,  # 转换为币数量
            price=price,
            total_usd=amount,
            status="pending",
            reason=reason,
            notes=f"止损: ${stop_loss:.4f}, 止盈: ${take_profit:.4f}"
        )
        
        self.trades.append(trade)
        self.save_state()
        
        self.log(f"📝 买入已规划: {trade_id}")
        self.log(f"   {symbol} {trade.amount:.6f} @ ${price:.4f}")
        self.log(f"   总额: ${amount:.2f}")
        self.log(f"   止损: ${stop_loss:.4f} ({self.safety['stop_loss_percent']}%)")
        self.log(f"   止盈: ${take_profit:.4f} ({self.safety['take_profit_percent']}%)")
        
        # 检查是否需要确认
        if amount >= self.safety["confirm_threshold_usd"]:
            self.log(f"⚠️ 需要！金额 ${amount:.2f} >= ${self.safety['confirm_threshold_usd']}")
        
        return trade
    
    def check_positions(self):
        """检查持仓，执行止盈止损"""
        for symbol, position in list(self.positions.items()):
            if position.status != "open":
                continue
            
            # 获取当前价格
            current_price = self.get_price(symbol)
            if not current_price:
                continue
            
            # 检查止损
            if current_price <= position.stop_loss:
                self.log(f"🔴 触发止损: {symbol}")
                self.execute_sell(symbol, position.amount, "止损触发")
            
            # 检查止盈
            elif current_price >= position.take_profit:
                self.log(f"🟢 触发止盈: {symbol}")
                self.execute_sell(symbol, position.amount, "止盈触发")
    
    def execute_buy(self, trade_id: str) -> bool:
        """执行买入"""
        for trade in self.trades:
            if trade.id == trade_id and trade.status == "pending":
                # 这里应该调用真实API
                # 模拟执行
                trade.status = "executed"
                
                # 创建持仓
                stop_loss, take_profit = self.calculate_stop_loss_take_profit(trade.price)
                position = Position(
                    symbol=trade.symbol,
                    amount=trade.amount,
                    entry_price=trade.price,
                    entry_time=datetime.now().isoformat(),
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    status="open"
                )
                self.positions[trade.symbol] = position
                
                # 扣除资金
                self.capital -= trade.total_usd
                self.last_trade_time = datetime.now()
                
                self.save_state()
                self.log(f"✅ 买入已执行: {trade_id}")
                return True
        
        return False
    
    def execute_sell(self, symbol: str, amount: float, reason: str) -> Optional[Trade]:
        """执行卖出"""
        if symbol not in self.positions:
            self.log(f"❌ 无持仓: {symbol}")
            return None
        
        position = self.positions[symbol]
        
        # 获取当前价格
        price = self.get_price(symbol)
        if not price:
            return None
        
        # 计算盈亏
        total_usd = amount * price
        pnl_usd = (price - position.entry_price) * amount
        pnl_percent = (price - position.entry_price) / position.entry_price * 100
        
        # 创建卖出交易
        trade_id = f"sell_{symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        trade = Trade(
            id=trade_id,
            timestamp=datetime.now().isoformat(),
            type="sell",
            symbol=symbol,
            amount=amount,
            price=price,
            total_usd=total_usd,
            status="executed",
            reason=reason,
            notes=f"盈亏: ${pnl_usd:.2f} ({pnl_percent:+.2f}%)"
        )
        
        self.trades.append(trade)
        
        # 更新持仓
        position.status = "closed"
        position.close_time = datetime.now().isoformat()
        position.close_price = price
        position.pnl_usd = pnl_usd
        position.pnl_percent = pnl_percent
        
        # 更新资金
        self.capital += total_usd
        self.daily_pnl += pnl_usd
        
        # 更新连续亏损计数
        if pnl_usd < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        self.save_state()
        
        self.log(f"✅ 卖出已执行: {trade_id}")
        self.log(f"   {symbol} {amount:.6f} @ ${price:.4f}")
        self.log(f"   盈亏: ${pnl_usd:.2f} ({pnl_percent:+.2f}%)")
        
        return trade
    
    def get_status(self) -> str:
        """获取状态"""
        # 计算持仓价值
        positions_value = 0
        for symbol, pos in self.positions.items():
            if pos.status == "open":
                price = self.get_price(symbol)
                if price:
                    positions_value += pos.amount * price
        
        total_value = self.capital + positions_value
        total_pnl = total_value - self.safety["initial_capital"]
        total_pnl_percent = total_pnl / self.safety["initial_capital"] * 100
        
        status = f"""
╔══════════════════════════════════════════════════════════════╗
║                    💰 真实交易系统状态                        ║
╠══════════════════════════════════════════════════════════════╣
║  本金: ${self.capital:.2f}                                        ║
║  持仓价值: ${positions_value:.2f}                                 ║
║  总资产: ${total_value:.2f}                                       ║
║  总盈亏: ${total_pnl:.2f} ({total_pnl_percent:+.2f}%)                           ║
╠══════════════════════════════════════════════════════════════╣
║  今日盈亏: ${self.daily_pnl:.2f}                                  ║
║  连续亏损: {self.consecutive_losses} 次                                         ║
║  持仓数量: {len([p for p in self.positions.values() if p.status == 'open'])}                                           ║
╠══════════════════════════════════════════════════════════════╣
║  安全设置                                                     ║
║  ├── 止损: {self.safety['stop_loss_percent']}%                                                ║
║  ├── 止盈: {self.safety['take_profit_percent']}%                                                ║
║  └── 需确认金额: ${self.safety['confirm_threshold_usd']}                                    ║
╚══════════════════════════════════════════════════════════════╝
"""
        return status


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='💰 真实交易系统')
    parser.add_argument('--status', action='store_true', help='查看状态')
    parser.add_argument('--buy', nargs=2, metavar=('SYMBOL', 'AMOUNT'), help='规划买入')
    parser.add_argument('--check', action='store_true', help='检查持仓（止盈止损）')
    parser.add_argument('--sell', nargs=2, metavar=('SYMBOL', 'AMOUNT'), help='卖出')
    args = parser.parse_args()
    
    # 获取API密钥
    sys.path.insert(0, '/home/admin/Ziwei/scripts')
    try:
        from secure_key_storage import SecureKeyStorage
        storage = SecureKeyStorage()
        api_key = storage.get_key("BINANCE_API_KEY", "binance")
        api_secret = storage.get_key("BINANCE_API_SECRET", "binance")
    except:
        api_key = None
        api_secret = None
    
    system = RealTradingSystem(api_key, api_secret)
    
    if args.status:
        print(system.get_status())
        return
    
    if args.buy:
        symbol, amount = args.buy
        trade = system.plan_buy(symbol.upper(), float(amount), "手动买入")
        return
    
    if args.check:
        system.check_positions()
        return
    
    if args.sell:
        symbol, amount = args.sell
        system.execute_sell(symbol.upper(), float(amount), "手动卖出")
        return
    
    print(system.get_status())


if __name__ == "__main__":
    main()