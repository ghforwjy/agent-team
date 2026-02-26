# Agent模块架构

## 为什么模块化？

**之前的问题：**
- 所有Agent定义混在一个文件里
- 工具函数也混在一起
- 不便于管理和扩展

**模块化后的好处：**
- 每个Agent独立文件，职责清晰
- 工具函数和配置放在一起
- 便于团队协作和维护

## Agent文件结构

每个Agent文件都遵循统一的结构：

```python
# agents/legal_agent.py

"""
法律合规专家 Agent 定义
基于 BaseAgent 的具体实现
"""
from langchain.tools import tool
from agent_framework import AgentConfig, BaseAgent
from skill_loader import create_skill_loader

# 1. 初始化技能加载器
_skill_loader = create_skill_loader()

# 2. 定义工具函数
@tool
def search_legal_knowledge(topic: str) -> str:
    """搜索法律相关知识"""
    # 优先从 SKILL.md 加载
    content = _get_legal_skill_content("contract-review")
    if content:
        return content
    # 回退到硬编码
    return "备用知识..."

@tool
def get_contract_review_template() -> str:
    """获取合同审查模板"""
    # ...

# 3. 定义Agent配置
LEGAL_EXPERT_CONFIG = AgentConfig(
    name="legal_expert",
    role="法律合规专家",
    description="负责合同审查、法律风险评估...",
    system_prompt="你是一位资深法律合规专家...",
    tools=[search_legal_knowledge, get_contract_review_template]
)

# 4. 创建函数
def create_legal_agent() -> BaseAgent:
    """创建法律合规专家 Agent 实例"""
    return LEGAL_EXPERT_CONFIG.create_agent()
```

## 模块入口文件

```python
# agents/__init__.py

from .legal_agent import LEGAL_EXPERT_CONFIG, create_legal_agent
from .finance_agent import FINANCE_EXPERT_CONFIG, create_finance_agent

__all__ = [
    'LEGAL_EXPERT_CONFIG',
    'FINANCE_EXPERT_CONFIG',
    'create_legal_agent',
    'create_finance_agent',
]
```

## 当前实现的Agent

| Agent | 文件 | 功能 |
|-------|------|------|
| 法律合规专家 | `agents/legal_agent.py` | 合同审查、合规检查、NDA分类 |
| 财务专家 | `agents/finance_agent.py` | 财务报表、差异分析、审计支持 |

## 扩展新Agent的步骤

**只需3步：**

1. **创建Agent文件** - 在`agents/`目录下新建文件
2. **更新模块入口** - 在`agents/__init__.py`中添加导出
3. **更新协调系统** - 在`legal_finance_swarm.py`中添加配置
