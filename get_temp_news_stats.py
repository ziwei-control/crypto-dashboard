#!/usr/bin/env python3
# =============================================================================
# 时效新闻保管库 - Dashboard 数据接口
# =============================================================================

import json
from datetime import datetime, timedelta
from pathlib import Path

TEMP_NEWS_DIR = Path("/home/admin/Ziwei/data/warroom/temp_news")

def get_stats():
    """获取保管库统计信息"""
    try:
        if not TEMP_NEWS_DIR.exists():
            return {
                'status': 'error',
                'message': '保管库不存在'
            }
        
        # 获取所有文件
        temp_files = sorted(TEMP_NEWS_DIR.glob("news_*.json"), reverse=True)
        
        # 计算统计信息
        total_files = len(temp_files)
        total_news = 0
        total_size = 0
        sources = set()
        
        # 最新文件信息
        latest_file = None
        latest_time = None
        
        # 最早文件信息
        oldest_file = None
        oldest_time = None
        
        for temp_file in temp_files:
            try:
                # 文件大小
                total_size += temp_file.stat().st_size
                
                # 读取文件信息
                with open(temp_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 统计新闻数
                news_count = data.get('total_items', 0)
                total_news += news_count
                
                # 统计来源
                file_sources = data.get('news', {}).keys()
                sources.update(file_sources)
                
                # 最新文件
                collected_at = data.get('collected_at')
                if collected_at:
                    file_time = datetime.fromisoformat(collected_at)
                    
                    if latest_time is None or file_time > latest_time:
                        latest_time = file_time
                        latest_file = temp_file.name
                    
                    if oldest_time is None or file_time < oldest_time:
                        oldest_time = file_time
                        oldest_file = temp_file.name
            
            except Exception:
                continue
        
        # 计算清理阈值
        cutoff_time = datetime.now() - timedelta(days=2)
        
        return {
            'status': 'success',
            'total_files': total_files,
            'total_news': total_news,
            'total_size_kb': round(total_size / 1024, 2),
            'sources_count': len(sources),
            'sources': list(sources)[:10],  # 只显示前 10 个来源
            'latest_file': latest_file,
            'latest_time': latest_time.isoformat() if latest_time else None,
            'oldest_file': oldest_file,
            'oldest_time': oldest_time.isoformat() if oldest_time else None,
            'cutoff_time': cutoff_time.isoformat(),
            'retention_days': 2
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

if __name__ == '__main__':
    stats = get_stats()
    print(json.dumps(stats, ensure_ascii=False, indent=2))
