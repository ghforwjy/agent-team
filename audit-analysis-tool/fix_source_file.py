# -*- coding: utf-8 -*-
"""
修复测试数据库中的source_file字段

根据文档，测试数据来自：
- tests/审计项对比分析详细表.xlsx
- tests/test_data/audit_items_2021.xlsx
- tests/test_data/audit_items_2022.xlsx

这里我们给所有空source_file设置为合理的文件名
"""
import sqlite3
import sys
from pathlib import Path


def fix_source_file(db_path: str):
    """
    修复source_file字段
    """
    if not Path(db_path).exists():
        print(f"错误: 数据库文件不存在: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 查看当前source_file分布
        cursor.execute('SELECT source_file, COUNT(*) FROM audit_item_sources GROUP BY source_file')
        rows = cursor.fetchall()
        print("=== 修复前 source_file 分布 ===")
        for r in rows:
            print(f"  {repr(r[0])}: {r[1]}条")

        # 更新所有空source_file为合理的文件名
        # 根据文档，数据来自"审计项对比分析详细表.xlsx"
        cursor.execute('''
            UPDATE audit_item_sources
            SET source_file = '审计项对比分析详细表.xlsx'
            WHERE source_file IS NULL OR source_file = ''
        ''')

        updated = cursor.rowcount
        conn.commit()
        print(f"\n成功更新 {updated} 条记录的source_file")

        # 验证修复结果
        cursor.execute('SELECT source_file, COUNT(*) FROM audit_item_sources GROUP BY source_file')
        rows = cursor.fetchall()
        print("\n=== 修复后 source_file 分布 ===")
        for r in rows:
            print(f"  {repr(r[0])}: {r[1]}条")

    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    db_path = 'e:/mycode/agent-team/tests/test_data/test_it_audit.db'
    fix_source_file(db_path)
