
"""
运行测试并保存输出到文件（带时间戳）
"""
import sys
import os
from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = os.path.join("tests", f"test_legal_finance_{timestamp}.log")

print(f"运行测试，输出将保存到: {output_file}")

original_stdout = sys.stdout

with open(output_file, 'w', encoding='utf-8') as f:
    sys.stdout = f
    
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from tests.test_legal_finance import run_all_tests
        run_all_tests()
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        sys.stdout = original_stdout

print(f"\n✅ 测试输出已保存到: {output_file}")

