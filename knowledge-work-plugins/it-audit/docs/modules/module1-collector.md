# 模块1：审计项收集器 详细设计

> 版本: v2.0
> 最后更新: 2026-03-02

## 一、功能概述

- **输入**: 各种格式的检查底稿Excel
- **处理**: 解析Excel → 列名映射 → 语义清洗 → LLM校验 → 入库
- **输出**: 标准审计项库 + 审计动作库（SQLite）

**核心目标**: 将各种来源的审计底稿清洗合并，形成统一的审计知识库：
- 相同审计项合并，不重复存储
- 不同审计动作积累到同一审计项下
- 支持语义相似度匹配，识别同义不同词的审计项

## 二、目录结构

```
1-audit-item-collector/
├── SKILL.md                     # 模块文档
├── references/                  # 参考资料
│   └── column-mapping-guide.md  # 列映射指南
└── scripts/                     # 功能脚本
    ├── __init__.py              # 模块导出
    ├── cleaner.py               # 清洗流程主程序
    ├── collector.py             # 收集器主逻辑
    ├── db_manager.py            # 数据库管理
    ├── excel_parser.py          # Excel解析
    ├── llm_verifier.py          # LLM校验模块
    ├── semantic_matcher.py      # 语义匹配模块
    └── analyzers/               # 数据分析器
        ├── __init__.py
        ├── models.py            # 数据模型
        ├── data_loader.py       # 数据加载
        ├── analyzer.py          # 分析逻辑
        └── reporter.py          # 报告生成
```

## 三、清洗流程

### 3.1 整体流程

```
┌─────────────────────────────────────────────────────────────────┐
│ 步骤1: Excel解析                                                 │
│   - 读取Excel文件                                                │
│   - 智能识别表头位置                                             │
│   - 列名映射到标准字段                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 步骤2: 数据提取                                                  │
│   - 提取：维度、审计项标题、审计程序                             │
│   - 过滤：检查结论、检查记录、证据清单（属于审计结果）           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 步骤3: 审计项语义匹配（向量模型）                                │
│   - 使用向量模型计算语义相似度                                   │
│   - 阈值判断：                                                   │
│     > 0.85: 高相似，进入步骤4（LLM校验）                         │
│     0.60-0.85: 中相似，待人工确认                               │
│     < 0.60: 低相似，视为新审计项，进入步骤5                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 步骤4: LLM校验（高相似情况）                                     │
│   - 筛选需要校验的候选（相似度>0.85）                            │
│   - 批量LLM校验（一次性校验）                                    │
│   - 判断结果：                                                   │
│     确认合并 → 进入步骤5（复用已有审计项）                       │
│     应分离 → 视为新审计项，进入步骤5（新建）                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 步骤5: 审计动作匹配（审计项已存在时）                            │
│   - 对比新审计程序与已有审计程序                                 │
│   - 语义相似度判断：                                             │
│     > 0.80: 需要LLM校验是否同一动作                              │
│     < 0.80: 新增审计动作                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 步骤6: 入库                                                      │
│   - 新审计项：写入audit_items                                    │
│   - 新审计动作：写入audit_procedures                             │
│   - 来源记录：写入audit_item_sources                             │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 两阶段匹配策略

> **核心问题**: 200条新 × 600条已有 = 120,000次比较，如果每次都调用LLM，成本和时间不可接受。
> 
> **解决方案**: 向量模型做初筛，LLM只校验候选结果。

```
阶段1: 向量模型初筛（快速、低成本）
┌─────────────────────────────────────────────────────────────────┐
│ 输入: 200条新审计项 + 600条已有审计项                            │
│ 处理: 批量计算向量，矩阵乘法求相似度                             │
│ 输出: 每条新审计项的Top-K候选（K=3）                             │
│ 耗时: 约10秒（本地模型）                                         │
│ 成本: 0元                                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
阶段2: LLM校验（仅对候选结果）
┌─────────────────────────────────────────────────────────────────┐
│ 输入: 约20-50条需要校验的候选对                                  │
│ 处理: 批量LLM校验（一次调用处理多个）                            │
│ 输出: 最终合并决策                                               │
│ 耗时: 约30秒                                                     │
│ 成本: 约0.1-0.5元                                                │
└─────────────────────────────────────────────────────────────────┘
```

## 四、相似度阈值配置

| 匹配对象 | 高相似阈值 | 中相似阈值 | 处理方式 |
|----------|-----------|-----------|----------|
| 审计项 | 0.85 | 0.60 | 高相似进入LLM校验，中相似人工确认 |
| 审计动作 | 0.80 | - | 高相似进入LLM校验，低相似新增 |

## 五、LLM校验设计

### 5.1 校验时机

在语义匹配完成后、入库之前，对以下情况进行LLM校验：

| 场景 | 触发条件 | 校验目的 |
|------|----------|----------|
| 审计项合并校验 | 语义相似度 >= 0.85 | 确认是否真的是同一检查项 |
| 审计动作合并校验 | 语义相似度 >= 0.80 | 确认检查方法是否真的相同 |
| 维度一致性校验 | 审计项合并时维度不一致 | 确认维度分类是否合理 |

### 5.2 校验Prompt模板

```
你是一个IT审计专家，负责审核审计项的合并决策是否正确。

