#!/usr/bin/env python3
"""
紫微智控 - 本地监控脚本
负责监听任务文件夹，协调各岗位工作
"""

import os
import sys
import time
import yaml
from datetime import datetime
from pathlib import Path

# 路径配置
Ziwei_DIR = Path("/home/admin/Ziwei")
CONFIG_FILE = Ziwei_DIR / "config" / "agents.yaml"
HEALTH_DIR = Ziwei_DIR / "data" / "health"
TASKS_DIR = Ziwei_DIR / "data" / "tasks"
LOGS_DIR = Ziwei_DIR / "data" / "logs"

def load_config():
    """加载配置文件"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def update_heartbeat(message="系统正常运行"):
    """更新心跳文件"""
    heartbeat_file = HEALTH_DIR / "heartbeat.log"
    timestamp = datetime.now().isoformat()
    with open(heartbeat_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

def check_system_status():
    """检查系统状态"""
    status_file = Ziwei_DIR / "data" / "system_status.md"
    if status_file.exists():
        with open(status_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "BUSY" in content:
                return "BUSY"
            elif "EMERGENCY" in content:
                return "EMERGENCY"
    return "IDLE"

def scan_tasks():
    """扫描任务文件夹"""
    current_tasks = TASKS_DIR / "current"
    if not current_tasks.exists():
        return []
    
    tasks = []
    for task_file in current_tasks.glob("*.md"):
        tasks.append({
            'file': task_file,
            'name': task_file.stem,
            'created': datetime.fromtimestamp(task_file.stat().st_mtime)
        })
    return tasks

def main():
    """主循环"""
    print(f"[{datetime.now().isoformat()}] 紫微智控本地监控启动")
    print(f"工作目录：{Ziwei_DIR}")
    
    # 加载配置
    config = load_config()
    print(f"已加载 {len(config.get('agents', {}))} 个岗位配置")
    
    # 初始化心跳
    update_heartbeat("监控脚本启动")
    
    last_heartbeat = time.time()
    
    try:
        while True:
            # 每 30 秒更新心跳
            if time.time() - last_heartbeat > 30:
                status = check_system_status()
                update_heartbeat(f"系统状态：{status}")
                last_heartbeat = time.time()
            
            # 扫描任务
            tasks = scan_tasks()
            if tasks:
                print(f"[{datetime.now().isoformat()}] 发现 {len(tasks)} 个进行中任务")
                for task in tasks:
                    print(f"  - {task['name']}")
            
            # 休眠
            time.sleep(10)
    
    except KeyboardInterrupt:
        print("\n[系统] 收到停止信号，正常退出")
        update_heartbeat("监控脚本停止")
        sys.exit(0)

if __name__ == "__main__":
    main()
