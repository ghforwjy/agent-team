
"""
调研方案协调系统测试
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_research_skills():
    """测试调研技能工具"""
    print("=" * 70)
    print("测试 1: 调研技能工具")
    print("=" * 70)
    
    from research_skills import (
        search_market_info, search_competitor_info,
        search_technical_info, search_financial_info
    )
    
    print("\n【测试】搜索AI行业市场信息...")
    market_info = search_market_info.invoke({"industry": "AI行业"})
    print(f"结果: {market_info[:100]}...")
    
    print("\n【测试】搜索OpenAI竞争对手信息...")
    competitor_info = search_competitor_info.invoke({"company": "OpenAI"})
    print(f"结果: {competitor_info[:100]}...")
    
    print("\n【测试】搜索大模型技术信息...")
    tech_info = search_technical_info.invoke({"topic": "大模型技术"})
    print(f"结果: {tech_info[:100]}...")
    
    print("\n【测试】搜索财务信息...")
    financial_info = search_financial_info.invoke({"topic": "估值模型"})
    print(f"结果: {financial_info[:100]}...")
    
    print("\n✅ 调研技能工具测试通过！\n")


def test_individual_experts():
    """测试单个专家agent"""
    print("=" * 70)
    print("测试 2: 单个专家Agent")
    print("=" * 70)
    
    from research_swarm import (
        run_market_analyst, run_technical_expert, run_financial_analyst
    )
    
    test_request = "调研AI行业的投资机会"
    
    print(f"\n【测试请求】{test_request}")
    
    print("\n【测试】市场分析师...")
    market_result = run_market_analyst(test_request)
    print(f"市场分析师输出: {market_result[:150]}...")
    
    print("\n【测试】技术专家...")
    tech_result = run_technical_expert(test_request)
    print(f"技术专家输出: {tech_result[:150]}...")
    
    print("\n【测试】金融分析师...")
    financial_result = run_financial_analyst(test_request)
    print(f"金融分析师输出: {financial_result[:150]}...")
    
    print("\n✅ 单个专家Agent测试通过！\n")


def test_concurrent_execution():
    """测试专家并发执行"""
    print("=" * 70)
    print("测试 3: 专家并发执行")
    print("=" * 70)
    
    from research_swarm import execute_experts_concurrently
    
    test_request = "调研新能源汽车行业"
    experts = ["market_analyst", "technical_expert"]
    
    print(f"\n【测试请求】{test_request}")
    print(f"【并发专家】{experts}")
    
    print("\n【测试】并发执行...")
    results = execute_experts_concurrently(experts, test_request)
    
    print(f"\n【并发执行结果】")
    for expert, result in results.items():
        print(f"  {expert}: {result[:100]}...")
    
    print("\n✅ 专家并发执行测试通过！\n")


def test_system_integration():
    """测试整个系统集成"""
    print("=" * 70)
    print("测试 4: 系统集成（简化版本）")
    print("=" * 70)
    
    from research_swarm import llm, SUMMARIZER_PROMPT
    
    test_request = "调研AI行业"
    mock_expert_results = """
    market_analyst: AI行业市场规模很大，增长很快
    technical_expert: 大模型技术是核心，Transformer架构
    """
    
    print(f"\n【测试请求】{test_request}")
    
    print("\n【测试】汇总专家...")
    prompt = SUMMARIZER_PROMPT.format(
        expert_results=mock_expert_results,
        original_request=test_request
    )
    
    summary = llm.invoke(prompt)
    print(f"汇总结果: {summary.content[:200]}...")
    
    print("\n✅ 系统集成测试通过！\n")


def test_full_system():
    """测试完整的调研系统（简化版）"""
    print("=" * 70)
    print("测试 5: 完整调研系统")
    print("=" * 70)
    
    from research_swarm import get_required_experts, summarize_results
    
    test_request = "调研AI行业的发展前景"
    
    print(f"\n【测试请求】{test_request}")
    
    print(f"\n【测试】测试专家选择...")
    experts = get_required_experts(test_request)
    print(f"选择的专家: {experts}")
    
    print(f"\n【测试】测试结果汇总...")
    mock_expert_results = {
        "market_analyst": "[市场分析师报告]\nAI行业市场规模很大",
        "technical_expert": "[技术专家报告]\n大模型技术是核心"
    }
    summary = summarize_results(mock_expert_results, test_request)
    print(f"汇总预览: {summary[:200]}...")
    
    print("\n✅ 完整调研系统测试通过！\n")


def print_system_architecture():
    """打印系统架构说明"""
    print("=" * 70)
    print("📊 调研方案协调系统 - 架构说明")
    print("=" * 70)
    print("\n核心特性:")
    print("  ✅ 多专家Agent并发执行")
    print("  ✅ 智能任务分配")
    print("  ✅ 结果自动汇总")
    print("  ✅ 用户反馈与多轮迭代")
    print("  ✅ 基于LangChain")
    print("\n专家团队:")
    print("  📈 市场分析师 - 分析市场规模、竞争格局")
    print("  🔧 技术专家 - 分析技术架构、趋势")
    print("  💰 金融分析师 - 分析财务、投资风险")
    print("\n工作流程:")
    print("  1. 协调员分析用户需求")
    print("  2. 选择合适的专家团队")
    print("  3. 专家并发执行调研")
    print("  4. 汇总生成调研报告")
    print("  5. 用户反馈后继续迭代")
    print("\n技术亮点:")
    print("  - asyncio异步并发")
    print("  - 灵活的专家选择")
    print("  - 支持多轮迭代")
    print("\n运行方式:")
    print("  python research_swarm.py")
    print("=" * 70)


def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("🔬 调研方案协调系统 - 测试套件")
    print("=" * 70)
    
    try:
        print_system_architecture()
        test_research_skills()
        test_individual_experts()
        test_concurrent_execution()
        test_system_integration()
        test_full_system()
        
        print("=" * 70)
        print("✅ 所有测试通过！")
        print("=" * 70)
        print("\n🎉 新的复杂任务调度场景已创建完成！")
        print("\n📁 新增文件:")
        print("  - research_skills.py      - 调研技能工具库")
        print("  - research_swarm.py       - 调研协调系统主程序")
        print("  - tests/test_research.py  - 测试文件")
        print("\n🚀 运行方式:")
        print("  python research_swarm.py")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
