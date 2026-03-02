# 模块2：策略合规检查器 详细设计

> 版本: v3.0
> 最后更新: 2026-03-02

## 一、功能概述

- **输入**: 标准检查项（从SQLite）+ 被审计制度文档
- **处理**: 向量筛选 → LLM确认 → 差距识别
- **输出**: 合规检查报告（JSON/Word）

**核心目标**: 
1. 发现制度与审计项不符合的地方
2. 检查制度是否涵盖了审计项对制度建设的要求
3. 给出制度调整意见，精确到具体制度、具体条款

## 二、目录结构

```
2-policy-compliance-checker/
├── SKILL.md                     # 模块文档
├── __init__.py
└── scripts/                     # 功能脚本
    ├── __init__.py              # 模块导出
    ├── policy_extractor.py      # 制度要求提取（主入口）
    ├── vector_screener.py       # 向量筛选器（新增）
    ├── db_manager.py            # 数据库管理（新增）
    └── analyzers/               # 数据分析器
        ├── __init__.py
        └── policy_reporter.py   # 策略报告生成
```

## 三、核心流程

### 3.1 制度要求提取流程（向量+LLM两阶段）

```
┌─────────────────────────────────────────────────────────────────┐
│              制度要求提取流程（向量+LLM两阶段）                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 加载审计项                                                   │
│     ├── 检查已筛选记录（增量模式）                                │
│     └── 只加载未筛选的审计项                                      │
│                                                                 │
│  2. 阶段1：向量语义筛选（秒级）                                   │
│     ├── 计算审计项与模板向量的相似度                              │
│     └── 根据相似度分级处理                                        │
│         ├── > 0.70：高置信度 → 直接确定分类，无需LLM              │
│         ├── 0.45-0.70：中置信度 → 需要LLM确认                    │
│         └── < 0.45：低置信度 → 不包含制度要求，跳过               │
│                                                                 │
│  3. 阶段2：LLM确认与分类                                         │
│     ├── 只处理中置信度的项                                        │
│     ├── LLM确认分类是否正确                                       │
│     └── 更新状态：confirmed/rejected                             │
│                                                                 │
│  4. 输出结果                                                     │
│     └── 生成JSON/HTML报告                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 制度完备性检查流程（待实现）

```
┌─────────────────────────────────────────────────────────────────┐
│                    制度完备性检查流程                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 读取审计项要求                                               │
│     ├── 从数据库读取所有审计项                                    │
│     ├── 提取审计程序中的制度要求                                  │
│     └── 按维度分类整理                                           │
│                                                                 │
│  2. 解析制度文档                                                 │
│     ├── 扫描制度文件夹                                           │
│     ├── 识别文档格式(Word/PDF/Excel)                              │
│     ├── 提取制度结构(章节/条款)                                   │
│     └── 建立制度条款索引                                         │
│                                                                 │
│  3. 智能匹配分析                                                 │
│     ├── 对每个审计项，向量检索Top-10候选条款                      │
│     ├── 关键词匹配补充检索                                        │
│     ├── LLM单条深度分析匹配程度                                   │
│     │   ├── 直接匹配: 条款完全满足要求                            │
│     │   ├── 部分匹配: 条款部分满足，需完善                        │
│     │   ├── 间接匹配: 通过其他条款间接满足                        │
│     │   └── 无匹配: 制度缺失                                     │
│     └── 记录匹配结果和差距分析                                    │
│                                                                 │
│  4. 生成检查报告                                                 │
│     ├── 统计总体符合度                                           │
│     ├── 列出不符合项(精确到条款)                                  │
│     ├── 列出缺失制度                                             │
│     └── 生成调整建议(含具体条款内容)                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 四、技术方案

| 组件 | 技术选型 | 理由 |
|------|----------|------|
| **向量筛选** | `sentence-transformers` | 复用模块1的SemanticMatcher，本地向量计算 |
| **向量模型** | `paraphrase-multilingual-MiniLM-L12-v2` | 多语言支持，适合中文语义匹配 |
| **LLM分析** | 豆包API/OpenAI兼容接口 | 确认分类，确保输出质量 |
| **报告生成** | `python-docx` + HTML | 直接生成可编辑的Word修订建议书 |

## 五、向量模板设计

### 5.1 模板结构

