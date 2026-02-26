# 知识库集成详解

## 什么是 knowledge-work-plugins？

**用图书馆的例子理解：**

想象你要开一家医院，你需要：
- 📚 **医学百科全书** - 各种疾病的诊断方法
- 📚 **手术操作手册** - 各种手术的标准流程
- 📚 **药品说明书** - 各种药物的用法用量

**knowledge-work-plugins 就是这样的"专业知识图书馆"！**

它是由 Anthropic 公司开源的一个项目，包含了大量专业领域的知识文件。

## 目录结构

```
knowledge-work-plugins/
├── legal/                          # 法律领域插件
│   ├── .claude-plugin/
│   │   └── plugin.json             # 插件配置
│   ├── commands/                   # 命令（快捷方式）
│   │   ├── review-contract.md
│   │   ├── triage-nda.md
│   │   └── ...
│   ├── skills/                     # 技能（核心知识）
│   │   ├── contract-review/
│   │   │   └── SKILL.md            # 合同审查知识文件
│   │   ├── compliance/
│   │   │   └── SKILL.md            # 合规检查知识文件
│   │   └── ...
│   └── CONNECTORS.md               # 连接器说明
│
├── finance/                        # 财务领域插件
│   └── skills/
│       ├── financial-statements/
│       │   └── SKILL.md            # 财务报表知识文件
│       └── ...
│
├── marketing/                      # 市场营销插件
├── sales/                          # 销售插件
├── data/                           # 数据分析插件
└── ...                             # 更多领域
```

## SKILL.md 文件结构

每个 SKILL.md 文件都遵循统一的格式：

```markdown
---
name: contract-review
description: 审查合同，识别偏离，生成修订建议
---

# Contract Review Skill

你是一个合同审查助手...

## Playbook-Based Review Methodology

### 步骤1：识别合同类型
SaaS协议、专业服务、许可证...

### 步骤2：确定用户立场
供应商、客户、许可方、被许可方...

### 步骤3：分析关键条款
- 责任限制条款
- 赔偿条款
- 知识产权条款
...
```

## 集成方式

### skill_loader.py 加载器

```python
class SkillLoader:
    """SKILL.md 文件加载器"""
    
    def __init__(self, plugins_dir="knowledge-work-plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.skills = {}
        self._load_all_skills()
    
    def get_skill(self, category, name):
        """获取指定技能"""
        return self.skills.get(f"{category}.{name}")
```

### 在 Agent 中使用

```python
@tool
def search_legal_knowledge(topic: str) -> str:
    """搜索法律相关知识"""
    
    # 1. 根据主题映射到具体的 SKILL.md
    skill_mapping = {
        "合同审查": "contract-review",
        "合规检查": "compliance",
        "NDA": "nda-triage",
    }
    
    # 2. 从 knowledge-work-plugins 加载知识
    skill_name = skill_mapping.get(topic)
    if skill_name:
        skill = _skill_loader.get_skill("legal", skill_name)
        if skill:
            return "【从SKILL.md加载】\n" + skill['content']
    
    # 3. 回退到硬编码知识
    return "【备用知识库】\n" + fallback_knowledge
```

## 已集成的技能列表

系统启动时会自动加载 **52个专业技能**：

**法律类（6个）：**
| 技能名 | 描述 |
|--------|------|
| contract-review | 合同审查，识别偏离，生成修订建议 |
| compliance | 合规检查，GDPR、CCPA等法规 |
| nda-triage | NDA分类和处理 |
| legal-risk-assessment | 法律风险评估 |
| meeting-briefing | 会议简报准备 |
| canned-responses | 模板化响应 |

**财务类（6个）：**
| 技能名 | 描述 |
|--------|------|
| financial-statements | 财务报表生成 |
| variance-analysis | 差异分析 |
| journal-entry-prep | 日记账准备 |
| reconciliation | 账户对账 |
| close-management | 月末结账管理 |
| audit-support | 审计支持 |
