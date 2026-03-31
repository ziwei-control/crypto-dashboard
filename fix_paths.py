#!/usr/bin/env python3
import os
import re

def fix_file(filepath):
    """修复单个文件的硬编码路径"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes = 0

        # 替换 sys.path.insert
        if "sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))" in content:
            content = content.replace(
                "sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))",
                "sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))"
            )
            changes += 1

        # 替换 BASE_DIR - 匹配多种写法
        patterns = [
            r'BASE_DIR\s*=\s*Path\(["\047]/home/admin/Ziwei["\047]\)',
            r'BASE_DIR\s*=\s*Path\(["\047]/home/admin/Ziwei["\047]\)',
            r"BASE_DIR = Path\('/home/admin/Ziwei'\)",
            r'BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))',
        ]

        for pattern in patterns:
            if re.search(pattern, content):
                content = re.sub(
                    pattern,
                    'BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))',
                    content
                )
                changes += 1
                break

        # 替换其他 /home/admin/Ziwei 路径
        content = re.sub(
            r'["\047]/home/admin/Ziwei/data',
            'BASE_DIR / "data"',
            content
        )

        # 替换 DATA_DIR 硬编码
        if 'DATA_DIR = Path(BASE_DIR / "data"")' in content:
            content = content.replace(
                'DATA_DIR = Path(BASE_DIR / "data"")',
                'DATA_DIR = BASE_DIR / "data"'
            )
            changes += 1

        if changes > 0 and content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes
        return False, 0
    except Exception as e:
        print(f"⚠️ 修复 {filepath} 时出错: {e}")
        return False, 0

# 修复所有 Python 文件
print("🔧 开始修复硬编码路径...")
fixed_count = 0
total_changes = 0

for filename in sorted(os.listdir('.')):
    if filename.endswith('.py'):
        fixed, changes = fix_file(filename)
        if fixed:
            fixed_count += 1
            total_changes += changes
            print(f"✅ 已修复: {filename} ({changes} 处修改)")

print(f"\n✅ 路径修复完成！总计修复 {fixed_count} 个文件，{total_changes} 处修改")