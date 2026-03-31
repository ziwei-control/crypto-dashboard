#!/usr/bin/env python3
"""
紫微智控 - 轻量级自动交易系统 (Lite版)
专为小资金设计 (11 USDT)

功能：
1. 市场监测 - 扫描热点币、新币
2. 情绪分析 - 多维度评分
3. 自动买入 - 信号触发自动下单
4. 自动卖出 - 止盈止损自动执行
5. 资金保护 - 严格控制风险

策略来源：紫微智控 + Meme 监控 + 情绪分析
"""

import os
import sys
import json
import time
import hmac
import hashlib
import requests
import signal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

# ============================================================================
# 配置
# ============================================================================

# Binance API
API_KEY = "eYfsfhnD7DP2aCORqOhU6f2zXvKIFdTKpNNSunUbhw4sRkdnKIuZaV3jobrKiNZW"
API_SECRET = "MIj1n4Rk8Dtp5vvYMqkNz935niIGNjUJg2S2JNMALYsQw2HrLDgsbXGHIVLTBhSb"
BASE_URL = "https://api.binance.com"

# 资金配置
MAX_CAPITAL = 11.0          # 最大使用资金 (USDT)
SINGLE_TRADE = 10.0         # 单笔交易金额 (USDT) - 一次买完

# 动态止损配置
# 根据币种类型自动调整止损比例
STOP_LOSS_CONFIG = {
    'mainstream': 0.05,     # 主流币（BTC、ETH、SOL）止损 5%
    'meme': 0.08,           # Meme币（DOGE、SHIB、PEPE）止损 8%
    'new_coin': 0.15,       # 新币（7天内上市）止损 15%
    'high_volatility': 0.12, # 高波动币（24h波动>20%）止损 12%
    'default': 0.06,        # 默认止损 6%
}

# 止盈配置
TAKE_PROFIT = 0.08          # 止盈 8%

# 币种分类
MAINSTREAM_COINS = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'AVAX', 'MATIC']
MEME_COINS = ['DOGE', 'SHIB', 'PEPE', 'WIF', 'BONK', 'FLOKI', 'BOME', 'NEIRO']

# 策略配置 - 严格模式
CHECK_INTERVAL = 30         # 检查间隔 (秒) - 更频繁监控
MIN_VOLUME = 50_000_000     # 最小交易量 $50M - 更高流动性
MIN_CHANGE = 5.0            # 最小涨幅 5%
MAX_CHANGE = 15.0           # 最大涨幅 15%（避免过热）
MIN_SCORE = 85              # 最小评分 85（更严格）
MIN_WIN_RATE = 70           # 最小胜率 70%

# 严格规则
MAX_POSITIONS = 1           # 最大持仓数：1
ALLOW_ADD_POSITION = False  # 禁止补仓

# 新币配置（7天内上市）
NEW_COINS = {
    'G': {'date': '2026-03-13', 'name': 'Gravity'},
    'XPL': {'date': '2026-03-12', 'name': 'Explorer'},
    'ANIME': {'date': '2026-03-10', 'name': 'Anime'},
    'CFG': {'date': '2026-03-15', 'name': 'Centrifuge'},
}

# 热点赛道
HOT_SECTORS = {
    'AI': ['FET', 'TAO', 'RNDR', 'NEAR', 'AGIX'],
    'Meme': ['PEPE', 'WIF', 'BONK', 'DOGE', 'SHIB', 'FLOKI', 'BOME'],
    'RWA': ['ONDO', 'MKR', 'COMP'],
    'DePIN': ['RNDR', 'FIL', 'AR'],
}

# Meme 策略数据路径
MEME_DATA_PATH = "/home/admin/Ziwei/products/meme-monitor/data/latest_analysis.json"

# 排除币种（不交易）
EXCLUDE_COINS = ['USDC', 'BUSD', 'DAI', 'TUSD', 'USDP', 'FDUSD']

# 数据目录
DATA_DIR = Path("/home/admin/Ziwei/data/ziwei_lite")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# 数据类
# ============================================================================

@dataclass
class Position:
    """持仓"""
    symbol: str
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: float
    score: int
    reason: str
    opened_at: str
    status: str = "active"

@dataclass
class Signal:
    """交易信号"""
    symbol: str
    price: float
    change_24h: float
    volume: float
    score: int
    win_rate: int  # 胜率评估
    analysis: str  # 分析理由
    tags: List[str]
    action: str  # BUY, HOLD, SELL

