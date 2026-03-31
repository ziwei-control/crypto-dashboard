#!/usr/bin/env python3
"""
CoPaw 主动监控器 - Proactive Monitor
让 AI 主动检查、主动通知、主动总结

作者: CoPaw AI 助手
版本: 1.0
"""

import os
import sys
import json
import time
import psutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

# ============================================================================
# 配置
# ============================================================================

CONFIG = {
    # 阈值设置
    "thresholds": {
        "cpu_percent": 80,      # CPU使用率警告阈值
        "memory_percent": 90,   # 内存使用率警告阈值
        "disk_percent": 85,     # 磁盘使用率警告阈值
    },
    
    # 监控的服务
    "services": [
        "copaw.service",
        "docker.service",
        "nginx.service",
    ],
    
    # 监控的日志文件
    "log_files": [
        "/var/log/syslog",
        "/var/log/nginx/error.log",
    ],
    
    # 异常关键词
    "error_keywords": [
        "error", "fatal", "critical", "exception",
        "failed", "timeout", "connection refused"
    ],
    
    # 监控的定时任务
    "cron_tasks": {
        "gem_hunter": {
            "pattern": "run_gem_hunter",
            "expected_interval_minutes": 5,
            "log_file": "/tmp/gem_hunter.log",
        }
    },
    
    # 输出
    "output_dir": "/home/admin/Ziwei/data/proactive",
    "report_file": "/home/admin/Ziwei/data/proactive/heartbeat_report.json",
}


