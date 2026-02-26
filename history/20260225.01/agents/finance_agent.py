
"""
财务专家 Agent 定义
基于 BaseAgent 的具体实现
"""
from typing import Dict, List
from langchain.tools import tool
from agent_framework import AgentConfig, BaseAgent
from skill_loader import create_skill_loader

# 初始化技能加载器
_skill_loader = create_skill_loader()

# 硬编码知识库作为备用
FINANCIAL_KNOWLEDGE_BASE = {
    "财务报表": {
        "GAAP标准": "ASC 220/IAS 1(利润表)、ASC 210/IAS 1(资产负债表)、ASC 230/IAS 7(现金流量表)",
        "利润表结构": "收入、成本、毛利、营业费用、营业利润、其他收入/费用、所得税、净利润",
        "资产负债表结构": "流动资产、非流动资产、流动负债、非流动负债、股东权益"
    },
    "差异分析": {
        "分解方法": "价格/数量分解、费率/组合分解、人力成本分解",
        "重要性阈值": "通常5-15%"
    },
    "审计支持": {
        "SOX合规": "SOX 404控制测试方法",
        "文档标准": "样本选择、文档标准、缺陷分类框架"
    }
}


def _get_finance_skill_content(skill_name):
    """从 SKILL.md 获取财务技能内容"""
    skill = _skill_loader.get_skill("finance", skill_name)
    if skill:
        return skill['content']
    return None


@tool
def search_financial_knowledge(topic: str) -> str:
    """
    搜索财务相关知识，包括财务报表、差异分析、日记账准备等
    优先从 SKILL.md 文件加载专业知识

    Args:
        topic: 财务主题，例如"财务报表"、"差异分析"、"GAAP"等
    
    Returns:
        财务专业知识
    """
    skill_mapping = {
        "财务报表": "financial-statements",
        "利润表": "financial-statements",
        "资产负债表": "financial-statements",
        "现金流量表": "financial-statements",
        "差异分析": "variance-analysis",
        "日记账": "journal-entry-prep",
        "账户对账": "reconciliation",
        "对账": "reconciliation",
        "月末结账": "close-management",
        "审计支持": "audit-support",
        "审计": "audit-support",
        "SOX": "audit-support",
    }
    
    skill_name = None
    for key, value in skill_mapping.items():
        if key.lower() in topic.lower():
            skill_name = value
            break
    
    if skill_name:
        content = _get_finance_skill_content(skill_name)
        if content:
            return "【财务知识库 - 从SKILL.md加载】\n" + content
    
    info = FINANCIAL_KNOWLEDGE_BASE.get(topic, {})
    if info:
        result = "【财务知识库 - " + topic + "】\n"
        for k, v in info.items():
            result += k + ": " + v + "\n"
        return result
    
    return "未找到" + topic + "的财务知识库信息"


@tool
def get_financial_statement_template() -> str:
    """
    获取财务报表模板
    优先从 SKILL.md 文件加载

    Returns:
        财务报表模板
    """
    content = _get_finance_skill_content("financial-statements")
    if content:
        return "【财务报表模板 - 从SKILL.md加载】\n" + content
    
    return """【财务报表模板】
==============
一、利润表
1. 收入
2. 成本
3. 毛利
4. 营业费用
5. 营业利润
6. 其他收入/费用
7. 所得税
8. 净利润

二、资产负债表
1. 资产
   - 流动资产
   - 非流动资产
2. 负债
   - 流动负债
   - 非流动负债
3. 股东权益
"""


@tool
def get_variance_analysis_template() -> str:
    """
    获取差异分析模板
    优先从 SKILL.md 文件加载

    Returns:
        差异分析模板
    """
    content = _get_finance_skill_content("variance-analysis")
    if content:
        return "【差异分析模板 - 从SKILL.md加载】\n" + content
    
    return """【差异分析模板】
==============
1. 差异计算
2. 重要性阈值判断
3. 差异分解
4. 驱动因素分析
5. 瀑布图展示
6. 业务原因说明
7. 趋势判断与行动建议
"""


# 财务专家配置
FINANCE_EXPERT_CONFIG = AgentConfig(
    name="finance_expert",
    role="财务专家",
    description="负责财务报表生成、差异分析、日记账准备、账户对账、月末结账、审计支持等财务相关任务",
    system_prompt="""你是一位资深财务专家。你的任务是处理财务报表生成、差异分析、日记账准备、账户对账、月末结账、审计支持等财务相关任务。

你可以使用以下工具获取专业财务知识：
- search_financial_knowledge(topic): 搜索财务相关知识
- get_financial_statement_template(): 获取财务报表模板
- get_variance_analysis_template(): 获取差异分析模板

请给出专业、详细的财务分析和建议。

重要免责声明：你协助处理财务工作流程，但不提供财务建议。所有报表应由合格的财务专业人员审查后才能用于报告或申报。

请在回答开头明确说明：【财务专家报告】
""",
    tools=[search_financial_knowledge, get_financial_statement_template, get_variance_analysis_template]
)


def create_finance_agent() -> BaseAgent:
    """创建财务专家 Agent 实例"""
    return FINANCE_EXPERT_CONFIG.create_agent()
