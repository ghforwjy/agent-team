# -*- coding: utf-8 -*-
"""
分析审计项和审计程序，找出包含制度要求的内容
"""
import sqlite3
import os

os.chdir(r'e:\mycode\agent-team')

def analyze_audit_items():
    conn = sqlite3.connect(r'tests\test_data\test_it_audit.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取所有审计项及其审计程序
    cursor.execute('''
        SELECT 
            ai.id,
            ai.item_code,
            ai.title,
            ai.description,
            ai.severity,
            ad.name as dimension_name,
            ap.procedure_text
        FROM audit_items ai
        JOIN audit_dimensions ad ON ai.dimension_id = ad.id
        LEFT JOIN audit_procedures ap ON ai.id = ap.item_id
        WHERE ai.status = 'active'
        ORDER BY ai.id
    ''')
    
    results = {}
    for row in cursor.fetchall():
        item_id = row['id']
        if item_id not in results:
            results[item_id] = {
                'item_code': row['item_code'],
                'title': row['title'],
                'description': row['description'],
                'severity': row['severity'],
                'dimension': row['dimension_name'],
                'procedures': []
            }
        if row['procedure_text']:
            results[item_id]['procedures'].append(row['procedure_text'])
    
    conn.close()
    return results

def main():
    items = analyze_audit_items()
    
    print(f"总计 {len(items)} 个审计项\n")
    
    # 输出前20个审计项的详细信息
    print("=" * 80)
    print("前20个审计项详情：")
    print("=" * 80)
    
    for i, (item_id, item) in enumerate(list(items.items())[:20], 1):
        print(f"\n【{i}】{item['item_code']}")
        print(f"维度: {item['dimension']}")
        print(f"标题: {item['title']}")
        if item['description']:
            print(f"描述: {item['description'][:100]}...")
        print(f"严重程度: {item['severity']}")
        print(f"审计程序数: {len(item['procedures'])}")
        
        for j, proc in enumerate(item['procedures'][:2], 1):  # 只显示前2个程序
            print(f"  程序{j}: {proc[:150]}...")
        
        if len(item['procedures']) > 2:
            print(f"  ... 还有 {len(item['procedures'])-2} 个程序")
    
    # 保存到文件供详细分析
    print("\n\n正在保存完整数据到文件...")
    with open(r'e:	emp_audit_items_analysis.txt', 'w', encoding='utf-8') as f:
        for item_id, item in items.items():
            f.write(f"\n{'='*80}\n")
            f.write(f"审计项: {item['item_code']}\n")
            f.write(f"维度: {item['dimension']}\n")
            f.write(f"标题: {item['title']}\n")
            f.write(f"描述: {item['description'] or '无'}\n")
            f.write(f"严重程度: {item['severity']}\n")
            f.write(f"审计程序:\n")
            for j, proc in enumerate(item['procedures'], 1):
                f.write(f"  {j}. {proc}\n")
    
    print(f"完整数据已保存到: e:\temp_audit_items_analysis.txt")

if __name__ == '__main__':
    main()
