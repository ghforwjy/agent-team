# 如何扩展新专家

## 想加一个"税务专家"？只需3步！

### 第1步：创建Agent文件

在 `agents/` 目录下创建 `tax_agent.py`：

```python
# agents/tax_agent.py

from langchain.tools import tool
from agent_framework import AgentConfig, BaseAgent
from skill_loader import create_skill_loader

_skill_loader = create_skill_loader()

@tool
def search_tax_knowledge(topic: str) -> str:
    """搜索税务相关知识"""
    skill = _skill_loader.get_skill("tax", "tax-consultation")
    if skill:
        return skill['content']
    return "备用税务知识..."

@tool
def get_tax_declaration_template() -> str:
    """获取税务申报模板"""
    # ...

TAX_EXPERT_CONFIG = AgentConfig(
    name="tax_expert",
    role="税务专家",
    description="负责税务咨询、申报指导",
    system_prompt="你是一位资深税务专家...",
    tools=[search_tax_knowledge, get_tax_declaration_template]
)

def create_tax_agent() -> BaseAgent:
    return TAX_EXPERT_CONFIG.create_agent()
```

### 第2步：更新模块入口

在 `agents/__init__.py` 中添加：

```python
from .tax_agent import TAX_EXPERT_CONFIG, create_tax_agent

__all__ = [
    # ... 原有的
    'TAX_EXPERT_CONFIG',
    'create_tax_agent',
]
```

### 第3步：更新协调系统

在 `legal_finance_swarm.py` 中导入并添加配置：

```python
from agents import LEGAL_EXPERT_CONFIG, FINANCE_EXPERT_CONFIG, TAX_EXPERT_CONFIG

def create_expert_configs():
    return {
        LEGAL_EXPERT_CONFIG.name: LEGAL_EXPERT_CONFIG,
        FINANCE_EXPERT_CONFIG.name: FINANCE_EXPERT_CONFIG,
        TAX_EXPERT_CONFIG.name: TAX_EXPERT_CONFIG,  # 新加！
    }
```

**就这么简单！协调员会自动识别税务问题，分配给税务专家！**

## 添加新的 SKILL.md

在 `knowledge-work-plugins/` 下创建新的技能目录：

```bash
mkdir -p knowledge-work-plugins/tax/skills/tax-consultation
```

创建 `SKILL.md` 文件：

```markdown
---
name: tax-consultation
description: 税务咨询和申报指导
---

# Tax Consultation Skill

你是一个税务咨询助手...

## 税务申报流程

### 增值税申报
...

### 企业所得税申报
...
```

## 可扩展的专家类型

1. **税务专家** - 税务咨询、申报指导
2. **人力资源专家** - 招聘、培训、绩效管理
3. **IT运维专家** - 系统监控、故障排查
4. **供应链专家** - 采购、库存、物流管理