```python
VECTOR_TEMPLATES = {
    '建立制度': [
        # 动词 + 名词组合
        '制定制度', '建立制度', '编制制度',
        '制定规定', '建立规定', '编制规定',
        '制定办法', '建立办法', '编制办法',
        '制定规程', '建立规程', '编制规程',
        # 常见完整表述
        '制定相关制度', '建立相关制度',
        '制定管理制度', '建立管理制度',
        '制定安全制度', '建立安全制度',
        '制定管理规定', '建立管理规定',
    ],
    '定期执行': [
        # 频率 + 动作组合
        '每年开展检查', '每季度开展检查', '定期开展检查',
        '每年进行评估', '每季度进行评估', '定期进行评估',
        '每年开展演练', '定期开展演练',
        '每年进行审计', '定期进行审计',
        '每年进行评审', '定期进行评审',
        # 常见完整表述
        '定期开展安全检查', '每年进行风险评估',
        '定期进行安全评估', '每年开展审计工作',
    ],
    '人员配备': [
        # 动词 + 对象组合
        '配备人员', '设置岗位', '指定人员',
        '配备专职人员', '设置专职岗位',
        '配备安全人员', '设置安全岗位',
        '指定专人负责', '配备专门人员',
        '设置管理人员', '配备管理人员',
        '明确安全责任', '落实安全责任',
    ],
    '岗位分离': [
        '职责分离', '不相容岗位分离', '岗位分离',
        '职责分工', '岗位制衡', '互相监督',
        '不相容职责', '职责相互制约',
    ],
    '文件保存': [
        '保存文档', '留存记录', '归档文件',
        '保存记录', '留存文档', '归档记录',
        '保存档案', '留存档案',
        '保存日志', '留存日志', '归档日志',
    ],
    '建立组织': [
        '成立委员会', '建立委员会', '设立委员会',
        '成立小组', '建立小组', '设立小组',
        '成立部门', '建立部门', '设立部门',
        '成立领导小组', '建立工作组', '设立工作组',
        '建立组织机构', '成立工作机构',
    ]
}
```

### 5.2 置信度分级处理

| 相似度范围 | 置信度 | 处理方式 | 说明 |
|-----------|--------|---------|------|
| > 0.70 | 高 | 直接确定分类 | 向量匹配结果可靠，无需LLM |
| 0.45-0.70 | 中 | LLM确认 | 需要LLM确认分类 |
| < 0.45 | 低 | 跳过 | 不包含制度要求 |

### 5.3 设计优势

1. **纯向量语义匹配**：避免关键词"漏筛"
2. **置信度分级**：高置信度直接确定，减少LLM调用
3. **关键词组合生成句子**：保证语义完整性

## 六、数据库表结构

### 6.1 已实现表

```sql
-- 制度要求筛选结果表
CREATE TABLE policy_screening_results (
    id INTEGER PRIMARY KEY,
    item_id INTEGER NOT NULL,              -- 关联审计项ID
    item_code VARCHAR(30) NOT NULL,        -- 审计项编码
    screening_batch VARCHAR(50),           -- 筛选批次号
    vector_similarity REAL,                -- 向量相似度
    screening_status VARCHAR(20),          -- pending/confirmed/rejected
    requirement_type VARCHAR(20),          -- 建立制度/定期执行/...
    confidence REAL,                       -- 置信度
    llm_verified BOOLEAN DEFAULT 0,        -- 是否经LLM确认
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(item_id)                        -- 每个审计项只筛选一次
);
```

### 6.2 待实现表

```sql
-- 制度文档表
policy_documents (
    id INTEGER PRIMARY KEY,
    doc_code TEXT UNIQUE,           -- 制度编码
    doc_name TEXT,                  -- 制度名称
    doc_version TEXT,               -- 版本号
    file_path TEXT,                 -- 文件路径
    effective_date DATE,            -- 生效日期
    status TEXT                     -- 有效/废止/修订中
);

-- 制度条款表
policy_clauses (
    id INTEGER PRIMARY KEY,
    doc_id INTEGER,                 -- 关联制度
    clause_number TEXT,             -- 条款编号(如"第5条"、"5.2")
    clause_title TEXT,              -- 条款标题
    clause_content TEXT,            -- 条款内容
    clause_vector BLOB,             -- 向量表示(用于检索)
    keywords TEXT                   -- 关键词
);

-- 审计项-制度映射表
audit_item_policy_mapping (
    id INTEGER PRIMARY KEY,
    item_id INTEGER,                -- 审计项ID
    clause_id INTEGER,              -- 制度条款ID
    match_type TEXT,                -- direct/partial/indirect/none
    match_score REAL,               -- 匹配分数0-100
    gaps TEXT,                      -- 差距描述(JSON)
    recommendation TEXT,            -- 调整建议
    suggested_content TEXT          -- 建议的条款内容
);

-- 制度差距表
policy_gaps (
    id INTEGER PRIMARY KEY,
    item_id INTEGER,                -- 审计项ID
    gap_type TEXT,                  -- 缺失/不完善/不符合
    severity TEXT,                  -- 高/中/低
    description TEXT,               -- 差距描述
    target_policy TEXT,             -- 目标制度
    target_clause TEXT,             -- 目标条款位置
    suggested_content TEXT          -- 建议内容
);
```

