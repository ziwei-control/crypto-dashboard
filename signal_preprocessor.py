#!/usr/bin/env python3
"""
信号前置处理器
解决信号滞后问题，过滤过期信号，识别新鲜信号

核心逻辑：
1. 信号时效性 - 信号发出后多久了？
2. 价格启动检测 - 价格刚启动 vs 已经涨完
3. 追涨风险评估 - 信号出现时价格已涨多少
4. 新鲜信号标记 - 只保留有效信号

问题场景：
- 信号说 BUY，但价格已经涨了 5% → 过期信号，不追
- 信号说 BUY，价格刚涨 0.5% → 新鲜信号，可入
- 信号说 SELL，价格已经跌了 8% → 过期信号，已止损
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# ============================================================
# 配置
# ============================================================

INTEL_DIR = Path("/home/admin/Ziwei/data/intel")
MEME_DATA = Path("/home/admin/Ziwei/products/meme-monitor/data/latest_analysis.json")
BINANCE_API = "https://api.binance.com"

# 信号时效配置
SIGNAL_CONFIG = {
    # 价格启动阈值（信号有效范围内）
    'fresh_threshold': 0.02,      # 涨幅 < 2% = 新鲜信号
    'valid_threshold': 0.05,      # 涨幅 < 5% = 有效信号
    'expired_threshold': 0.08,    # 涨幅 > 8% = 过期信号
    
    # 信号有效时间
    'fresh_minutes': 30,          # 30分钟内 = 新鲜
    'valid_minutes': 120,         # 2小时内 = 有效
    'expired_minutes': 240,       # 4小时后 = 过期
    
    # 追涨风险
    'safe_chase': 0.03,           # 3%以内安全追涨
    'risky_chase': 0.06,          # 3-6%需谨慎
    'danger_chase': 0.10,         # 10%以上危险
}

# 币种分类
MAINSTREAM_COINS = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA']
MEME_COINS = ['DOGE', 'SHIB', 'PEPE', 'WIF', 'BONK', 'FLOKI']
NEW_COINS = ['G', 'XPL', 'ANIME', 'CFG']

# ============================================================
# 数据类
# ============================================================

@dataclass
class ProcessedSignal:
    """处理后的信号"""
    symbol: str
    signal_type: str           # BUY / WEAK_BUY / SELL / HOLD
    signal_time: datetime
    signal_age_minutes: float
    
    # 价格信息
    current_price: float
    price_at_signal: float
    price_change_pct: float    # 信号后价格变化
    change_24h: float          # 24小时价格变化（关键！）
    
    # 信号依据（新增！）
    signal_basis: str          # FRESH / DIP / CHASE / CAUTION / LATE / TIMELY
    
    # 时效性
    freshness: str             # FRESH / VALID / EXPIRED
    freshness_score: float     # 0-100
    
    # 追涨风险
    chase_risk: str            # SAFE / CAUTION / DANGER
    chase_risk_score: float    # 0-100
    
    # 综合评分
    actionability: float       # 0-100 可操作性
    recommendation: str        # ENTER / WAIT / AVOID
    
    # 原因
    reasons: List[str]

# ============================================================
# 核心类
# ============================================================

class SignalPreprocessor:
    """信号前置处理器"""
    
    def __init__(self):
        self.price_history = self._load_price_history()
        self.signals = self._load_signals()
        
        print("=" * 70)
        print("🔄 信号前置处理器")
        print("=" * 70)
        print(f"   新鲜阈值: < {SIGNAL_CONFIG['fresh_threshold']*100:.0f}%")
        print(f"   有效阈值: < {SIGNAL_CONFIG['valid_threshold']*100:.0f}%")
        print(f"   过期阈值: > {SIGNAL_CONFIG['expired_threshold']*100:.0f}%")
        print("=" * 70)
    
    def _load_price_history(self) -> List[dict]:
        """加载价格历史"""
        history = []
        files = sorted(INTEL_DIR.glob("intel_*.json"), reverse=True)[:20]
        
        for f in files:
            try:
                with open(f) as fp:
                    data = json.load(fp)
                    history.append({
                        'timestamp': datetime.fromisoformat(data['timestamp']),
                        'prices': data.get('prices', {})
                    })
            except:
                continue
        
        return sorted(history, key=lambda x: x['timestamp'], reverse=True)
    
    def _load_signals(self) -> dict:
        """加载信号数据"""
        try:
            with open(MEME_DATA) as f:
                return json.load(f)
        except:
            return {}
    
    def _get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        try:
            resp = requests.get(f"{BINANCE_API}/api/v3/ticker/price?symbol={symbol}USDT")
            if resp.status_code == 200:
                return float(resp.json()['price'])
        except:
            pass
        return 0.0
    
    def _get_price_at_time(self, symbol: str, target_time: datetime) -> Tuple[float, datetime]:
        """获取指定时间的价格"""
        closest_price = 0.0
        closest_time = None
        min_diff = timedelta(hours=24)
        
        for record in self.price_history:
            if symbol not in record['prices']:
                continue
            
            diff = abs(record['timestamp'] - target_time)
            if diff < min_diff:
                min_diff = diff
                closest_price = float(record['prices'][symbol]['price'])
                closest_time = record['timestamp']
        
        return closest_price, closest_time
    
    def _estimate_signal_time(self, symbol: str) -> datetime:
        """估算信号产生时间"""
        # 从策略信号获取
        for s in self.signals.get('strategy_signals', []):
            if s['symbol'] == symbol:
                # 检查价格历史，找到信号开始的时间点
                # 简化：使用最新情报时间
                pass
        
        # 默认使用最近情报时间
        if self.price_history:
            return self.price_history[0]['timestamp']
        
        return datetime.now()
    
    def _calculate_freshness(self, price_change_pct: float, signal_age_minutes: float) -> Tuple[str, float]:
        """计算信号新鲜度"""
        score = 100.0
        
        # 基于价格变化扣分
        if price_change_pct > SIGNAL_CONFIG['expired_threshold']:
            score -= 50
        elif price_change_pct > SIGNAL_CONFIG['valid_threshold']:
            score -= 30
        elif price_change_pct > SIGNAL_CONFIG['fresh_threshold']:
            score -= 10
        
        # 基于时间扣分
        if signal_age_minutes > SIGNAL_CONFIG['expired_minutes']:
            score -= 30
        elif signal_age_minutes > SIGNAL_CONFIG['valid_minutes']:
            score -= 15
        elif signal_age_minutes > SIGNAL_CONFIG['fresh_minutes']:
            score -= 5
        
        score = max(0, min(100, score))
        
        # 新鲜度等级
        if score >= 70:
            freshness = "FRESH"
        elif score >= 40:
            freshness = "VALID"
        else:
            freshness = "EXPIRED"
        
        return freshness, score
    
    def _calculate_chase_risk(self, price_change_pct: float) -> Tuple[str, float]:
        """计算追涨风险"""
        abs_change = abs(price_change_pct)
        
        if abs_change <= SIGNAL_CONFIG['safe_chase']:
            return "SAFE", 90
        elif abs_change <= SIGNAL_CONFIG['risky_chase']:
            return "CAUTION", 60
        else:
            return "DANGER", 30
    
    def _get_24h_change(self, symbol: str) -> float:
        """获取24小时价格变化"""
        try:
            resp = requests.get(f"{BINANCE_API}/api/v3/ticker/24hr?symbol={symbol}USDT")
            if resp.status_code == 200:
                return float(resp.json()['priceChangePercent']) / 100
        except:
            pass
        return 0.0
    
    def _detect_signal_basis(self, symbol: str, signal_type: str, change_24h: float) -> Tuple[str, List[str]]:
        """检测信号依据：是基于已涨价格还是潜在机会"""
        reasons = []
        
        if 'BUY' in signal_type:
            if change_24h > 0.05:  # 24h涨超5%
                basis = "CHASE"  # 追涨信号
                reasons.append(f"⚠️ 信号基于已涨{change_24h*100:.1f}%，属追涨信号")
                reasons.append(f"   最佳入场点已过，建议等待回调")
            elif change_24h > 0.03:  # 24h涨超3%
                basis = "CAUTION"
                reasons.append(f"🟡 信号基于已涨{change_24h*100:.1f}%，需谨慎")
            elif change_24h < -0.02:  # 24h下跌
                basis = "DIP"  # 抄底信号
                reasons.append(f"✅ 信号基于下跌{change_24h*100:.1f}%，属抄底机会")
            else:
                basis = "FRESH"
                reasons.append(f"✅ 信号基于正常波动，属新鲜机会")
        elif 'SELL' in signal_type:
            if change_24h < -0.05:  # 24h跌超5%
                basis = "LATE"  # 卖出信号已晚
                reasons.append(f"❌ 信号基于已跌{change_24h*100:.1f}%，卖出信号已晚")
            else:
                basis = "TIMELY"
                reasons.append(f"✅ 卖出信号及时")
        else:
            basis = "NEUTRAL"
            reasons.append(f"➡️ 中性信号")
        
        return basis, reasons
    
    def process_signal(self, symbol: str, signal_type: str = None) -> ProcessedSignal:
        """处理单个信号"""
        
        # 获取信号类型
        if signal_type is None:
            for s in self.signals.get('strategy_signals', []):
                if s['symbol'] == symbol:
                    signal_type = s['signal']
                    break
        
        if signal_type is None:
            signal_type = "UNKNOWN"
        
        # 获取价格信息
        current_price = self._get_current_price(symbol)
        signal_time = self._estimate_signal_time(symbol)
        price_at_signal, actual_time = self._get_price_at_time(symbol, signal_time)
        
        if price_at_signal == 0:
            price_at_signal = current_price
        
        # 计算价格变化
        price_change_pct = (current_price / price_at_signal - 1) if price_at_signal > 0 else 0
        
        # 计算24h变化（关键！）
        change_24h = self._get_24h_change(symbol)
        
        # 检测信号依据（新增！）
        signal_basis, basis_reasons = self._detect_signal_basis(symbol, signal_type, change_24h)
        
        # 计算信号年龄
        signal_age = datetime.now() - signal_time
        signal_age_minutes = signal_age.total_seconds() / 60
        
        # 计算新鲜度（基于信号依据调整）
        if signal_basis == "CHASE":
            # 追涨信号，大幅降低新鲜度
            freshness, freshness_score = "EXPIRED", 20
        elif signal_basis == "CAUTION":
            freshness, freshness_score = "VALID", 50
        elif signal_basis == "DIP":
            # 抄底信号，提高新鲜度
            freshness, freshness_score = "FRESH", 90
        else:
            freshness, freshness_score = self._calculate_freshness(price_change_pct, signal_age_minutes)
        
        # 计算追涨风险（基于24h变化）
        chase_risk, chase_risk_score = self._calculate_chase_risk(change_24h)
        
        # 计算可操作性
        actionability = (freshness_score * 0.4 + chase_risk_score * 0.6)
        
        # 生成原因
        reasons = basis_reasons  # 使用信号依据原因
        
        reasons.append(f"")
        reasons.append(f"【价格数据】")
        reasons.append(f"  当前价格: ${current_price:.6f}")
        reasons.append(f"  24h变化: {change_24h*100:+.2f}%")
        reasons.append(f"  信号后变化: {price_change_pct*100:+.2f}%")
        
        reasons.append(f"")
        reasons.append(f"【时效评估】")
        reasons.append(f"  新鲜度: {freshness} ({freshness_score}分)")
        reasons.append(f"  追涨风险: {chase_risk}")
        
        # 生成建议（基于信号依据）
        if signal_basis == "CHASE":
            recommendation = "AVOID"
            reasons.append(f"")
            reasons.append(f"🚫 建议避免追涨，等待回调")
        elif signal_basis == "CAUTION":
            recommendation = "WAIT"
            reasons.append(f"")
            reasons.append(f"⏸️ 建议小仓位试探，大仓位等待")
        elif signal_basis == "DIP":
            recommendation = "ENTER"
            reasons.append(f"")
            reasons.append(f"✅ 可以考虑入场抄底")
        elif signal_basis == "LATE":
            recommendation = "HOLD"
            reasons.append(f"")
            reasons.append(f"🤷 卖出信号已晚，持有等待反弹")
        else:
            if freshness == "EXPIRED" or chase_risk == "DANGER":
                recommendation = "AVOID"
                reasons.append(f"")
                reasons.append(f"🚫 建议避免")
            elif freshness == "VALID" or chase_risk == "CAUTION":
                recommendation = "WAIT"
                reasons.append(f"")
                reasons.append(f"⏸️ 建议等待")
            else:
                recommendation = "ENTER"
                reasons.append(f"")
                reasons.append(f"✅ 可以考虑入场")
        
        return ProcessedSignal(
            symbol=symbol,
            signal_type=signal_type,
            signal_time=signal_time,
            signal_age_minutes=signal_age_minutes,
            current_price=current_price,
            price_at_signal=price_at_signal,
            price_change_pct=price_change_pct,
            change_24h=change_24h,
            signal_basis=signal_basis,
            freshness=freshness,
            freshness_score=freshness_score,
            chase_risk=chase_risk,
            chase_risk_score=chase_risk_score,
            actionability=actionability,
            recommendation=recommendation,
            reasons=reasons
        )
    
    def analyze_all(self, symbols: List[str] = None) -> List[ProcessedSignal]:
        """分析所有信号"""
        if symbols is None:
            symbols = ['SOL', 'XRP', 'DOGE', 'ETH', 'BTC', 'PEPE']
        
        results = []
        for symbol in symbols:
            result = self.process_signal(symbol)
            results.append(result)
        
        # 按可操作性排序
        results.sort(key=lambda x: x.actionability, reverse=True)
        
        return results
    
    def print_report(self, signals: List[ProcessedSignal] = None):
        """打印报告"""
        if signals is None:
            signals = self.analyze_all()
        
        print("\n" + "=" * 70)
        print("📊 信号前置处理报告")
        print("=" * 70)
        
        # 按信号依据分类
        fresh_signals = [s for s in signals if s.signal_basis in ["FRESH", "DIP"]]
        caution_signals = [s for s in signals if s.signal_basis in ["CAUTION"]]
        chase_signals = [s for s in signals if s.signal_basis in ["CHASE", "LATE"]]
        
        # 新鲜信号 / 抄底信号
        if fresh_signals:
            print("\n【🟢 新鲜信号 - 可考虑入场】")
            print("-" * 70)
            for s in fresh_signals:
                basis_text = "抄底机会" if s.signal_basis == "DIP" else "新鲜机会"
                print(f"\n  {s.symbol} ({s.signal_type}) - {basis_text}")
                for r in s.reasons:
                    if r:
                        print(f"    {r}")
        
        # 谨慎信号
        if caution_signals:
            print("\n【🟡 谨慎信号 - 需等待回调】")
            print("-" * 70)
            for s in caution_signals:
                print(f"\n  {s.symbol} ({s.signal_type})")
                for r in s.reasons:
                    if r:
                        print(f"    {r}")
        
        # 追涨信号 / 过期信号
        if chase_signals:
            print("\n【🔴 追涨信号 - 建议避免】")
            print("-" * 70)
            for s in chase_signals:
                basis_text = "卖出已晚" if s.signal_basis == "LATE" else "追涨风险"
                print(f"\n  {s.symbol} ({s.signal_type}) - {basis_text}")
                for r in s.reasons:
                    if r:
                        print(f"    {r}")
        
        # 推荐排序
        print("\n" + "=" * 70)
        print("📋 推荐排序（按可操作性）")
        print("=" * 70)
        for i, s in enumerate(signals, 1):
            action_emoji = "✅" if s.recommendation == "ENTER" else "⏸️" if s.recommendation == "WAIT" else "🚫"
            basis_emoji = "💰" if s.signal_basis == "DIP" else "⭐" if s.signal_basis == "FRESH" else "⚠️" if s.signal_basis == "CAUTION" else "🚨"
            print(f"  {i}. {s.symbol} | {action_emoji} {s.recommendation} | {basis_emoji} {s.signal_basis} | 评分: {s.actionability:.0f}")
        
        return signals

# ============================================================
# 主函数
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="信号前置处理器")
    parser.add_argument("symbol", nargs="?", default=None, help="指定币种")
    parser.add_argument("--all", action="store_true", help="分析所有信号")
    
    args = parser.parse_args()
    
    processor = SignalPreprocessor()
    
    if args.symbol:
        result = processor.process_signal(args.symbol.upper())
        processor.print_report([result])
    else:
        signals = processor.analyze_all()
        processor.print_report(signals)

if __name__ == "__main__":
    main()