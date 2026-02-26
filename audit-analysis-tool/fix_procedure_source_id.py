# -*- coding: utf-8 -*-
"""
修复审计程序的source_id字段

将每个审计程序的source_id设置为对应审计项的第一个来源的ID
"""
import sqlite3
import sys
from pathlib import Path


def fix_procedure_source_id(db_path: str):
    """
    修复审计程序的source_id

    Args:
        db_path: 数据库文件路径
    """
    if not Path(db_path).exists():
        print(f"错误: 数据库文件不存在: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 获取每个审计项的第一个来源ID
        cursor.execute('''
            SELECT item_id, MIN(id) as first_source_id
            FROM audit_item_sources
            GROUP BY item_id
        ''')
        item_source_map = {row[0]: row[1] for row in cursor.fetchall()}
        print(f"找到 {len(item_source_map)} 个审计项的来源映射")

        # 获取所有审计程序
        cursor.execute('SELECT id, item_id, source_id FROM audit_procedures')
        procedures = cursor.fetchall()
        print(f"共有 {len(procedures)} 个审计程序")

        # 统计需要修复的程序数
        need_fix = sum(1 for p in procedures if p[2] is None)
        print(f"需要修复的程序数: {need_fix}")

        # 修复source_id为NULL的审计程序
        updated = 0
        for proc_id, item_id, source_id in procedures:
            if source_id is None and item_id in item_source_map:
                cursor.execute('''
                    UPDATE audit_procedures
                    SET source_id = ?
                    WHERE id = ?
                ''', (item_source_map[item_id], proc_id))
                updated += 1

        conn.commit()
        print(f"成功修复 {updated} 个审计程序的source_id")

        # 验证修复结果
        cursor.execute('SELECT COUNT(*), COUNT(source_id) FROM audit_procedures')
        total, with_source = cursor.fetchall()[0]
        print(f"修复后: 总程序数={total}, 有source_id的程序数={with_source}")

    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    db_path = 'e:/mycode/agent-team/tests/test_data/test_it_audit.db'
    fix_procedure_source_id(db_path)
