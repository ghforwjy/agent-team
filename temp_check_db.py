# -*- coding: utf-8 -*-
import sqlite3
import os

# 检查测试数据库
test_db = r'e:\mycode\agent-team\tests\test_data\test_it_audit.db'
if os.path.exists(test_db):
    print(f'=== 测试数据库: {test_db} ===')
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print('\n--- audit_dimensions ---')
    try:
        cursor.execute('SELECT id, code, name FROM audit_dimensions LIMIT 10')
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"  {row['id']}: {row['code']} - {row['name']}")
        else:
            print('  (空表)')
    except Exception as e:
        print(f'  错误: {e}')
    
    print('\n--- audit_items 统计 ---')
    try:
        cursor.execute('SELECT COUNT(*) as cnt FROM audit_items')
        print(f"  审计项数: {cursor.fetchone()['cnt']}")
    except Exception as e:
        print(f'  错误: {e}')
    
    conn.close()
else:
    print(f'测试数据库不存在: {test_db}')

# 检查主数据库
main_db = r'e:\mycode\agent-team\knowledge-work-plugins\it-audit\data\it_audit.db'
print(f'\n=== 主数据库: {main_db} ===')
if os.path.exists(main_db):
    conn = sqlite3.connect(main_db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print('\n--- audit_dimensions ---')
    try:
        cursor.execute('SELECT id, code, name FROM audit_dimensions LIMIT 10')
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"  {row['id']}: {row['code']} - {row['name']}")
        else:
            print('  (空表)')
    except Exception as e:
        print(f'  错误: {e}')
    
    print('\n--- audit_items 统计 ---')
    try:
        cursor.execute('SELECT COUNT(*) as cnt FROM audit_items')
        print(f"  审计项数: {cursor.fetchone()['cnt']}")
    except Exception as e:
        print(f'  错误: {e}')
    
    conn.close()
else:
    print(f'主数据库不存在: {main_db}')