## 七、核心类设计

### 7.1 已实现类

```python
# 1. PolicyVectorScreener - 向量筛选器
class PolicyVectorScreener:
    """制度要求向量筛选器 - 向量语义匹配 + 置信度分级"""
    
    HIGH_CONFIDENCE_THRESHOLD = 0.70   # 高置信度阈值
    LOW_CONFIDENCE_THRESHOLD = 0.45    # 低置信度阈值
    
    def __init__(self):
        # 复用模块1的SemanticMatcher
        pass
    
    def screen(self, items: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        向量语义筛选 + 置信度分级
        Returns: (高置信度结果, 中置信度结果)
        """
        pass

# 2. PolicyRequirementExtractor - 制度要求提取器
class PolicyRequirementExtractor:
    """制度要求提取器 - 向量+LLM两阶段"""
    
    def __init__(self, db_path: str, force_full: bool = False):
        pass
    
    def extract(self) -> str:
        """执行提取流程"""
        pass

# 3. PolicyDatabaseManager - 数据库管理器
class PolicyDatabaseManager:
    """制度合规检查数据库管理器"""
    
    def save_screening_result(self, result: Dict) -> int:
        """保存筛选结果"""
        pass
    
    def get_screened_item_ids(self) -> Set[int]:
        """获取已筛选的审计项ID集合"""
        pass
```

### 7.2 待实现类

```python
# 1. PolicyParser - 制度解析器
class PolicyParser:
    def parse(self, file_path: str) -> PolicyDocument
    def extract_clauses(self, doc: PolicyDocument) -> List[Clause]

# 2. ClauseIndexer - 条款索引器
class ClauseIndexer:
    def build_index(self, clauses: List[Clause]) -> FAISS.Index
    def search(self, query: str, top_k: int = 10) -> List[Clause]
    def keyword_search(self, keywords: List[str]) -> List[Clause]

# 3. ComplianceChecker - 完备性检查器
class ComplianceChecker:
    def check(self, audit_items: List[AuditItem]) -> CheckResult
    def _analyze_single_item(self, item: AuditItem, candidates: List[Clause]) -> Mapping

# 4. LLMAnalyzer - LLM分析器
class LLMAnalyzer:
    def analyze_match(self, item: AuditItem, clauses: List[Clause]) -> AnalysisResult
    def generate_recommendation(self, gap: Gap) -> Recommendation

# 5. ReportGenerator - 报告生成器
class ReportGenerator:
    def generate_json(self, result: CheckResult) -> str
    def generate_word(self, result: CheckResult) -> str
```

## 八、数据分析器

模块2内置数据分析器，位于 `scripts/analyzers/` 目录：

| 文件 | 功能 |
|------|------|
| policy_reporter.py | 策略报告生成（类型分布、维度覆盖度、置信度分析） |

**使用方法**:
```python
from skills.policy_compliance_checker.scripts.analyzers import PolicyRequirementReporter

reporter = PolicyRequirementReporter(extraction_result)
reporter.generate_html_report('output/policy_report.html')
```

## 九、命令行使用

```bash
# 制度要求提取（增量模式）
python -m knowledge_work_plugins.it_audit.skills.policy_compliance_checker.scripts.policy_extractor \
    --db-path "knowledge-work-plugins/it-audit/data/it_audit.db"

# 制度要求提取（强制全量）
python -m knowledge_work_plugins.it_audit.skills.policy_compliance_checker.scripts.policy_extractor \
    --db-path "knowledge-work-plugins/it-audit/data/it_audit.db" \
    --force-full

# 指定输出报告路径
python -m ... --output "reports/policy_check.json"
```

## 十、效率对比

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 阶段1处理 | LLM调用(50条/批) | 向量计算(秒级) | 90%+ |
| 阶段1耗时 | 50-150秒 | <5秒 | 95%+ |
| 高置信度处理 | 需要LLM | 直接确定 | 节省LLM调用 |
| LLM调用次数 | 9次 | 1-2次（仅中置信度） | 80%+ |
| 总处理时间 | 90-270秒 | 10-60秒 | 70%+ |
| 支持增量 | 否 | 是 | - |
| 结果可追溯 | 否 | 是 | - |

## 十一、版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| v3.0 | 2026-03-02 | 添加向量+LLM两阶段筛选方案，新增向量模板设计，更新数据库表结构 |
| v2.0 | 2026-03-02 | 文档重组，更新目录结构，添加分析器说明 |
| v1.0 | 2026-02-27 | 初始设计 |
