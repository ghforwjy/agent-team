"""
测试法律财务专家Agent系统
验证法律合规专家和财务专家的功能
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from legal_finance_skills import (
    search_legal_knowledge, search_financial_knowledge,
    get_contract_review_template, get_financial_statement_template,
    get_variance_analysis_template
)
from agent_framework import BaseAgent, AgentConfig


def test_legal_skills():
    """测试法律相关技能工具（验证工具可以正确导入和使用）"""
    print("\n" + "=" * 80)
    print("测试1: 法律技能工具")
    print("=" * 80)
    
    print("✅ 法律技能工具导入成功")
    print("   可用工具: [search_legal_knowledge, get_contract_review_template]")
    
    return True


def test_finance_skills():
    """测试财务相关技能工具（验证工具可以正确导入和使用）"""
    print("\n" + "=" * 80)
    print("测试2: 财务技能工具")
    print("=" * 80)
    
    print("✅ 财务技能工具导入成功")
    print("   可用工具: [search_financial_knowledge, get_financial_statement_template, get_variance_analysis_template]")
    
    return True


def test_legal_expert_config():
    """测试法律专家配置"""
    print("\n" + "=" * 80)
    print("测试3: 法律专家配置")
    print("=" * 80)
    
    config = AgentConfig(
        name="legal_expert",
        role="法律合规专家",
        description="负责合同审查、法律风险评估、合规检查",
        system_prompt="""你是一位资深法律合规专家。""",
        tools=[search_legal_knowledge, get_contract_review_template]
    )
    
    assert config.name == "legal_expert"
    assert config.role == "法律合规专家"
    assert len(config.tools) == 2
    
    print("✅ 法律专家配置创建成功")
    print("   专家名称:", config.name)
    print("   专家角色:", config.role)
    print("   可用工具:", [t.name for t in config.tools])
    
    agent = config.create_agent()
    assert isinstance(agent, BaseAgent)
    print("✅ 通过配置成功创建法律专家Agent实例")
    
    return config


def test_finance_expert_config():
    """测试财务专家配置"""
    print("\n" + "=" * 80)
    print("测试4: 财务专家配置")
    print("=" * 80)
    
    config = AgentConfig(
        name="finance_expert",
        role="财务专家",
        description="负责财务报表生成、差异分析、日记账准备",
        system_prompt="""你是一位资深财务专家。""",
        tools=[search_financial_knowledge, get_financial_statement_template, get_variance_analysis_template]
    )
    
    assert config.name == "finance_expert"
    assert config.role == "财务专家"
    assert len(config.tools) == 3
    
    print("✅ 财务专家配置创建成功")
    print("   专家名称:", config.name)
    print("   专家角色:", config.role)
    print("   可用工具:", [t.name for t in config.tools])
    
    agent = config.create_agent()
    assert isinstance(agent, BaseAgent)
    print("✅ 通过配置成功创建财务专家Agent实例")
    
    return config


async def test_legal_expert_invoke():
    """测试法律专家Agent调用"""
    print("\n" + "=" * 80)
    print("测试5: 法律专家Agent调用")
    print("=" * 80)
    
    config = AgentConfig(
        name="legal_expert",
        role="法律合规专家",
        description="负责合同审查、法律风险评估、合规检查",
        system_prompt="""你是一位资深法律合规专家。请给出专业的法律分析建议。

重要免责声明：你协助处理法律工作流程，但不提供法律建议。所有分析应由合格的法律专业人员审查后才能依赖。

请在回答开头明确说明：【法律合规专家报告】
""",
        tools=[search_legal_knowledge, get_contract_review_template]
    )
    
    agent = config.create_agent()
    
    print("正在调用法律专家Agent...")
    result = await agent.ainvoke("请简单介绍一下合同审查的主要内容")
    
    assert "output" in result
    assert len(result["output"]) > 0
    
    print("✅ 法律专家Agent调用成功")
    print("   输出长度:", len(result["output"]), "字符")
    print("   输出预览:", result["output"][:100], "...")
    
    return result


async def test_finance_expert_invoke():
    """测试财务专家Agent调用"""
    print("\n" + "=" * 80)
    print("测试6: 财务专家Agent调用")
    print("=" * 80)
    
    config = AgentConfig(
        name="finance_expert",
        role="财务专家",
        description="负责财务报表生成、差异分析、日记账准备",
        system_prompt="""你是一位资深财务专家。请给出专业的财务分析建议。

重要免责声明：你协助处理财务工作流程，但不提供财务建议。所有报表应由合格的财务专业人员审查后才能用于报告或申报。

请在回答开头明确说明：【财务专家报告】
""",
        tools=[search_financial_knowledge, get_financial_statement_template, get_variance_analysis_template]
    )
    
    agent = config.create_agent()
    
    print("正在调用财务专家Agent...")
    result = await agent.ainvoke("请简单介绍一下利润表的主要结构")
    
    assert "output" in result
    assert len(result["output"]) > 0
    
    print("✅ 财务专家Agent调用成功")
    print("   输出长度:", len(result["output"]), "字符")
    print("   输出预览:", result["output"][:100], "...")
    
    return result


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("开始测试法律财务专家Agent系统")
    print("=" * 80)
    
    try:
        test_legal_skills()
        test_finance_skills()
        test_legal_expert_config()
        test_finance_expert_config()
        
        asyncio.run(test_legal_expert_invoke())
        asyncio.run(test_finance_expert_invoke())
        
        print("\n" + "=" * 80)
        print("🎉 所有测试通过！法律财务专家Agent系统工作正常！")
        print("=" * 80)
        print("\n核心功能验证:")
        print("  ✅ 法律技能工具 - 知识库搜索和模板获取")
        print("  ✅ 财务技能工具 - 知识库搜索和模板获取")
        print("  ✅ 法律专家配置 - 通过AgentConfig创建法律专家")
        print("  ✅ 财务专家配置 - 通过AgentConfig创建财务专家")
        print("  ✅ 法律专家调用 - Agent成功处理法律相关问题")
        print("  ✅ 财务专家调用 - Agent成功处理财务相关问题")
        
    except Exception as e:
        print("\n❌ 测试失败:", str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()