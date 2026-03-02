# IT审计Agent

IT审计Agent是一个智能化的IT审计辅助系统，提供审计项收集、策略合规检查等功能。

## 文档索引

### 架构设计
| 文档 | 说明 |
|------|------|
| [架构设计总览](./docs/architecture/design-overview.md) | 整体架构、目录结构、数据库设计、技术选型 |

### 模块详细设计
| 文档 | 说明 |
|------|------|
| [模块1：审计项收集器](./docs/modules/module1-collector.md) | 清洗流程、语义匹配、LLM校验、分析器 |
| [模块2：策略合规检查器](./docs/modules/module2-checker.md) | 制度解析、条款检索、合规分析 |

### 测试相关
| 文档 | 说明 |
|------|------|
| [测试场景设计](./docs/testing/test-scenarios.md) | 5个测试场景、JSON格式规范、成功标准 |

## 目录结构

```
it-audit/
├── README.md                    # 本文档（文档索引入口）
├── docs/                        # 文档目录
│   ├── architecture/            # 架构设计
│   │   └── design-overview.md   # 架构设计总览
│   ├── modules/                 # 模块详细设计
│   │   ├── module1-collector.md # 模块1详细设计
│   │   └── module2-checker.md   # 模块2详细设计
│   └── testing/                 # 测试相关
│       └── test-scenarios.md    # 测试场景设计
├── commands/                    # 命令定义
│   ├── collect-audit-items.md   # 收集审计项命令
│   ├── check-policy-compliance.md # 策略合规检查命令
│   ├── generate-report.md       # 生成报告命令
│   └── run-audit.md             # 运行审计命令
├── data/                        # 数据目录
│   └── it_audit.db              # 主数据库
├── skills/                      # 技能模块
│   ├── 1-audit-item-collector/  # 模块1: 审计项收集
│   ├── 2-policy-compliance-checker/ # 模块2: 策略合规检查
│   └── scenario-tester/         # 场景测试器
└── tests/                       # 测试目录
    └── output/                  # 测试输出
```

## 模块概览

### 模块1: 审计项收集器 (1-audit-item-collector)

负责从Excel文件中收集、清洗、存储审计项数据。

**核心功能**:
- Excel解析与列名映射
- 语义相似度匹配（向量模型）
- LLM校验（防止假阳性合并）
- 审计项与审计动作分离存储
- 来源追溯记录

**详细文档**: [module1-collector.md](./docs/modules/module1-collector.md)

### 模块2: 策略合规检查器 (2-policy-compliance-checker)

负责从制度文档中提取审计要求，进行合规检查。

**核心功能**:
- 制度文档解析（Word/PDF）
- 条款索引与向量检索
- LLM深度分析匹配程度
- 差距分析与调整建议生成

**详细文档**: [module2-checker.md](./docs/modules/module2-checker.md)

### 场景测试器 (scenario-tester)

提供常态化场景测试功能，验证各模块功能的正确性。

**使用方法**:
```bash
# 运行所有场景测试
python -m knowledge_work_plugins.it_audit.skills.scenario_tester.scripts.runner

# 运行指定模块测试
python -m knowledge_work_plugins.it_audit.skills.scenario_tester.scripts.runner --module 1
```

## 代码组织规则

### 模块代码组织

每个功能模块遵循以下组织规则:

1. **scripts/**: 功能实现代码
   - 核心业务逻辑脚本
   - 工具类和辅助函数

2. **scripts/analyzers/**: 数据分析器
   - 数据模型定义 (models.py)
   - 数据加载器 (data_loader.py)
   - 分析逻辑 (analyzer.py)
   - 报告生成器 (reporter.py)

3. **references/**: 参考文档
   - 配置指南
   - 映射规则
   - 使用说明

### 分析器架构

```
数据库/JSON数据
    ↓
data_loader.py (加载数据)
    ↓
models.py (数据模型)
    ↓
analyzer.py (分析计算)
    ↓
reporter.py (报告生成)
    ↓
输出 (Console/HTML/CSV/JSON)
```

## 数据库路径规则

> **重要**: 所有模块的数据库路径必须由调用者传入，不提供默认值。

**推荐路径约定**（调用者可自定义，但建议遵循以下约定）：

| 场景 | 推荐路径 | 说明 |
|------|----------|------|
| 正式使用 | `knowledge-work-plugins/it-audit/data/it_audit.db` | 项目标准数据库位置 |
| 测试使用 | `tests/test_data/test_it_audit.db` | 测试隔离，不影响正式数据 |

### 命令行使用示例

```bash
# 模块1: 审计项收集器
python -m knowledge_work_plugins.it_audit.skills.audit_item_collector.scripts.collector \
    -d "knowledge-work-plugins/it-audit/data/it_audit.db" \
    "训练材料/审计底稿.xlsx"

# 模块1: 清洗器
python -m knowledge_work_plugins.it_audit.skills.audit_item_collector.scripts.cleaner \
    -d "knowledge-work-plugins/it-audit/data/it_audit.db" \
    "训练材料/审计底稿.xlsx" \
    --apply

# 模块2: 策略合规检查器
python -m knowledge_work_plugins.it_audit.skills.policy_compliance_checker.scripts.policy_extractor \
    --db-path "knowledge-work-plugins/it-audit/data/it_audit.db" \
    --policy-folder "制度文件/"
```

### 代码调用示例

```python
from knowledge_work_plugins.it_audit.skills.audit_item_collector.scripts import (
    DatabaseManager, AuditItemCleaner
)

# 正式使用
db_path = "knowledge-work-plugins/it-audit/data/it_audit.db"

# 初始化数据库
db = DatabaseManager(db_path)
db.init_database()

# 使用清洗器
cleaner = AuditItemCleaner(db_path)
result = cleaner.clean_from_excel("审计底稿.xlsx")
```

## 快速开始

1. 收集审计项:
   ```
   /collect-audit-items <excel_file>
   ```

2. 检查策略合规:
   ```
   /check-policy-compliance <policy_document>
   ```

3. 生成分析报告:
   ```
   /generate-report
   ```

4. 运行场景测试:
   ```bash
   python -m knowledge_work_plugins.it_audit.skills.scenario_tester.scripts.runner
   ```

## 版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| v3.1 | 2026-03-02 | 数据库路径规则：必须传入db_path参数 |
| v3.0 | 2026-03-02 | 文档重组，统一入口索引，更新目录结构 |
| v2.0 | 2026-02-27 | 添加LLM校验、场景测试器 |
| v1.0 | 2026-02-25 | 初始版本 |
