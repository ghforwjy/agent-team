
"""
Agent 模块
每个 Agent 都是 BaseAgent 的具体实现，有独立的配置和 Skills
"""
from .legal_agent import LEGAL_EXPERT_CONFIG, create_legal_agent
from .finance_agent import FINANCE_EXPERT_CONFIG, create_finance_agent

__all__ = [
    'LEGAL_EXPERT_CONFIG',
    'FINANCE_EXPERT_CONFIG',
    'create_legal_agent',
    'create_finance_agent',
]
