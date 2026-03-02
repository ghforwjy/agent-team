import sqlite3

# 检查测试数据库中的重复记录
db_path = 'tests/test_data/test_it_audit.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 查找相似度完全相同的记录
print("查找相似度完全相同的记录:\n")
cursor.execute('''
    SELECT item_code, item_title, dimension_name, requirement_type, 
           vector_similarity, confidence, screening_status,
           procedure_text
    FROM policy_screening_results
    WHERE vector_similarity = 0.4506
    ORDER BY item_code
''')

rows = cursor.fetchall()
print(f"找到 {len(rows)} 条相似度为 0.4506 的记录:\n")

for i, row in enumerate(rows, 1):
    print(f"{i}. 编码：{row['item_code']}")
    print(f"   标题：{row['item_title'][:50]}...")
    print(f"   维度：{row['dimension_name']}")
    print(f"   类型：{row['requirement_type']}")
    print(f"   相似度：{row['vector_similarity']}")
    print(f"   置信度：{row['confidence']}")
    print(f"   状态：{row['screening_status']}")
    print(f"   程序：{row['procedure_text'][:50]}...")
    print()

# 检查是否是同一个审计项的不同程序
print("\n\n检查审计项详情:")
cursor.execute('''
    SELECT ai.id, ai.item_code, ai.title, ad.name as dimension
    FROM audit_items ai
    JOIN audit_dimensions ad ON ai.dimension_id = ad.id
    WHERE ai.item_code IN ('NEW-20260302153258-M075', 'NEW-20260302153300-M132')
    ORDER BY ai.id
''')

items = cursor.fetchall()
for item in items:
    print(f"\n审计项：{item['item_code']}")
    print(f"  标题：{item['title']}")
    print(f"  维度：{item['dimension']}")
    
    # 查询该审计项的所有程序
    cursor.execute('''
        SELECT id, procedure_text, is_primary
        FROM audit_procedures
        WHERE item_id = ?
    ''', (item['id'],))
    
    procedures = cursor.fetchall()
    print(f"  程序数：{len(procedures)}")
    for proc in procedures:
        print(f"    - [{proc['id']}] {proc['procedure_text'][:60]}...")

conn.close()
