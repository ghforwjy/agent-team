
"""
法律财务专家协调系统 - 使用模块化的Agent定义
每个Agent都有独立的定义文件，放在 agents/ 目录下
"""
import asyncio
from agent_framework import CoordinatorAgent, AgentOrchestrator
from agents import LEGAL_EXPERT_CONFIG, FINANCE_EXPERT_CONFIG


def create_expert_configs():
    """
    创建法律财务专家Agent配置
    从 agents 模块加载独立定义的 Agent 配置
    """
    return {
        LEGAL_EXPERT_CONFIG.name: LEGAL_EXPERT_CONFIG,
        FINANCE_EXPERT_CONFIG.name: FINANCE_EXPERT_CONFIG
    }


def create_legal_finance_orchestrator():
    """
    创建法律财务编排器
    
    Returns:
        AgentOrchestrator实例
    """
    print("=" * 80)
    print("初始化法律财务专家协调系统")
    print("=" * 80)
    print("\n技术特性:")
    print("  - 真正的通用Agent框架 - BaseAgent基类")
    print("  - 真正的协调Agent - CoordinatorAgent通过大模型智能指派")
    print("  - 配置化实例化 - AgentConfig通过配置创建不同专家")
    print("  - 支持Skills工具 - 每个专家Agent都可调用专业工具")
    print("  - 多Agent并发执行 - asyncio异步并发")
    print("  - 模块化Agent定义 - 每个Agent独立文件，便于管理")
    print("=" * 80)
    
    expert_configs = create_expert_configs()
    
    print("\n专家团队配置:")
    for name, config in expert_configs.items():
        print(f"  {config.role}({name})")
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


async def run_legal_finance_async(request, max_rounds=2):
    """
    异步运行法律财务专家系统
    
    Args:
        request: 用户需求
        max_rounds: 最大轮数
        
    Returns:
        分析报告
    """
    orchestrator = create_legal_finance_orchestrator()
    
    summary = await orchestrator.run(request, max_rounds)
    
    return summary


def run_legal_finance(request, max_rounds=2):
    """
    同步运行法律财务专家系统
    
    Args:
        request: 用户需求
        max_rounds: 最大轮数
        
    Returns:
        分析报告
    """
    return asyncio.run(run_legal_finance_async(request, max_rounds))


def interactive_legal_finance():
    """交互式法律财务专家系统"""
    print("\n" + "=" * 80)
    print("法律财务专家协调系统 - 交互式模式")
    print("=" * 80)
    
    while True:
        print("\n请输入您的需求 (输入 'quit' 退出):")
        user_input = input("\n用户: ")
        
        if user_input.lower() in ['quit', 'exit', '退出']:
            print("\n感谢使用，再见！")
            break
        
        print("\n请输入最大分析轮数 (默认2轮):")
        try:
            max_rounds_input = input("轮数: ")
            max_rounds = int(max_rounds_input) if max_rounds_input.strip() else 2
        except:
            max_rounds = 2
        
        try:
            print(f"\n开始分析...")
            summary = run_legal_finance(user_input, max_rounds)
            
            print("\n" + "=" * 80)
            print("分析报告")
            print("=" * 80)
            print(summary)
            print("=" * 80)
            
        except Exception as e:
            print(f"\n【错误】发生异常: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    interactive_legal_finance()
