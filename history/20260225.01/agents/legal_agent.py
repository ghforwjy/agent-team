
"""
法律合规专家 Agent 定义
基于 BaseAgent 的具体实现
"""
from typing import Dict, List
from langchain.tools import tool
from agent_framework import AgentConfig, BaseAgent
from skill_loader import create_skill_loader

# 初始化技能加载器
_skill_loader = create_skill_loader()

# 硬编码知识库作为备用
LEGAL_KNOWLEDGE_BASE = {
    "合同审查": {
        "关键条款": "责任限制、赔偿条款、知识产权、数据保护、期限与终止、适用法律",
        "风险等级": "GREEN(可接受)、YELLOW(需协商)、RED(需升级)",
        "审查方法": "基于playbook审查、条款分析、偏离严重度分类、生成修订建议"
    },
    "法律风险评估": {
        "评估框架": "严重性(1-5级) x 可能性(1-5级)",
        "风险等级": "低/中/高/严重",
        "升级标准": "外部律师介入指引"
    },
    "合规检查": {
        "主要法规": "GDPR(欧盟)、CCPA/CPRA(加州)、PIPL(中国)等",
        "GDPR要求": "数据保护、72小时违约通知、DPIA、SCCs"
    }
}


def _get_legal_skill_content(skill_name):
    """从 SKILL.md 获取法律技能内容"""
    skill = _skill_loader.get_skill("legal", skill_name)
    if skill:
        return skill['content']
    return None


@tool
def search_legal_knowledge(topic: str) -> str:
    """
    搜索法律相关知识，包括合同审查、合规检查、法律风险评估等
    优先从 SKILL.md 文件加载专业知识

    Args:
        topic: 法律主题，例如"合同审查"、"合规检查"、"GDPR"等
    
    Returns:
        法律专业知识
    """
    skill_mapping = {
        "合同审查": "contract-review",
        "合同": "contract-review",
        "contract": "contract-review",
        "合规检查": "compliance",
        "合规": "compliance",
        "compliance": "compliance",
        "GDPR": "compliance",
        "NDA分类": "nda-triage",
        "NDA": "nda-triage",
        "法律风险评估": "legal-risk-assessment",
        "风险评估": "legal-risk-assessment",
        "会议简报": "meeting-briefing",
        "模板化响应": "canned-responses",
    }
    
    skill_name = None
    for key, value in skill_mapping.items():
        if key.lower() in topic.lower():
            skill_name = value
            break
    
    if skill_name:
        content = _get_legal_skill_content(skill_name)
        if content:
            return "【法律知识库 - 从SKILL.md加载】\n" + content
    
    info = LEGAL_KNOWLEDGE_BASE.get(topic, {})
    if info:
        result = "【法律知识库 - " + topic + "】\n"
        for k, v in info.items():
            result += k + ": " + v + "\n"
        return result
    
    return "未找到" + topic + "的法律知识库信息"


@tool
def get_contract_review_template() -> str:
    """
    获取合同审查模板
    优先从 SKILL.md 文件加载

    Returns:
        合同审查模板
    """
    content = _get_legal_skill_content("contract-review")
    if content:
        return "【合同审查模板 - 从SKILL.md加载】\n" + content
    
    return """【合同审查模板】
==============
1. 合同类型识别
2. 用户方立场确认
3. 关键条款分析
   - 责任限制条款
   - 赔偿条款
   - 知识产权条款
   - 数据保护条款
   - 期限与终止条款
   - 适用法律与争议解决
4. 偏离严重度分类(GREEN/YELLOW/RED)
5. 生成修订建议(redline)
6. 谈判优先级建议(Tier 1/2/3)
"""


# 法律专家配置
LEGAL_EXPERT_CONFIG = AgentConfig(
    name="legal_expert",
    role="法律合规专家",
    description="负责合同审查、法律风险评估、合规检查、NDA分类、会议简报等法律相关任务",
    system_prompt="""你是一位资深法律合规专家。你的任务是处理合同审查、法律风险评估、合规检查、NDA分类、会议简报等法律相关任务。

你可以使用以下工具获取专业法律知识：
- search_legal_knowledge(topic): 搜索法律相关知识
- get_contract_review_template(): 获取合同审查模板

请给出专业、详细的法律分析和建议。

重要免责声明：你协助处理法律工作流程，但不提供法律建议。所有分析应由合格的法律专业人员审查后才能依赖。

请在回答开头明确说明：【法律合规专家报告】
""",
    tools=[search_legal_knowledge, get_contract_review_template]
)


def create_legal_agent() -> BaseAgent:
    """创建法律合规专家 Agent 实例"""
    return LEGAL_EXPERT_CONFIG.create_agent()
