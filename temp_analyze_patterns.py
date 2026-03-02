# -*- coding: utf-8 -*-
"""
分析审计程序中的制度要求模式
"""
import sqlite3
import re

conn = sqlite3.connect(r'e:\mycode\agent-team\tests\test_data\test_it_audit.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('''
    SELECT ai.item_code, ai.title, ap.procedure_text
    FROM audit_items ai
    LEFT JOIN audit_procedures ap ON ai.id = ap.item_id
    WHERE ai.status = 'active'
''')

# 定义制度要求的关键词模式
patterns = {
    '建立制度': [
        r'制定.*?(方案|制度|办法|规范|流程|规定)',
        r'建立.*?(制度|机制|体系|流程|规范)',
        r'是否.*?(有|建立|制定|完善).*?(制度|方案|办法)',
    ],
    '建立组织': [
        r'设立.*?(委员会|部门|岗位|小组|团队)',
        r'建立.*?(委员会|组织|部门)',
        r'设置.*?(岗位|部门|委员会)',
        r'是否.*?(设立|设置|建立).*?(岗位|部门|委员会)',
    ],
    '人员配备': [
        r'配备.*?(人员|员工|管理员)',
        r'不少于.*?\d+.*?(人|%|名)',
        r'至少.*?(\d+|一|两|三).*?(人|名|个)',
        r'具有.*?(资格|背景|经验|学历)',
        r'满足.*?(任职|资格|条件)',
    ],
    '定期执行': [
        r'每年.*?(一次|至少|开展|进行|评审|修订)',
        r'定期.*?(评审|检查|更新|修订|培训|演练)',
        r'至少.*?(每年|每季度|每月|每半年)',
        r'每(年|季度|月|半年).*?(一次|进行|开展)',
    ],
    '岗位分离': [
        r'分离',
        r'主备岗',
        r'相互制约',
        r'兼岗',
        r'职责.*?(分离|独立|清晰)',
    ],
    '文件保存': [
        r'保存.*?(\d+|一|二|三|五|十).*?(年|月|日)',
        r'至少保存',
        r'留存.*?(\d+|一|二|三|五|十).*?(年|月)',
    ],
}

results = {key: [] for key in patterns.keys()}
results['其他'] = []

for row in cursor.fetchall():
    title = row['title'] or ''
    procedure = row['procedure_text'] or ''
    text = title + ' ' + procedure
    
    matched = False
    for category, regex_list in patterns.items():
        for regex in regex_list:
            if re.search(regex, text):
                results[category].append({
                    'item_code': row['item_code'],
                    'title': title,
                    'procedure': procedure[:200] + '...' if len(procedure) > 200 else procedure
                })
                matched = True
                break
        if matched:
            break
    
    if not matched:
        results['其他'].append({
            'item_code': row['item_code'],
            'title': title,
            'procedure': procedure[:200] + '...' if len(procedure) > 200 else procedure
        })

conn.close()

# 输出统计
print("=" * 80)
print("制度要求类型统计")
print("=" * 80)
for category, items in results.items():
    print(f"{category}: {len(items)} 条")

# 输出每类的前3个示例
print("\n" + "=" * 80)
print("各类别示例（前3个）")
print("=" * 80)

for category, items in results.items():
    if items:
        print(f"\n【{category}】共 {len(items)} 条")
        for i, item in enumerate(items[:3], 1):
            print(f"\n  示例{i}: {item['item_code']}")
            print(f"  标题: {item['title']}")
            print(f"  程序: {item['procedure'][:150]}...")

# 保存完整结果
output_file = r'e:\mycode\agent-team\temp_audit_analysis_result.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("制度要求提取分析结果\n")
    f.write("=" * 80 + "\n\n")
    
    for category, items in results.items():
        f.write(f"\n{'='*80}\n")
        f.write(f"【{category}】共 {len(items)} 条\n")
        f.write(f"{'='*80}\n")
        
        for i, item in enumerate(items, 1):
            f.write(f"\n{i}. {item['item_code']}\n")
            f.write(f"   标题: {item['title']}\n")
            f.write(f"   程序: {item['procedure']}\n")

print(f"\n\n完整分析结果已保存到: {output_file}")
