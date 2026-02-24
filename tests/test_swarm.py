import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from swarm_agent import process_question

def test_swarm_agent():
    print("=" * 70)
    print("🐝 蜂群式Agent系统测试 - 真正使用LangChain + LangGraph")
    print("=" * 70)
    
    test_cases = [
        "我的APP登录不上去了，怎么办？",
        "帮我查一下ORD001这个订单的物流信息",
        "我想申请退款，请问流程是怎样的？",
        "无线蓝牙耳机多少钱？有什么功能？"
    ]
    
    for i, question in enumerate(test_cases, 1):
        print(f"\n{'=' * 70}")
        print(f"测试用例 {i}: {question}")
        print(f"{'=' * 70}")
        
        try:
            response = process_question(question)
            print(f"\n【最终回答】\n{response}")
        except Exception as e:
            print(f"\n【错误】发生异常: {str(e)}")
    
    print(f"\n{'=' * 70}")
    print("测试完成！")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    test_swarm_agent()
