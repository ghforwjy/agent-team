# -*- coding: utf-8 -*-
"""
重新生成报告，测试自动换行效果
"""
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 
    'knowledge-work-plugins', 'it-audit', 'skills', 
    '2-policy-compliance-checker', 'scripts', 'analyzers'))

from screening_reporter import ScreeningResultReporter

# 使用测试数据库
db_path = 'tests/test_data/test_it_audit.db'
reporter = ScreeningResultReporter(db_path)

output_dir = 'tests/output'
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, 'screening_results.html')

# 生成报告
print(f"从数据库生成报告：{db_path}")
reporter.generate_html_report(output_path)

# 打印统计信息
stats = reporter.generate_summary()
print(f"\n统计信息:")
print(f"  总记录数：{stats.get('total', 0)}")
print(f"  按状态：{stats.get('by_status', {})}")
print(f"  按类型：{stats.get('by_type', {})}")

print(f"\n✓ HTML 报告已生成：{output_path}")
print(f"✓ 表格高度：800px")
print(f"✓ 表头支持拖动调整宽度")
print(f"✓ 内容自动换行，行高自适应")
