#!/usr/bin/env python3
# =============================================================================
# 时效新闻保管库 - 全球战情室新闻暂存管理
# 功能：暂存新闻，每 2 日自动删除前 2 天的旧闻
# =============================================================================

import os
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# 配置
TEMP_NEWS_DIR = Path("/home/admin/Ziwei/data/warroom/temp_news")  # 时效新闻保管库
INTEL_DIR = Path("/home/admin/Ziwei/data/intel")  # 情报源目录
RETENTION_DAYS = 2  # 保留 2 天
CLEANUP_INTERVAL = 2  # 每 2 日清理一次

def ensure_directories():
    """确保目录存在"""
    TEMP_NEWS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✅ 时效新闻保管库：{TEMP_NEWS_DIR}")

def copy_news_to_temp():
    """将最新情报新闻复制到暂存库"""
    try:
        if not INTEL_DIR.exists():
            print(f"⚠️ 情报目录不存在：{INTEL_DIR}")
            return False
        
        # 获取最新的情报文件
        intel_files = sorted(INTEL_DIR.glob("intel_*.json"), reverse=True)
        
        if not intel_files:
            print("⚠️ 暂无情报文件")
            return False
        
        latest_intel = intel_files[0]
        print(f"📄 读取最新情报：{latest_intel.name}")
        
        # 读取情报数据
        with open(latest_intel, 'r', encoding='utf-8') as f:
            intel_data = json.load(f)
        
        # 提取新闻数据
        news_data = intel_data.get('news', {})
        timestamp = intel_data.get('timestamp', datetime.now().isoformat())
        
        # 生成暂存文件名（带日期）
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_file = TEMP_NEWS_DIR / f"news_{date_str}.json"
        
        # 保存新闻到暂存库
        temp_data = {
            'source_file': latest_intel.name,
            'timestamp': timestamp,
            'collected_at': datetime.now().isoformat(),
            'news': news_data,
            'total_items': sum(len(articles) for articles in news_data.values())
        }
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(temp_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 新闻已暂存：{temp_file.name}")
        print(f"   新闻总数：{temp_data['total_items']} 条")
        
        return True
    
    except Exception as e:
        print(f"❌ 暂存失败：{e}")
        return False

def cleanup_old_news():
    """清理 2 天前的旧闻"""
    try:
        if not TEMP_NEWS_DIR.exists():
            print("⚠️ 保管库不存在")
            return 0
        
        # 计算清理阈值（2 天前）
        cutoff_time = datetime.now() - timedelta(days=RETENTION_DAYS)
        
        deleted_count = 0
        kept_count = 0
        
        # 遍历所有暂存文件
        for temp_file in TEMP_NEWS_DIR.glob("news_*.json"):
            try:
                # 从文件名提取时间
                # 格式：news_YYYYMMDD_HHMMSS.json
                filename = temp_file.stem
                date_part = filename.split('_')[1]  # YYYYMMDD
                time_part = filename.split('_')[2]  # HHMMSS
                
                file_time = datetime.strptime(f"{date_part}_{time_part}", '%Y%m%d_%H%M%S')
                
                # 判断是否超过保留期限
                if file_time < cutoff_time:
                    # 删除旧文件
                    temp_file.unlink()
                    deleted_count += 1
                    print(f"🗑️  已删除：{temp_file.name} ({file_time.strftime('%Y-%m-%d %H:%M')})")
                else:
                    kept_count += 1
            
            except Exception as e:
                print(f"⚠️  处理文件失败 {temp_file.name}: {e}")
                continue
        
        print(f"\n📊 清理完成:")
        print(f"   删除旧闻：{deleted_count} 个文件")
        print(f"   保留新闻：{kept_count} 个文件")
        print(f"   清理阈值：{cutoff_time.strftime('%Y-%m-%d %H:%M')}")
        
        return deleted_count
    
    except Exception as e:
        print(f"❌ 清理失败：{e}")
        return 0

def get_temp_news_summary():
    """获取暂存新闻摘要"""
    try:
        if not TEMP_NEWS_DIR.exists():
            return {'error': '保管库不存在'}
        
        temp_files = sorted(TEMP_NEWS_DIR.glob("news_*.json"), reverse=True)
        
        summary = {
            'total_files': len(temp_files),
            'files': [],
            'total_news': 0
        }
        
        for temp_file in temp_files[:10]:  # 只显示最近 10 个文件
            try:
                with open(temp_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                summary['files'].append({
                    'filename': temp_file.name,
                    'timestamp': data.get('collected_at', 'N/A'),
                    'total_items': data.get('total_items', 0),
                    'sources': list(data.get('news', {}).keys())
                })
                summary['total_news'] += data.get('total_items', 0)
            
            except Exception as e:
                continue
        
        return summary
    
    except Exception as e:
        return {'error': str(e)}

def main():
    """主函数"""
    import sys
    
    print("=" * 70)
    print("📰 时效新闻保管库管理系统")
    print("=" * 70)
    print()
    
    ensure_directories()
    print()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'copy':
            # 复制新闻到暂存库
            print("📥 复制新闻到暂存库...")
            copy_news_to_temp()
        
        elif command == 'cleanup':
            # 清理旧闻
            print(f"🧹 清理 {RETENTION_DAYS} 天前的旧闻...")
            cleanup_old_news()
        
        elif command == 'summary':
            # 显示摘要
            print("📊 暂存新闻摘要...")
            summary = get_temp_news_summary()
            
            if 'error' in summary:
                print(f"❌ {summary['error']}")
            else:
                print(f"总文件数：{summary['total_files']}")
                print(f"总新闻数：{summary['total_news']}")
                print()
                for file_info in summary['files']:
                    print(f"📄 {file_info['filename']}")
                    print(f"   时间：{file_info['timestamp']}")
                    print(f"   新闻：{file_info['total_items']} 条")
                    print(f"   来源：{', '.join(file_info['sources'])}")
                    print()
        
        elif command == 'status':
            # 显示状态
            print("📊 保管库状态...")
            if TEMP_NEWS_DIR.exists():
                files = list(TEMP_NEWS_DIR.glob("news_*.json"))
                total_size = sum(f.stat().st_size for f in files)
                print(f"保管库位置：{TEMP_NEWS_DIR}")
                print(f"文件数量：{len(files)}")
                print(f"总大小：{total_size / 1024:.2f} KB")
            else:
                print("❌ 保管库不存在")
        
        else:
            print(f"❌ 未知命令：{command}")
            print("\n可用命令:")
            print("  copy    - 复制新闻到暂存库")
            print("  cleanup - 清理旧闻")
            print("  summary - 显示摘要")
            print("  status  - 显示状态")
    else:
        # 默认执行所有操作
        print("🔄 执行完整流程...")
        print()
        
        print("1️⃣ 复制新闻到暂存库")
        copy_news_to_temp()
        print()
        
        print("2️⃣ 清理旧闻")
        cleanup_old_news()
        print()
        
        print("3️⃣ 显示摘要")
        summary = get_temp_news_summary()
        if 'error' not in summary:
            print(f"总文件数：{summary['total_files']}")
            print(f"总新闻数：{summary['total_news']}")

if __name__ == '__main__':
    main()