# ============================================================================
# 核心类
# ============================================================================

class ZiweiLiteTrader:
    """紫微智控轻量级交易员"""
    
    def __init__(self):
        self.positions: Dict[str, Position] = {}
        self.capital = MAX_CAPITAL
        self.trades_history = []
        
        self._load_state()
        self._update_balance()
        
        print("=" * 60)
        print("🌟 紫微智控 - 轻量级自动交易系统")
        print("=" * 60)
        print(f"   可用资金: ${self.capital:.2f}")
        print(f"   单笔金额: ${SINGLE_TRADE:.2f}")
        print(f"   止盈: +{TAKE_PROFIT*100:.0f}%")
        print(f"   动态止损: 主流5% | Meme8% | 新币15%")
        print(f"   最小评分: {MIN_SCORE}")
        print("=" * 60)
    
    def _load_state(self):
        """加载状态"""
        state_file = DATA_DIR / "state.json"
        if state_file.exists():
            try:
                with open(state_file) as f:
                    state = json.load(f)
                    self.capital = state.get('capital', MAX_CAPITAL)
                    for sym, pos in state.get('positions', {}).items():
                        self.positions[sym] = Position(**pos)
                    self.trades_history = state.get('history', [])
                print(f"✅ 加载状态: {len(self.positions)} 持仓, ${self.capital:.2f} 可用")
            except Exception as e:
                print(f"⚠️ 加载状态失败: {e}")
    
    def _save_state(self):
        """保存状态"""
        state = {
            'capital': self.capital,
            'positions': {sym: asdict(pos) for sym, pos in self.positions.items()},
            'history': self.trades_history[-100:],  # 只保留最近100条
            'updated_at': datetime.now().isoformat(),
        }
        with open(DATA_DIR / "state.json", 'w') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def _update_balance(self):
        """更新余额"""
        try:
            balance = self._api_get_balance('USDT')
            if balance > 0:
                # 限制最大使用资金
                self.capital = min(balance, MAX_CAPITAL)
        except Exception as e:
            print(f"⚠️ 获取余额失败: {e}")
    
    # =========================================================================
    # API 方法
    # =========================================================================
    
    def _sign(self, params: dict) -> str:
        """签名"""
        query = '&'.join(f"{k}={v}" for k, v in params.items())
        sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
        return f"{query}&signature={sig}"
    
    def _api_request(self, method: str, endpoint: str, params: dict = None, signed: bool = False) -> Optional[dict]:
        """API请求"""
        url = f"{BASE_URL}{endpoint}"
        headers = {"X-MBX-APIKEY": API_KEY}
        
        if params is None:
            params = {}
        
        try:
            if signed:
                params['timestamp'] = int(time.time() * 1000)
                params['recvWindow'] = 5000
                query = self._sign(params)
                url = f"{url}?{query}"
            elif params:
                url = f"{url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
            
            if method == "GET":
                resp = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                resp = requests.post(url, headers=headers, timeout=10)
            elif method == "DELETE":
                resp = requests.delete(url, headers=headers, timeout=10)
            else:
                return None
            
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"API错误 {resp.status_code}: {resp.text[:100]}")
                return None
        except Exception as e:
            print(f"API异常: {e}")
            return None
    
    def _api_get_price(self, symbol: str) -> float:
        """获取价格"""
        data = self._api_request("GET", "/api/v3/ticker/price", {"symbol": f"{symbol}USDT"})
        return float(data['price']) if data else 0
    
    def _api_get_balance(self, asset: str) -> float:
        """获取余额"""
        data = self._api_request("GET", "/api/v3/account", signed=True)
        if data and 'balances' in data:
            for b in data['balances']:
                if b['asset'] == asset:
                    return float(b['free'])
        return 0
    
    def _api_buy(self, symbol: str, usdt_amount: float) -> Optional[dict]:
        """市价买入"""
        # 获取精度
        exchange_info = self._api_request("GET", "/api/v3/exchangeInfo")
        step_size = 0.0001
        min_qty = 0.0001
        
        if exchange_info:
            for s in exchange_info.get('symbols', []):
                if s['symbol'] == f"{symbol}USDT":
                    for f in s['filters']:
                        if f['filterType'] == 'LOT_SIZE':
                            step_size = float(f['stepSize'])
                        if f['filterType'] == 'NOTIONAL':
                            min_qty = float(f.get('minNotional', 5))
        
        # 计算数量
        price = self._api_get_price(symbol)
        if price <= 0:
            return None
        
        quantity = usdt_amount / price
        # 精度处理
        precision = len(str(step_size).rstrip('0').split('.')[-1]) if '.' in str(step_size) else 0
        quantity = round(quantity - (quantity % step_size), precision)
        
        print(f"\n💰 买入 {symbol}: {quantity} 个 @ ${price:.6f} = ${usdt_amount:.2f}")
        
        result = self._api_request("POST", "/api/v3/order", {
            "symbol": f"{symbol}USDT",
            "side": "BUY",
            "type": "MARKET",
            "quantity": quantity,
        }, signed=True)
        
        return result
    
    def _api_sell(self, symbol: str, quantity: float) -> Optional[dict]:
        """市价卖出"""
        print(f"\n💰 卖出 {symbol}: {quantity} 个")
        
        result = self._api_request("POST", "/api/v3/order", {
            "symbol": f"{symbol}USDT",
            "side": "SELL",
            "type": "MARKET",
            "quantity": quantity,
        }, signed=True)
        
        return result
    
    # =========================================================================
    # 策略方法
    # =========================================================================
    
    def scan_market(self) -> List[Signal]:
        """扫描市场 - 统一评分（技术 + Meme策略 + 情绪 + 新币 + 赛道）"""
        print(f"\n🔍 扫描市场（统一评分模式）...")
        
        signals = []
        
        # 加载 Meme 策略数据
        meme_data = self._load_meme_data()
        strategy_signals = {}
        sentiment_scores = {}
        cex_hot = {}
        
        if meme_data:
            # 解析策略信号
            for s in meme_data.get('strategy_signals', []):
                strategy_signals[s['symbol']] = s
            
            # 解析情绪排名
            for sent in meme_data.get('market_overview', {}).get('top_sentiment', []):
                sentiment_scores[sent['symbol']] = sent['score']
            
            # 解析 CEX 热门
            for hot in meme_data.get('cex_hot', []):
                cex_hot[hot['symbol']] = hot
        
        # 获取所有行情
        tickers = self._api_request("GET", "/api/v3/ticker/24hr")
        if not tickers:
            return signals
        
        for t in tickers:
            symbol = t['symbol']
            if not symbol.endswith('USDT'):
                continue
            
            coin = symbol.replace('USDT', '').replace('1000', '')
            
            # 排除
            if coin in EXCLUDE_COINS:
                continue
            
            try:
                price = float(t['lastPrice'])
                change_24h = float(t['priceChangePercent'])
                volume = float(t['quoteVolume'])
                high_24h = float(t['highPrice'])
                low_24h = float(t['lowPrice'])
                open_price = float(t['openPrice'])
                
                if price <= 0:
                    continue
                
                # 新币降低交易量要求（10M）
                is_new_coin = coin in NEW_COINS and (datetime.now() - datetime.strptime(NEW_COINS[coin]['date'], '%Y-%m-%d')).days <= 7
                min_vol = 10_000_000 if is_new_coin else MIN_VOLUME
                
                if volume < min_vol:
                    continue
                
                # ============================================================
                # 统一评分系统
                # ============================================================
                
                # 1. 技术评分 (30%)
                tech_score = 50
                price_pos = (price - low_24h) / (high_24h - low_24h) if high_24h != low_24h else 0.5
                volatility = (high_24h - low_24h) / open_price * 100 if open_price > 0 else 0
                
                # 价格位置
                if price_pos <= 0.3:
                    tech_score += 15
                elif price_pos >= 0.8:
                    tech_score -= 10
                
                # 波动率（新币容忍度更高）
                if is_new_coin:
                    if 5 <= volatility <= 30:
                        tech_score += 10
                else:
                    if 5 <= volatility <= 15:
                        tech_score += 10
                    elif volatility > 25:
                        tech_score -= 10
                
                # 涨幅
                if MIN_CHANGE <= change_24h <= MAX_CHANGE:
                    tech_score += 15
                elif change_24h > 20:
                    tech_score -= 10
                elif change_24h < -5:
                    tech_score -= 15
                
                # 交易量
                if volume > 200_000_000:
                    tech_score += 15
                elif volume > 100_000_000:
                    tech_score += 10
                elif volume > 50_000_000:
                    tech_score += 5
                
                tech_score = max(0, min(100, tech_score))
                
                # 2. Meme 策略评分 (30%)
                meme_score = 50
                strategy = strategy_signals.get(coin, {})
                
                if strategy:
                    signal = strategy.get('signal', '')
                    if signal == 'BUY':
                        meme_score += 30
                    elif signal == 'WEAK_BUY':
                        meme_score += 20
                    elif signal == 'SELL':
                        meme_score -= 30
                    meme_score += min(strategy.get('score', 0), 20)
                
                if coin in cex_hot:
                    hot_change = cex_hot[coin].get('price_change_24h', 0)
                    if 10 <= hot_change <= 30:
                        meme_score += 15
                    elif hot_change > 30:
                        meme_score += 5
                
                meme_score = max(0, min(100, meme_score))
                
                # 3. 情绪评分 (20%)
                sentiment_score = 50
                sent = sentiment_scores.get(coin, 0)
                if sent >= 7:
                    sentiment_score = 85
                elif sent >= 5:
                    sentiment_score = 70
                elif sent >= 3:
                    sentiment_score = 60
                
                # 4. 新币加分
                new_coin_bonus = 0
                if is_new_coin:
                    days = (datetime.now() - datetime.strptime(NEW_COINS[coin]['date'], '%Y-%m-%d')).days
                    if days <= 3:
                        new_coin_bonus = 30
                    elif days <= 7:
                        new_coin_bonus = 20
                    elif days <= 14:
                        new_coin_bonus = 10
                
                # 5. 赛道加分
                sector_bonus = 0
                for sector, coins in HOT_SECTORS.items():
                    if coin in coins:
                        if sector == 'AI':
                            sector_bonus = 20
                        elif sector == 'Meme':
                            sector_bonus = 15
                        else:
                            sector_bonus = 12
                        break
                
                # 6. 总分
                total_score = (
                    tech_score * 0.30 +
                    meme_score * 0.30 +
                    sentiment_score * 0.20 +
                    new_coin_bonus +
                    sector_bonus
                )
                total_score = min(100, total_score)
                
                # 7. 胜率
                if total_score >= 85:
                    win_rate = 90
                elif total_score >= 75:
                    win_rate = 80
                elif total_score >= 65:
                    win_rate = 70
                elif total_score >= 55:
                    win_rate = 60
                else:
                    win_rate = 40
                
                # 风险调整
                if volatility > 40:
                    win_rate -= 15
                if change_24h > 30:
                    win_rate -= 10
                win_rate = max(0, min(100, win_rate))
                
                # 8. 分析
                tags = []
                analysis_parts = []
                
                if price_pos <= 0.3:
                    tags.append("📍 低位")
                if tech_score >= 70:
                    tags.append("📈 技术强")
                
                if strategy and 'BUY' in strategy.get('signal', ''):
                    tags.append(f"🎯 {strategy['signal']}")
                
                if sent >= 5:
                    tags.append(f"😊 情绪{sent}")
                
                if new_coin_bonus > 0:
                    days = (datetime.now() - datetime.strptime(NEW_COINS[coin]['date'], '%Y-%m-%d')).days
                    tags.append(f"🆕 新币{days}天")
                
                for sector, coins in HOT_SECTORS.items():
                    if coin in coins:
                        emoji = "🤖" if sector == "AI" else "🎭" if sector == "Meme" else "🏠"
                        tags.append(f"{emoji} {sector}")
                        break
                
                if coin in cex_hot:
                    tags.append("🔥 CEX热门")
                
                analysis = f"技术{tech_score} | Meme{meme_score} | 情绪{sentiment_score}"
                
                # 9. 操作
                if total_score >= 75 and win_rate >= 70:
                    action = "BUY"
                elif total_score >= 60:
                    action = "HOLD"
                else:
                    action = "AVOID"
                
                signals.append(Signal(
                    symbol=coin,
                    price=price,
                    change_24h=change_24h,
                    volume=volume / 1_000_000,
                    score=int(total_score),
                    win_rate=win_rate,
                    analysis=analysis,
                    tags=tags,
                    action=action,
                ))
                
            except Exception as e:
                continue
        
        # 排序：综合评分 = 总分*0.5 + 胜率*0.3 + 动量*0.2
        signals.sort(key=lambda x: x.score * 0.5 + x.win_rate * 0.3 + max(0, x.change_24h) * 0.2, reverse=True)
        
        return signals[:30]
    
    def _load_meme_data(self) -> dict:
        """加载 Meme 策略数据"""
        try:
            with open(MEME_DATA_PATH) as f:
                return json.load(f)
        except:
            return {}
    
    def _can_buy(self) -> tuple:
        """检查是否可以买入"""
        # 1. 检查持仓数量
        active_positions = [p for p in self.positions.values() if p.status == "active"]
        if len(active_positions) >= MAX_POSITIONS:
            return False, f"已有持仓 {len(active_positions)} 个，限制 {MAX_POSITIONS} 个"
        
        # 2. 检查资金
        self._update_balance()
        if self.capital < SINGLE_TRADE:
            return False, f"资金不足 ${self.capital:.2f} < ${SINGLE_TRADE}"
        
        # 3. 禁止补仓检查
        for pos in active_positions:
            if pos.status == "active":
                return False, f"持有 {pos.symbol}，禁止补仓"
        
        return True, "可以买入"
    
    def check_positions(self):
        """检查持仓 - 止盈止损"""
        for symbol, pos in list(self.positions.items()):
            if pos.status != "active":
                continue
            
            current_price = self._api_get_price(symbol)
            if current_price <= 0:
                continue
            
            pnl_pct = (current_price / pos.entry_price - 1) * 100
            
            print(f"  {symbol}: ${current_price:.6f} | PnL: {pnl_pct:+.2f}% | 止损: ${pos.stop_loss:.6f} | 止盈: ${pos.take_profit:.6f}")
            
            # 止损检查
            if current_price <= pos.stop_loss:
                print(f"\n🚨 触发止损! {symbol}")
                self._execute_sell(symbol, "stop_loss")
            
            # 止盈检查
            elif current_price >= pos.take_profit:
                print(f"\n🎉 触发止盈! {symbol}")
                self._execute_sell(symbol, "take_profit")
    
    def _calculate_dynamic_stop_loss(self, symbol: str, entry_price: float, volatility: float) -> tuple:
        """计算动态止损止盈
        
        返回: (止损价, 止损比例, 原因)
        """
        # 1. 新币优先判断
        is_new = symbol in NEW_COINS and (datetime.now() - datetime.strptime(NEW_COINS[symbol]['date'], '%Y-%m-%d')).days <= 7
        
        if is_new:
            stop_ratio = STOP_LOSS_CONFIG['new_coin']
            reason = "新币止损15%"
        # 2. 高波动币
        elif volatility > 30:
            stop_ratio = STOP_LOSS_CONFIG['high_volatility']
            reason = f"高波动止损12%(波动{volatility:.0f}%)"
        # 3. Meme币
        elif symbol in MEME_COINS:
            stop_ratio = STOP_LOSS_CONFIG['meme']
            reason = "Meme止损8%"
        # 4. 主流币
        elif symbol in MAINSTREAM_COINS:
            stop_ratio = STOP_LOSS_CONFIG['mainstream']
            reason = "主流币止损5%"
        # 5. 默认
        else:
            stop_ratio = STOP_LOSS_CONFIG['default']
            reason = "默认止损6%"
        
        stop_price = entry_price * (1 - stop_ratio)
        
        return stop_price, stop_ratio, reason
    
    def _execute_buy(self, signal: Signal):
        """执行买入"""
        if self.capital < SINGLE_TRADE:
            print(f"⚠️ 资金不足: ${self.capital:.2f} < ${SINGLE_TRADE}")
            return False
        
        # 下单
        result = self._api_buy(signal.symbol, SINGLE_TRADE)
        
        if result and 'orderId' in result:
            # 记录持仓
            price = self._api_get_price(signal.symbol)
            quantity = SINGLE_TRADE / price
            
            # 获取波动率（从信号中估算，或默认10%）
            volatility = abs(signal.change_24h) * 2  # 简单估算
            if volatility < 5:
                volatility = 10  # 默认值
            
            # 动态止损止盈
            stop_price, stop_ratio, stop_reason = self._calculate_dynamic_stop_loss(signal.symbol, price, volatility)
            take_profit_price = price * (1 + TAKE_PROFIT)
            
            self.positions[signal.symbol] = Position(
                symbol=signal.symbol,
                entry_price=price,
                quantity=quantity,
                stop_loss=stop_price,
                take_profit=take_profit_price,
                score=signal.score,
                reason=f"{stop_reason} | " + ' | '.join(signal.tags[:3]),
                opened_at=datetime.now().isoformat(),
            )
            
            self.capital -= SINGLE_TRADE
            self._save_state()
            
            print(f"✅ 买入成功: {signal.symbol}")
            print(f"   入场价: ${price:.6f}")
            print(f"   止损价: ${stop_price:.6f} ({stop_reason})")
            print(f"   止盈价: ${take_profit_price:.6f} (+{TAKE_PROFIT*100:.0f}%)")
            print(f"   风险: 最多亏损 ${quantity * (price - stop_price):.2f}")
            
            return True
        else:
            print(f"❌ 买入失败: {result}")
            return False
    
    def _execute_sell(self, symbol: str, reason: str):
        """执行卖出"""
        pos = self.positions.get(symbol)
        if not pos:
            return False
        
        result = self._api_sell(symbol, pos.quantity)
        
        if result and 'orderId' in result:
            exit_price = self._api_get_price(symbol)
            pnl = (exit_price - pos.entry_price) * pos.quantity
            pnl_pct = (exit_price / pos.entry_price - 1) * 100
            
            self.capital += exit_price * pos.quantity
            pos.status = "closed"
            
            # 记录历史
            self.trades_history.append({
                'symbol': symbol,
                'entry_price': pos.entry_price,
                'exit_price': exit_price,
                'quantity': pos.quantity,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'reason': reason,
                'closed_at': datetime.now().isoformat(),
            })
            
            self._save_state()
            
            print(f"✅ 卖出成功: {symbol}")
            print(f"   入场价: ${pos.entry_price:.6f}")
            print(f"   出场价: ${exit_price:.6f}")
            print(f"   盈亏: ${pnl:.4f} ({pnl_pct:+.2f}%)")
            
            return True
        else:
            print(f"❌ 卖出失败: {result}")
            return False
    
    # =========================================================================
    # 主循环
    # =========================================================================
    
    def run(self):
        """运行 - 严格模式"""
        print("\n🚀 启动自动交易（严格模式）...")
        print(f"   规则: 评分≥{MIN_SCORE} | 胜率≥{MIN_WIN_RATE}% | 单仓 | 禁补仓")
        
        while True:
            try:
                # 1. 检查持仓 - 纪律卖出
                print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')}")
                print("📊 检查持仓...")
                self.check_positions()
                
                # 2. 检查是否可以买入
                can_buy, reason = self._can_buy()
                
                if can_buy:
                    # 3. 扫描市场
                    signals = self.scan_market()
                    
                    if signals:
                        print(f"\n🎯 TOP 5 候选:")
                        for i, s in enumerate(signals[:5], 1):
                            status = "✅" if s.action == "BUY" else "⏸️"
                            print(f"  {i}. {s.symbol}: ${s.price:.6f} | {s.change_24h:+.1f}%")
                            print(f"     评分:{s.score} | 胜率:{s.win_rate}% | {status}")
                            print(f"     分析: {s.analysis}")
                        
                        # 4. 严格买入条件
                        best = signals[0]
                        
                        # 必须满足所有条件
                        conditions = [
                            (best.action == "BUY", f"操作信号: {best.action}"),
                            (best.score >= MIN_SCORE, f"评分: {best.score} ≥ {MIN_SCORE}"),
                            (best.win_rate >= MIN_WIN_RATE, f"胜率: {best.win_rate}% ≥ {MIN_WIN_RATE}%"),
                            (best.symbol not in self.positions, f"未持有: {best.symbol}"),
                        ]
                        
                        all_pass = True
                        print(f"\n🔍 买入检查:")
                        for cond, desc in conditions:
                            status = "✅" if cond else "❌"
                            print(f"   {status} {desc}")
                            if not cond:
                                all_pass = False
                        
                        if all_pass:
                            print(f"\n🤖 触发买入: {best.symbol}")
                            print(f"   理由: {best.analysis}")
                            self._execute_buy(best)
                        else:
                            print(f"\n⏸️ 不满足条件，等待...")
                    else:
                        print("  无符合条件的信号")
                else:
                    print(f"  {reason}")
                
                # 5. 等待
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                print("\n👋 停止交易")
                self._save_state()
                break
            except Exception as e:
                print(f"❌ 错误: {e}")
                time.sleep(10)
    
    def status(self):
        """状态"""
        print("\n" + "=" * 60)
        print("📊 当前状态")
        print("=" * 60)
        print(f"   可用资金: ${self.capital:.2f} / ${MAX_CAPITAL:.2f}")
        print(f"   持仓数量: {len([p for p in self.positions.values() if p.status == 'active'])} / {MAX_POSITIONS}")
        print(f"   买入条件: 评分≥{MIN_SCORE} | 胜率≥{MIN_WIN_RATE}%")
        print(f"   止盈: +{TAKE_PROFIT*100:.0f}%")
        print(f"   动态止损配置:")
        print(f"      主流币: {STOP_LOSS_CONFIG['mainstream']*100:.0f}%")
        print(f"      Meme币: {STOP_LOSS_CONFIG['meme']*100:.0f}%")
        print(f"      新币: {STOP_LOSS_CONFIG['new_coin']*100:.0f}%")
        print(f"      高波动: {STOP_LOSS_CONFIG['high_volatility']*100:.0f}%")
        
        active = [p for p in self.positions.values() if p.status == "active"]
        if active:
            print("\n   📍 持仓详情:")
            for pos in active:
                current = self._api_get_price(pos.symbol)
                pnl = (current / pos.entry_price - 1) * 100 if current > 0 else 0
                pnl_color = "🟢" if pnl >= 0 else "🔴"
                
                # 计算实际止损比例
                stop_ratio = (pos.entry_price - pos.stop_loss) / pos.entry_price * 100
                
                print(f"\n   {pos.symbol}: {pos.quantity:.4f} @ ${pos.entry_price:.6f}")
                print(f"      当前: ${current:.6f} | {pnl_color} {pnl:+.2f}%")
                print(f"      止盈: ${pos.take_profit:.6f} (+{TAKE_PROFIT*100:.0f}%)")
                print(f"      止损: ${pos.stop_loss:.6f} (-{stop_ratio:.0f}%)")
                print(f"      最大亏损: ${pos.quantity * (pos.entry_price - pos.stop_loss):.2f}")
                print(f"      理由: {pos.reason}")
        else:
            print("\n   📍 无持仓，等待买入信号...")
        
        if self.trades_history:
            wins = len([t for t in self.trades_history if t.get('pnl', 0) > 0])
            total = len(self.trades_history)
            total_pnl = sum(t.get('pnl', 0) for t in self.trades_history)
            print(f"\n   📈 历史交易: {total} 笔 | 胜率: {wins/total*100:.0f}% | 总盈亏: ${total_pnl:.2f}")

