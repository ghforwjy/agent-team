
"""
调研方案协调系统 - 使用真正的通用Agent框架
基于agent_framework.py的通用Agent基类
"""
import asyncio
from research_skills import (
    search_market_info, search_competitor_info,
    search_technical_info, search_financial_info
)
from agent_framework import (
    BaseAgent, AgentConfig, CoordinatorAgent, AgentOrchestrator
)


def create_expert_configs():
    """
    创建专家Agent配置
    通过配置实例化不同的专家Agent
    """
    MARKET_ANALYST_CONFIG = AgentConfig(
        name="market_analyst",
        role="市场分析师",
        description="负责分析行业市场、竞争格局、增长趋势等",
        system_prompt="""你是一位资深市场分析师。你的任务是分析行业市场、竞争格局、增长趋势等。
你可以使用以下工具获取数据：
- search_market_info(industry): 搜索行业市场信息
- search_competitor_info(company): 搜索竞争对手信息

请给出专业、详细、有数据支撑的分析报告。
请在回答开头明确说明：【市场分析师报告】
""",
        tools=[search_market_info, search_competitor_info]
    )

    TECHNICAL_EXPERT_CONFIG = AgentConfig(
        name="technical_expert",
        role="技术专家",
        description="负责分析技术架构、技术趋势、技术挑战等",
        system_prompt="""你是一位技术专家。你的任务是分析技术架构、技术趋势、技术挑战等。
你可以使用以下工具获取数据：
- search_technical_info(topic): 搜索技术相关信息

请给出专业、详细的技术分析报告。
请在回答开头明确说明：【技术专家报告】
""",
        tools=[search_technical_info]
    )

    FINANCIAL_ANALYST_CONFIG = AgentConfig(
        name="financial_analyst",
        role="金融分析师",
        description="负责分析财务模型、投资风险、估值方法等",
        system_prompt="""你是一位金融分析师。你的任务是分析财务模型、投资风险、估值方法等。
你可以使用以下工具获取数据：
- search_financial_info(topic): 搜索财务和投资相关信息

请给出专业、详细的财务分析报告。
请在回答开头明确说明：【金融分析师报告】
""",
        tools=[search_financial_info]
    )

    return {
        MARKET_ANALYST_CONFIG.name: MARKET_ANALYST_CONFIG,
        TECHNICAL_EXPERT_CONFIG.name: TECHNICAL_EXPERT_CONFIG,
        FINANCIAL_ANALYST_CONFIG.name: FINANCIAL_ANALYST_CONFIG
    }


def create_research_orchestrator():
    """
    创建调研编排器
    
    Returns:
        AgentOrchestrator实例
    """
    print("=" * 80)
    print("📊 初始化调研方案协调系统")
    print("=" * 80)
    print("\n技术特性:")
    print("  ✅ 真正的通用Agent框架 - BaseAgent基类")
    print("  ✅ 真正的协调Agent - CoordinatorAgent通过大模型智能指派")
    print("  ✅ 配置化实例化 - AgentConfig通过配置创建不同专家")
    print("  ✅ 支持Skills工具 - 每个专家Agent都可调用专业工具")
    print("  ✅ 多Agent并发执行 - asyncio异步并发")
    print("  ✅ 结果汇总与多轮迭代 - 支持用户反馈")
    print("=" * 80)
    
    expert_configs = create_expert_configs()
    
    print("\n专家团队配置:")
    for name, config in expert_configs.items():
        print(f"  🤖 {config.role}({name})")
        print(f"     - 描述: {config.description}")
        print(f"     - 可用工具: {[t.name for t in config.tools]}")
    print("=" * 80)
    
    coordinator = CoordinatorAgent(
        available_agents=expert_configs,
        name="coordinator",
        role="协调员"
    )
    
    orchestrator = AgentOrchestrator(
        coordinator=coordinator,
        agent_configs=expert_configs
    )
    
    return orchestrator


async def run_research_async(request, max_rounds=2):
    """
    异步运行调研系统
    
    Args:
        request: 用户调研需求
        max_rounds: 最大调研轮数
        
    Returns:
        调研报告
    """
    orchestrator = create_research_orchestrator()
    
    summary = await orchestrator.run(request, max_rounds)
    
    return summary


def run_research(request, max_rounds=2):
    """
    同步运行调研系统
    
    Args:
        request: 用户调研需求
        max_rounds: 最大调研轮数
        
    Returns:
        调研报告
    """
    return asyncio.run(run_research_async(request, max_rounds))


def interactive_research():
    """交互式调研系统"""
    print("\n" + "=" * 80)
    print("📋 调研方案协调系统 - 交互式模式")
    print("=" * 80)
    
    while True:
        print("\n请输入您的调研需求 (输入 'quit' 退出):")
        user_input = input("\n用户: ")
        
        if user_input.lower() in ['quit', 'exit', '退出']:
            print("\n感谢使用，再见！")
            break
        
        print("\n请输入最大调研轮数 (默认2轮):")
        try:
            max_rounds_input = input("轮数: ")
            max_rounds = int(max_rounds_input) if max_rounds_input.strip() else 2
        except:
            max_rounds = 2
        
        try:
            print(f"\n开始调研...")
            summary = run_research(user_input, max_rounds)
            
            print("\n" + "=" * 80)
            print("📋 调研报告")
            print("=" * 80)
            print(summary)
            print("=" * 80)
            
        except Exception as e:
            print(f"\n【错误】发生异常: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    interactive_research()

