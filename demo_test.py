import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from swarm_agent import process_question

print("=" * 70)
print("🐝 蜂群式Agent系统 - 快速演示")
print("=" * 70)
print()

demo_questions = [
    "我的APP登录不上去了，怎么办？",
    "帮我查一下ORD001这个订单的物流信息",
    "我想申请退款，请问流程是怎样的？",
    "无线蓝牙耳机多少钱？有什么功能？"
]

for i, question in enumerate(demo_questions, 1):
    print(f"\n{'=' * 70}")
    print(f"演示问题 {i}: {question}")
    print(f"{'=' * 70}")
    
    try:
        response = process_question(question)
        print(f"\n【最终回答】\n{response}")
    except Exception as e:
        print(f"\n【错误】发生异常: {str(e)}")

print(f"\n{'=' * 70}")
print("演示完成！")
print(f"{'=' * 70}")