class ProactiveMonitor:
    """主动监控器"""
    
    def __init__(self):
        self.output_dir = Path(CONFIG['output_dir'])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.alerts = []
        self.info = []
        self.timestamp = datetime.now()
    
    def log(self, msg: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {msg}")
        
        if level == "ALERT":
            self.alerts.append(f"[{timestamp}] {msg}")
        else:
            self.info.append(f"[{timestamp}] {msg}")
    
    def check_services(self) -> Dict:
        """检查服务状态"""
        self.log("🔍 检查服务状态...")
        results = {}
        
        for service in CONFIG['services']:
            try:
                result = subprocess.run(
                    ['systemctl', 'is-active', service],
                    capture_output=True, text=True, timeout=5
                )
                status = result.stdout.strip()
                results[service] = status
                
                if status != 'active':
                    self.log(f"⚠️ {service} 状态异常: {status}", "ALERT")
                else:
                    self.log(f"✅ {service}: {status}")
                    
            except Exception as e:
                results[service] = f"检查失败: {e}"
                self.log(f"❌ {service} 检查失败: {e}", "ALERT")
        
        return results
    
    def check_resources(self) -> Dict:
        """检查系统资源"""
        self.log("🔍 检查系统资源...")
        results = {}
        
        # CPU
        cpu = psutil.cpu_percent(interval=1)
        results['cpu_percent'] = cpu
        if cpu > CONFIG['thresholds']['cpu_percent']:
            self.log(f"⚠️ CPU 使用率过高: {cpu}%", "ALERT")
        else:
            self.log(f"✅ CPU: {cpu}%")
        
        # 内存
        memory = psutil.virtual_memory()
        results['memory_percent'] = memory.percent
        results['memory_used_gb'] = round(memory.used / (1024**3), 2)
        results['memory_total_gb'] = round(memory.total / (1024**3), 2)
        
        if memory.percent > CONFIG['thresholds']['memory_percent']:
            self.log(f"⚠️ 内存使用率过高: {memory.percent}%", "ALERT")
        else:
            self.log(f"✅ 内存: {memory.percent}% ({results['memory_used_gb']}/{results['memory_total_gb']}GB)")
        
        # 磁盘
        disk = psutil.disk_usage('/')
        results['disk_percent'] = disk.percent
        results['disk_used_gb'] = round(disk.used / (1024**3), 2)
        results['disk_total_gb'] = round(disk.total / (1024**3), 2)
        
        if disk.percent > CONFIG['thresholds']['disk_percent']:
            self.log(f"⚠️ 磁盘使用率过高: {disk.percent}%", "ALERT")
        else:
            self.log(f"✅ 磁盘: {disk.percent}% ({results['disk_used_gb']}/{results['disk_total_gb']}GB)")
        
        return results
    
    def check_logs(self) -> Dict:
        """检查日志异常"""
        self.log("🔍 检查日志异常...")
        results = {'errors': []}
        
        for log_file in CONFIG['log_files']:
            if not os.path.exists(log_file):
                continue
            
            try:
                # 只检查最近100行
                result = subprocess.run(
                    ['tail', '-100', log_file],
                    capture_output=True, text=True, timeout=5
                )
                lines = result.stdout.lower()
                
                for keyword in CONFIG['error_keywords']:
                    if keyword in lines:
                        count = lines.count(keyword)
                        results['errors'].append({
                            'file': log_file,
                            'keyword': keyword,
                            'count': count
                        })
                        self.log(f"⚠️ {log_file} 发现 {count} 个 '{keyword}'", "ALERT")
                        
            except Exception as e:
                self.log(f"检查 {log_file} 失败: {e}")
        
        if not results['errors']:
            self.log("✅ 日志正常，无异常关键词")
        
        return results
    
    def check_cron_tasks(self) -> Dict:
        """检查定时任务"""
        self.log("🔍 检查定时任务...")
        results = {}
        
        for task_name, task_config in CONFIG['cron_tasks'].items():
            log_file = task_config['log_file']
            expected_interval = task_config['expected_interval_minutes']
            
            if not os.path.exists(log_file):
                results[task_name] = "日志文件不存在"
                self.log(f"⚠️ {task_name}: 日志文件不存在", "ALERT")
                continue
            
            try:
                # 获取日志文件最后修改时间
                mtime = os.path.getmtime(log_file)
                last_run = datetime.fromtimestamp(mtime)
                minutes_ago = (datetime.now() - last_run).total_seconds() / 60
                
                results[task_name] = {
                    'last_run': last_run.isoformat(),
                    'minutes_ago': round(minutes_ago, 1),
                }
                
                # 如果超过预期间隔的2倍，警告
                if minutes_ago > expected_interval * 2:
                    self.log(f"⚠️ {task_name} 可能停止运行，上次运行: {minutes_ago:.0f}分钟前", "ALERT")
                else:
                    self.log(f"✅ {task_name}: 上次运行 {minutes_ago:.1f}分钟前")
                    
            except Exception as e:
                results[task_name] = f"检查失败: {e}"
                self.log(f"❌ {task_name} 检查失败: {e}")
        
        return results
    
    def check_profits(self) -> Dict:
        """检查收益/交易状态"""
        self.log("🔍 检查收益状态...")
        results = {}
        
        # 检查早期币挖掘器结果
        latest_gems = "/home/admin/Ziwei/products/meme-monitor/data/latest_gems.json"
        if os.path.exists(latest_gems):
            try:
                with open(latest_gems) as f:
                    data = json.load(f)
                results['gems_found'] = data.get('summary', {}).get('total_gems', 0)
                results['last_scan'] = data.get('timestamp', 'Unknown')
                self.log(f"✅ 早期币挖掘器: 发现 {results['gems_found']} 个早期币")
            except Exception as e:
                results['error'] = str(e)
        
        return results
    
    def generate_report(self) -> Dict:
        """生成完整报告"""
        report = {
            'timestamp': self.timestamp.isoformat(),
            'status': 'ALERT' if self.alerts else 'OK',
            'alerts': self.alerts,
            'info': self.info,
            'details': {
                'services': self.check_services(),
                'resources': self.check_resources(),
                'logs': self.check_logs(),
                'cron_tasks': self.check_cron_tasks(),
                'profits': self.check_profits(),
            }
        }
        
        # 保存报告
        with open(CONFIG['report_file'], 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        return report
    
    def notify_if_needed(self, report: Dict):
        """如果有警告，发送通知"""
        if not self.alerts:
            return
        
        # 构建通知内容
        alert_msg = "\n".join(self.alerts[:5])  # 最多5条
        
        print(f"\n{'='*50}")
        print(f"🚨 发现 {len(self.alerts)} 个警告!")
        print(f"{'='*50}")
        print(alert_msg)
        print(f"{'='*50}\n")
        
        # TODO: 发送钉钉通知
        # 目前只打印，后续可以接入钉钉webhook
    
    def run(self):
        """执行监控"""
        print("\n" + "="*60)
        print(f"🫀 CoPaw 主动监控 - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")
        
        report = self.generate_report()
        self.notify_if_needed(report)
        
        print(f"\n{'='*60}")
        print(f"✅ 监控完成 | 状态: {report['status']} | 警告: {len(self.alerts)}")
        print(f"{'='*60}\n")
        
        return report


def main():
    monitor = ProactiveMonitor()
    report = monitor.run()
    
    # 返回状态码
    sys.exit(0 if report['status'] == 'OK' else 1)


if __name__ == "__main__":
    main()