## 待审核内容

### 1. 审计项合并审核

以下审计项对被向量模型标记为"相似度>=0.85"，请判断是否真的是同一检查项：

{item_merges_json}

**判断标准：**
- **应该合并（reuse）**：检查重点相同、检查对象相同、只是表述不同
- **应该分离（create）**：检查重点不同、存在包含关系、检查角度不同

### 2. 审计动作合并审核

以下审计动作对被向量模型标记为"相似度>=0.80"，请判断是否真的是同一检查方法：

{procedure_merges_json}

**判断标准：**
- **应该复用（reuse_procedure）**：检查方法相同、检查对象相同
- **应该新建（create_procedure）**：检查方法不同、检查对象不同

## 输出格式

请以JSON格式输出审核结果：
{
    "review_status": "confirmed/adjusted",
    "item_merge_decisions": [...],
    "procedure_merge_decisions": [...]
}
```

### 5.3 典型错误案例

```
案例1: 假阳性合并
- 审计项A: "是否建立IT治理委员会"
- 审计项B: "IT治理委员会是否有效运作"
- 语义相似度: 0.88 (高相似)
- LLM判断: 不是同一审计项
  - A检查的是"有没有建立"
  - B检查的是"运作是否有效"
  - 检查重点不同，应保持分离

案例2: 动作误合并
- 动作A: "查阅IT治理委员会成立发文"
- 动作B: "查阅IT治理委员会会议记录"
- 语义相似度: 0.82 (高相似)
- LLM判断: 不是同一动作
  - A检查的是"成立文件"
  - B检查的是"会议记录"
  - 检查对象不同，应保留两个动作
```

## 六、数据分析器

模块1内置数据分析器，位于 `scripts/analyzers/` 目录：

| 文件 | 功能 |
|------|------|
| models.py | 数据模型定义（AuditItem, AuditProcedure, ItemSource等） |
| data_loader.py | 从SQLite数据库加载数据 |
| analyzer.py | 统计分析（维度分布、程序数量统计等） |
| reporter.py | 报告生成（Console/HTML/CSV/JSON） |

**使用方法**:
```python
from skills.audit_item_collector.scripts.analyzers import (
    DatabaseLoader, AuditAnalyzer, HtmlReporter
)

# 数据库路径必须传入
db_path = "knowledge-work-plugins/it-audit/data/it_audit.db"

with DatabaseLoader(db_path) as loader:
    analyzer = AuditAnalyzer(loader)
    result = analyzer.analyze()
    
    reporter = HtmlReporter(analyzer)
    reporter.generate_report('output/report.html')
```

## 七、核心类设计

```python
# 1. ExcelParser - Excel解析器
class ExcelParser:
    def parse(self, file_path: str) -> List[Dict]
    def detect_header_row(self, sheet) -> int
    def map_columns(self, headers: List[str]) -> Dict

# 2. SemanticMatcher - 语义匹配器
class SemanticMatcher:
    def batch_match(self, new_items: List, existing_items: List) -> Dict
    def _match_item(self, new_title: str, existing_items: List) -> MatchResult
    def _match_procedure(self, new_proc: str, existing_procs: List) -> MatchResult

# 3. LLMVerifier - LLM校验器
class LLMVerifier:
    def verify_merge_suggestions(self, merge_result: Dict) -> Dict
    def _filter_candidates_for_llm(self, merge_result: Dict) -> Dict
    def _build_verification_prompt(self, candidates: Dict) -> str
    def apply_detailed_adjustments(self, merge_result: Dict, review: Dict) -> Dict

# 4. Cleaner - 清洗流程主程序
class Cleaner:
    def clean_from_excel(self, file_path: str, output_json: str = None) -> Dict
    def apply_result(self, result_json: str, approved: bool = True)
```

## 八、版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| v2.1 | 2026-03-02 | 数据库路径规则：必须传入db_path参数 |
| v2.0 | 2026-03-02 | 文档重组，添加分析器目录结构 |
| v1.5 | 2026-02-27 | LLM校验修复：添加审计动作校验、阈值筛选 |
| v1.0 | 2026-02-25 | 初始设计 |
