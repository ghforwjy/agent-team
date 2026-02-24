
"""
测试新的通用Agent框架
验证BaseAgent、CoordinatorAgent、AgentConfig等核心组件
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from research_skills import search_market_info, search_technical_info
from agent_framework import (
    BaseAgent, AgentConfig, CoordinatorAgent, AgentOrchestrator, TaskAssignment
)


def test_base_agent():
    """测试BaseAgent基类"""
    print("\n" + "=" * 80)
    print("测试1: BaseAgent基类")
    print("=" * 80)
    
    test_agent = BaseAgent(
        name="test_agent",
        role="测试Agent",
        system_prompt="""你是一个测试助手。请简单回答问题。""",
        tools=[]
    )
    
    assert test_agent.name == "test_agent"
    assert test_agent.role == "测试Agent"
    assert hasattr(test_agent, 'system_prompt_full')
    
    print("✅ BaseAgent基类初始化成功")
    print(f"   Agent名称: {test_agent.name}")
    print(f"   Agent角色: {test_agent.role}")
    
    return test_agent


def test_agent_config():
    """测试AgentConfig配置类"""
    print("\n" + "=" * 80)
    print("测试2: AgentConfig配置类")
    print("=" * 80)
    
    config = AgentConfig(
        name="market_expert",
        role="市场专家",
        description="分析市场趋势",
        system_prompt="""你是市场专家。""",
        tools=[search_market_info]
    )
    
    assert config.name == "market_expert"
    assert config.role == "市场专家"
    assert len(config.tools) == 1
    
    print("✅ AgentConfig配置类创建成功")
    print(f"   配置名称: {config.name}")
    print(f"   配置角色: {config.role}")
    print(f"   可用工具: {[t.name for t in config.tools]}")
    
    agent = config.create_agent()
    assert isinstance(agent, BaseAgent)
    print("✅ 通过AgentConfig成功创建BaseAgent实例")
    
    return config


async def test_single_agent_with_tools():
    """测试单个Agent使用Skills工具"""
    print("\n" + "=" * 80)
    print("测试3: 单个Agent使用Skills工具")
    print("=" * 80)
    
    config = AgentConfig(
        name="tech_expert",
        role="技术专家",
        description="分析技术趋势",
        system_prompt="""你是一位技术专家。请根据参考数据进行分析。""",
        tools=[search_technical_info]
    )
    
    agent = config.create_agent()
    
    print("正在调用Agent...")
    result = await agent.ainvoke("请分析大模型技术的发展趋势")
    
    assert "output" in result
    print("✅ Agent调用成功")
    print(f"   输出长度: {len(result['output'])} 字符")
    print(f"   输出预览: {result['output'][:100]}...")
    
    return result


def test_task_assignment():
    """测试TaskAssignment任务分配类"""
    print("\n" + "=" * 80)
    print("测试4: TaskAssignment任务分配类")
    print("=" * 80)
    
    ta = TaskAssignment(
        agent_name="market_analyst",
        task_description="分析AI行业的市场规模",
        priority=1
    )
    
    assert ta.agent_name == "market_analyst"
    assert ta.priority == 1
    
    print("✅ TaskAssignment创建成功")
    print(f"   目标Agent: {ta.agent_name}")
    print(f"   任务描述: {ta.task_description}")
    print(f"   优先级: {ta.priority}")
    
    return ta


async def test_coordinator_agent():
    """测试CoordinatorAgent协调Agent"""
    print("\n" + "=" * 80)
    print("测试5: CoordinatorAgent协调Agent")
    print("=" * 80)
    
    expert_configs = {
        "market_analyst": AgentConfig(
            name="market_analyst",
            role="市场分析师",
            description="分析行业市场",
            system_prompt="""你是市场分析师。""",
            tools=[search_market_info]
        ),
        "tech_expert": AgentConfig(
            name="tech_expert",
            role="技术专家",
            description="分析技术趋势",
            system_prompt="""你是技术专家。""",
            tools=[search_technical_info]
        )
    }
    
    coordinator = CoordinatorAgent(
        available_agents=expert_configs,
        name="coordinator",
        role="协调员"
    )
    
    assert coordinator.name == "coordinator"
    assert len(coordinator.available_agents) == 2
    
    print("✅ CoordinatorAgent初始化成功")
    print(f"   可用专家数: {len(coordinator.available_agents)}")
    
    print("\n正在测试协调员分析需求...")
    task_assignments = await coordinator.analyze_and_assign(
        "请调研AI行业的市场前景和技术趋势"
    )
    
    print(f"✅ 协调员分配了 {len(task_assignments)} 个任务")
    for i, ta in enumerate(task_assignments, 1):
        print(f"   任务{i}: {ta.agent_name} - {ta.task_description[:50]}...")
    
    return coordinator, task_assignments


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("开始测试新的通用Agent框架")
    print("=" * 80)
    
    try:
        test_base_agent()
        test_agent_config()
        test_task_assignment()
        
        asyncio.run(test_single_agent_with_tools())
        asyncio.run(test_coordinator_agent())
        
        print("\n" + "=" * 80)
        print("🎉 所有测试通过！新的通用Agent框架工作正常！")
        print("=" * 80)
        print("\n核心功能验证:")
        print("  ✅ BaseAgent - 真正的通用Agent基类")
        print("  ✅ AgentConfig - 配置化实例化专家")
        print("  ✅ CoordinatorAgent - 真正的协调Agent")
        print("  ✅ Skills工具 - 支持工具调用")
        print("  ✅ 任务分配 - 通过大模型智能指派")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()

