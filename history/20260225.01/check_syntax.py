
"""
简单的语法检查脚本
"""
import ast
import sys

try:
    with open('research_swarm.py', 'r', encoding='utf-8') as f:
        source = f.read()
    
    ast.parse(source)
    print("✅ 语法检查通过！")
except SyntaxError as e:
    print(f"❌ 语法错误: {e}")
    print(f"   位置: 行 {e.lineno}, 列 {e.offset}")
    print(f"   内容: {e.text}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 其他错误: {e}")
    sys.exit(1)