# ============================================================================
# 主函数
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="紫微智控轻量级交易系统")
    parser.add_argument("--run", action="store_true", help="启动自动交易")
    parser.add_argument("--status", action="store_true", help="查看状态")
    parser.add_argument("--scan", action="store_true", help="扫描市场")
    parser.add_argument("--buy", metavar="SYMBOL", help="手动买入")
    parser.add_argument("--sell", metavar="SYMBOL", help="手动卖出")
    
    args = parser.parse_args()
    
    trader = ZiweiLiteTrader()
    
    if args.run:
        trader.run()
    elif args.status:
        trader.status()
    elif args.scan:
        signals = trader.scan_market()
        print("\n" + "=" * 70)
        print(f"🎯 市场扫描结果 (评分≥{MIN_SCORE}, 胜率≥{MIN_WIN_RATE}%)")
        print(f"   综合评分 = 评分×0.6 + 胜率×0.4")
        print("=" * 70)
        for i, s in enumerate(signals[:10], 1):
            composite = s.score * 0.6 + s.win_rate * 0.4
            status = "✅ BUY" if s.action == "BUY" else "⏸️ HOLD" if s.action == "HOLD" else "❌ AVOID"
            best = "⭐ 最优" if i == 1 and s.action == "BUY" else ""
            print(f"\n{i}. {s.symbol}: ${s.price:.6f} | {s.change_24h:+.1f}% | 综合:{composite:.0f} {best}")
            print(f"   评分:{s.score} | 胜率:{s.win_rate}% | {status}")
            print(f"   分析: {s.analysis}")
            if s.tags:
                print(f"   标签: {' '.join(s.tags)}")
    elif args.buy:
        signal = Signal(
            symbol=args.buy.upper(),
            price=trader._api_get_price(args.buy.upper()),
            change_24h=0,
            volume=0,
            score=100,
            tags=["手动"],
            action="BUY",
        )
        trader._execute_buy(signal)
    elif args.sell:
        trader._execute_sell(args.sell.upper(), "manual")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()