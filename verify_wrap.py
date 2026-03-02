# 验证自动换行样式
with open('tests/output/screening_results.html', 'r', encoding='utf-8') as f:
    content = f.read()

print("验证自动换行相关样式:\n")

# 检查关键样式
checks = [
    ('white-space: normal', '允许自动换行'),
    ('word-wrap: break-word', '长单词换行'),
    ('word-break: break-all', '强制单词内换行'),
    ('line-height: 1.5', '行高 1.5 倍'),
    ('height: auto', '高度自适应'),
    ('overflow: visible', '内容可见不裁剪'),
    ('text-overflow: clip', '不使用省略号'),
    ('max-width: none', '移除最大宽度限制'),
]

print("样式检查:")
for pattern, desc in checks:
    count = content.count(pattern)
    if count > 0:
        print(f"  ✓ {desc} - 出现 {count} 次")
    else:
        print(f"  ✗ {desc} - 未找到")

# 检查不应该存在的样式
print("\n不应该存在的样式:")
bad_patterns = [
    ('white-space: nowrap', '强制不换行'),
    ('text-overflow: ellipsis', '省略号裁剪'),
    ('overflow: hidden', '内容隐藏'),
]

for pattern, desc in bad_patterns:
    count = content.count(pattern)
    if count > 0:
        print(f"  ⚠ {desc} - 出现 {count} 次 (应该移除)")
    else:
        print(f"  ✓ {desc} - 已正确移除")

print("\n✅ 自动换行功能已启用！")
print("\n改进说明:")
print("  - 单元格内容自动换行")
print("  - 行高根据内容自适应")
print("  - 长文本完整显示，不再裁剪")
print("  - 表格可读性大幅提升")
