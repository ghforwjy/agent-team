
"""
运行法律财务专家Agent（使用协调员和编排器）并保存完整报告
"""
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from legal_finance_swarm import run_legal_finance


def save_full_report(request, result, timestamp, index=None):
    """保存完整报告到带时间戳的文件"""
    if index:
        filename = os.path.join("tests", f"report_{index}_{timestamp}.txt")
    else:
        filename = os.path.join("tests", f"full_report_{timestamp}.txt")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("法律财务专家完整报告（协调员+编排器）\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"用户请求:\n{request}\n\n")
        f.write("=" * 80 + "\n")
        f.write("专家分析报告:\n")
        f.write("=" * 80 + "\n")
        f.write(result + "\n")
    
    print(f"\n✅ 完整报告已保存到: {filename}")
    print(f"   报告长度: {len(result)} 字符")
    
    return filename


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("=" * 80)
    print("法律财务专家Agent - 使用协调员+编排器")
    print("=" * 80)
    
    test_requests = [
        "请审查一份供应商合同的关键条款，并给出风险评估和修订建议",
        "请生成一份利润表的标准格式，并说明各个主要科目的含义"
    ]
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n{'=' * 80}")
        print(f"测试请求 {i}")
        print(f"{'=' * 80}")
        print(f"\n请求内容: {request}")
        
        try:
            result = run_legal_finance(request, max_rounds=1)
            
            save_full_report(request, result, timestamp, index=i)
            
        except Exception as e:
            print(f"\n❌ 运行失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✅ 所有完整报告已保存成功！")
    print("=" * 80)


if __name__ == "__main__":
    main()

