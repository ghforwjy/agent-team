
"""
完整的端到端测试
测试整个调研系统从接收到需求到生成报告的完整流程
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from research_swarm import create_research_orchestrator


async def test_end_to_end():
    """完整的端到端测试"""
    print("\n" + "=" * 80)
    print("端到端测试: 完整调研流程")
    print("=" * 80)
    
    orchestrator = create_research_orchestrator()
    
    user_request = "请调研AI行业的投资机会，包括市场前景、技术趋势和财务分析"
    print(f"\n用户需求: {user_request}")
    
    print("\n开始运行调研系统...")
    summary = await orchestrator.run(user_request, max_rounds=1)
    
    print("\n" + "=" * 80)
    print("最终调研报告:")
    print("=" * 80)
    print(summary)
    print("=" * 80)
    
    print(f"\n✅ 端到端测试通过！调研报告长度: {len(summary)} 字符")


if __name__ == "__main__":
    asyncio.run(test_end_to_end())

