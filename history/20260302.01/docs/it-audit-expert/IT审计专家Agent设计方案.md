# IT审计专家Agent设计方案

> 版本: v2.3
> 创建日期: 2026-02-25
> 最后更新: 2026-02-25
> 状态: 设计中

---

## 一、设计原则

### 1.1 核心原则

**原则一：审计项标准化**
- 审计项（检查项）是核心资产，独立于数据来源
- 不同格式的Excel检查底稿只是数据输入方式
- 导入后统一清洗为标准格式

**原则二：数据统一管理**
- 使用SQLite数据库统一存储所有审计数据
- 避免JSON文件分散导致的维护困难
- 维度、大类、小类统一管理，修改一处全局生效

**原则三：模块解耦**
- 三个模块（收集、执行、报告）独立运行
- 模块间通过标准JSON接口传递数据
- 每个模块可独立扩展和替换

**原则四：冲突可追溯**
- 记录每条审计项的来源
- 检测并记录冲突，支持人工审核和自动处理
- 保留历史版本，支持版本对比

### 1.2 总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     IT审计专家Agent架构                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│   │ 模块1:审计项收集 │    │ 模块2:审计执行   │    │模块3:报告生成│ │
│   │ (Item Collector)│───▶│(Audit Executor) │───▶│(Reporter)   │ │
│   └────────┬────────┘    └────────┬────────┘    └──────┬──────┘ │
│            │                      │                      │        │
│            ▼                      ▼                      ▼        │
│   ┌─────────────────────────────────────────────────────────────┐ │
│   │                    SQLite 数据库                            │ │
│   │  ├─ 审计维度表        ├─ 检查项表         ├─ 法规依据表  │ │
│   │  ├─ 来源追溯表        ├─ 冲突记录表        ├─ 审计任务表  │ │
│   │  └─ 审计结果表                                           │ │
│   └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 数据流

```
输入层                    处理层                      输出层
─────────                ──────                      ──────

检查底稿Excel  ──▶  模块1:收集与标准化  ──▶  标准检查项库
                               │
                               ▼
                        冲突检测与处理
                        入库SQLite
                               │
                               ▼              模块2:审计执行
被审计文档 ──────────────────────────────────────────────▶ 审计结果
(Word/PDF)                      │
                               ▼
                        文档解析
                        语义匹配
                        符合性判断
                               │
                               ▼              模块3:报告生成
审计结果 ──────────────────────────────────────────────▶ 审计报告
                               │
                               ▼
                        模板填充
                        格式转换
```

---

## 二、数据库设计

### 2.1 数据库整体结构

```
knowledge-work-plugins/it-audit/
└── data/
    └── it_audit.db          # SQLite数据库文件
```

### 2.2 表结构定义

#### 2.2.1 审计维度表 (audit_dimensions)

```sql
CREATE TABLE audit_dimensions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) UNIQUE NOT NULL,      -- 维度编码：IT-GOV, ITGC-AC
    name VARCHAR(100) NOT NULL,           -- 维度名称
    parent_id INTEGER,                    -- 父维度ID，支持层级
    level INTEGER DEFAULT 1,               -- 层级：1-大类, 2-中类, 3-小类
    description TEXT,
    display_order INTEGER DEFAULT 0,       -- 显示顺序
    is_active BOOLEAN DEFAULT 1,         -- 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES audit_dimensions(id)
);

-- 初始化维度数据
INSERT INTO audit_dimensions (code, name, level, display_order) VALUES
    ('IT-GOV', 'IT治理', 1, 1),
    ('ITGC', 'IT一般控制', 1, 2),
    ('APP', '应用控制', 1, 3),
    ('DS', '数据安全', 1, 4),
    ('SD', '系统开发', 1, 5),
    ('COMP', '合规管理', 1, 6);

-- ITGC子维度
INSERT INTO audit_dimensions (code, name, parent_id, level, display_order)
SELECT 'ITGC-AC', '访问控制', id, 2, 1 FROM audit_dimensions WHERE code = 'ITGC';
INSERT INTO audit_dimensions (code, name, parent_id, level, display_order)
SELECT 'ITGC-CM', '变更管理', id, 2, 2 FROM audit_dimensions WHERE code = 'ITGC';
INSERT INTO audit_dimensions (code, name, parent_id, level, display_order)
SELECT 'ITGC-OPS', 'IT运维', id, 2, 3 FROM audit_dimensions WHERE code = 'ITGC';
```

#### 2.2.2 审计项表 (audit_items)

> **设计说明**: 审计项是核心实体，只存储审计问题本身。审计程序/动作单独存储在 audit_procedures 表中，支持一对多关系。

```sql
CREATE TABLE audit_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code VARCHAR(30) UNIQUE NOT NULL, -- 检查项编码：IT-GOV-001, ITGC-AC-001
    dimension_id INTEGER NOT NULL,         -- 关联维度ID
    title VARCHAR(500) NOT NULL,           -- 检查项标题（核心匹配字段）
    title_vector BLOB,                     -- 标题语义向量（用于相似度匹配）
    description TEXT,                      -- 检查内容描述
    criteria TEXT,                         -- 判断标准
    severity VARCHAR(10),                  -- 严重程度：高/中/低
    evidence_required TEXT,                -- 所需证据（JSON数组）
    status VARCHAR(20) DEFAULT 'active',   -- 状态：active/deprecated
    version VARCHAR(20) DEFAULT 'v1',      -- 版本号
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dimension_id) REFERENCES audit_dimensions(id)
);
```

#### 2.2.3 审计动作表 (audit_procedures) 【新增】

> **设计说明**: 一个审计项可以有多个审计动作，来自不同来源的底稿。通过语义匹配去重，逐步积累。

```sql
CREATE TABLE audit_procedures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,              -- 关联审计项ID
    procedure_text TEXT NOT NULL,          -- 审计程序/检查方法内容
    procedure_type VARCHAR(50),            -- 动作类型：查阅/访谈/测试/观察/分析
    procedure_vector BLOB,                 -- 审计程序语义向量
    source_id INTEGER,                     -- 关联来源记录ID
    is_primary BOOLEAN DEFAULT 0,          -- 是否为主要动作
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES audit_items(id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES audit_item_sources(id)
);

-- 索引
CREATE INDEX idx_procedures_item ON audit_procedures(item_id);
CREATE INDEX idx_procedures_type ON audit_procedures(procedure_type);
```

**数据关系示意**:
```
audit_items (审计项)
├── "公司是否建立IT治理委员会"
│   └── audit_procedures (审计动作)
│       ├── "查阅IT治理委员会成立发文" (来源: 2021底稿)
│       └── "检查公司是否制定IT治理委员会成立文件" (来源: 2022底稿)
```

#### 2.2.4 法规依据表 (regulatory_basis)

```sql
CREATE TABLE regulatory_basis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    law_name VARCHAR(100) NOT NULL,        -- 法规名称：网络安全法
    article VARCHAR(50),                   -- 条款编号：第21条
    content TEXT,                          -- 条款内容摘要
    FOREIGN KEY (item_id) REFERENCES audit_items(id)
);
```

#### 2.2.4 来源追溯表 (audit_item_sources)

```sql
CREATE TABLE audit_item_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,              -- 关联的标准化检查项ID
    source_type VARCHAR(20) NOT NULL,      -- 来源类型：excel/word/manual
    source_file VARCHAR(200),              -- 来源文件名
    source_sheet VARCHAR(100),             -- 来源Sheet名称
    source_row INTEGER,                    -- 来源行号
    raw_title VARCHAR(200),                -- 原始标题（未标准化前）
    raw_data TEXT,                         -- 原始完整数据（JSON）
    import_batch VARCHAR(50),              -- 导入批次号：20240225-001
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES audit_items(id)
);
```

#### 2.2.5 冲突记录表 (audit_item_conflicts)

```sql
CREATE TABLE audit_item_conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_a_id INTEGER NOT NULL,            -- 检查项A（已存在的）
    item_b_id INTEGER NOT NULL,            -- 检查项B（待入库的）
    conflict_type VARCHAR(20) NOT NULL,    -- 冲突类型：duplicate/similar/conflict
    similarity_score FLOAT,                -- 相似度分数（0-1）
    compare_fields TEXT,                   -- 比较的字段（JSON）
    conflict_details TEXT,                 -- 冲突详情（JSON）
    resolution VARCHAR(20),                -- 处理方式：pending/merge/keep_both/ignore_a/ignore_b
    resolved_by VARCHAR(50),               -- 处理人
    resolution_note TEXT,                 -- 处理备注
    resolved_at TIMESTAMP,
    FOREIGN KEY (item_a_id) REFERENCES audit_items(id),
    FOREIGN KEY (item_b_id) REFERENCES audit_items(id)
);
```

#### 2.2.6 审计任务表 (audit_tasks)

```sql
CREATE TABLE audit_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_code VARCHAR(50) UNIQUE NOT NULL, -- 任务编码：AUDIT-20240225-001
    task_name VARCHAR(200) NOT NULL,       -- 任务名称
    target_name VARCHAR(200),              -- 被审计对象名称
    target_type VARCHAR(50),               -- 被审计对象类型：制度/部门/系统
    target_files TEXT,                     -- 被审计文档路径（JSON数组）
    scope_dimensions TEXT,                 -- 审计范围涉及的维度ID（JSON数组）
    status VARCHAR(20) DEFAULT 'pending', -- pending/running/completed/cancelled
    auditor VARCHAR(50),                   -- 审计人员
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    note TEXT
);
```

#### 2.2.7 审计结果表 (audit_results)

```sql
CREATE TABLE audit_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,           -- 符合/部分符合/不符合/不适用
    finding TEXT,                          -- 审计发现描述
    evidence TEXT,                          -- 审计证据
    recommendation TEXT,                    -- 改进建议
    severity VARCHAR(10),                  -- 发现严重程度
    responsible_party VARCHAR(100),         -- 责任部门
    deadline DATE,                          -- 整改期限
    rectification_status VARCHAR(20),      -- 整改状态：pending/ongoing/completed
    auditor VARCHAR(50),                   -- 审计人员
    audited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES audit_tasks(id),
    FOREIGN KEY (item_id) REFERENCES audit_items(id)
);
```

### 2.3 索引设计

```sql
-- 检查项维度索引
CREATE INDEX idx_items_dimension ON audit_items(dimension_id);
CREATE INDEX idx_items_status ON audit_items(status);

-- 来源追溯索引
CREATE INDEX idx_sources_item ON audit_item_sources(item_id);
CREATE INDEX idx_sources_batch ON audit_item_sources(import_batch);

-- 冲突检测索引
CREATE INDEX idx_conflicts_type ON audit_item_conflicts(conflict_type);
CREATE INDEX idx_conflicts_resolution ON audit_item_conflicts(resolution);

-- 审计任务索引
CREATE INDEX idx_tasks_status ON audit_tasks(status);

-- 审计结果索引
CREATE INDEX idx_results_task ON audit_results(task_id);
CREATE INDEX idx_results_status ON audit_results(status);
```

---

## 三、模块设计

### 3.1 模块1：审计项收集器 (Audit Item Collector)

#### 3.1.1 功能概述

- 输入：各种格式的检查底稿Excel
- 处理：解析Excel → 列名映射 → **语义清洗** → 入库
- 输出：标准审计项库 + 审计动作库（SQLite）

**核心目标**：将各种来源的审计底稿清洗合并，形成统一的审计知识库：
- 相同审计项合并，不重复存储
- 不同审计动作积累到同一审计项下
- 支持语义相似度匹配，识别同义不同词的审计项

#### 3.1.2 清洗流程（详细设计）

```
┌─────────────────────────────────────────────────────────────────┐
│ 步骤1: Excel解析                                                 │
│    ├─ 读取Excel文件                                              │
│    ├─ 智能识别表头位置（扫描前10行）                             │
│    ├─ 列名映射到标准字段                                         │
│    └─ 过滤审计结果字段（检查结论、证据清单等不导入）             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 步骤2: 数据提取                                                  │
│    ├─ 提取字段：维度、审计项标题、审计程序                       │
│    ├─ 标题标准化：去除空格、标点、统一格式                       │
│    └─ 记录原始数据用于追溯                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 步骤3: 审计项语义匹配 【核心】                                   │
│    ├─ 计算新审计项标题的语义向量                                 │
│    ├─ 与数据库中已有审计项进行语义相似度匹配                     │
│    └─ 阈值判断：                                                 │
│        > 0.85: 高相似 → 视为同一审计项，进入步骤4                │
│        0.60-0.85: 中相似 → 人工确认                             │
│        < 0.60: 低相似 → 视为新审计项，进入步骤5A                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 步骤4: 审计动作匹配（审计项已存在时）                            │
│    ├─ 计算新审计程序的语义向量                                   │
│    ├─ 与该审计项下已有审计动作进行相似度匹配                     │
│    └─ 判断结果：                                                 │
│        > 0.80: 动作相似 → 跳过，只记录来源                       │
│        < 0.80: 动作不同 → 新增审计动作，进入步骤5B               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 步骤5A: 新建审计项                                               │
│    ├─ 写入 audit_items 表                                        │
│    ├─ 缓存标题语义向量                                           │
│    ├─ 创建审计动作记录                                           │
│    └─ 记录来源追溯                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 步骤5B: 新增审计动作                                             │
│    ├─ 写入 audit_procedures 表                                   │
│    ├─ 缓存动作语义向量                                           │
│    └─ 记录来源追溯                                               │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.1.3 语义匹配详细设计

**性能优化策略**:

> **核心问题**: 200条新 × 600条已有 = 120,000次比较，如果每次都调用LLM，成本和时间不可接受。
> 
> **解决方案**: 向量模型做初筛，LLM只校验候选结果。

**两阶段匹配流程**:

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

**向量模型批量匹配算法**:

```python
import numpy as np
from sentence_transformers import SentenceTransformer

def batch_match_items(new_titles: List[str], existing_items: List[dict], top_k: int = 3) -> Dict:
    """
    批量匹配审计项（向量模型）
    
    性能: 200条 × 600条 ≈ 10秒（本地模型）
    """
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    # 批量计算新审计项向量
    new_vectors = model.encode(new_titles, batch_size=32, show_progress_bar=True)
    
    # 获取已有审计项向量（优先使用缓存）
    existing_vectors = np.array([
        item.get('title_vector') or model.encode(item['title'])
        for item in existing_items
    ])
    
    # 矩阵乘法计算相似度（一次计算所有配对）
    similarity_matrix = np.dot(new_vectors, existing_vectors.T)
    
    # 为每条新审计项找到Top-K候选
    results = {}
    for i, new_title in enumerate(new_titles):
        top_indices = np.argsort(similarity_matrix[i])[-top_k:][::-1]
        results[new_title] = [
            {
                'item': existing_items[idx],
                'similarity': float(similarity_matrix[i][idx])
            }
            for idx in top_indices
            if similarity_matrix[i][idx] > 0.60  # 只保留相似度>0.60的
        ]
    
    return results
```

**LLM批量校验算法**:

```python
def batch_llm_verify(candidates: List[Dict], batch_size: int = 10) -> List[Dict]:
    """
    批量LLM校验（减少API调用次数）
    
    将多个校验任务合并到一个prompt中
    """
    results = []
    
    for i in range(0, len(candidates), batch_size):
        batch = candidates[i:i+batch_size]
        
        prompt = f"""
你是一个IT审计专家。请判断以下{len(batch)}对审计项是否应该合并。

{format_candidates_for_prompt(batch)}

请以JSON数组格式输出，每项包含：
- index: 序号
- should_merge: true/false
- reason: 简短理由（20字内）
"""
        
        response = llm.call(prompt)
        batch_results = parse_llm_response(response)
        results.extend(batch_results)
    
    return results
```

**调用次数估算**:

| 场景 | 向量比较次数 | LLM调用次数 | 说明 |
|------|-------------|-------------|------|
| 200条新，600条已有 | 120,000次 | 约5-10次 | 只对相似度>0.85的调用LLM |
| 预计高相似匹配 | - | 约20-50条 | 合并成5-10次批量调用 |
| 总成本 | 0元 | 约0.1-0.5元 | 本地向量模型免费 |

**审计项匹配算法（优化后）**:

```python
def match_audit_item(new_title: str, db_items: List[dict]) -> MatchResult:
    """
    审计项语义匹配
    
    Returns:
        MatchResult:
            - type: 'exact' | 'high_similar' | 'medium_similar' | 'new'
            - matched_item: 匹配到的审计项（如有）
            - similarity: 相似度分数 (0-1)
    """
    # 1. 完全匹配（标准化后字符串相同）
    normalized_new = normalize_text(new_title)
    for item in db_items:
        if normalize_text(item['title']) == normalized_new:
            return MatchResult('exact', item, 1.0)
    
    # 2. 语义相似度计算
    new_vector = model.encode(new_title)
    
    best_match = None
    best_score = 0.0
    
    for item in db_items:
        # 使用缓存的向量或重新计算
        item_vector = item.get('title_vector') or model.encode(item['title'])
        score = cosine_similarity(new_vector, item_vector)
        
        if score > best_score:
            best_score = score
            best_match = item
    
    # 3. 阈值判断
    if best_score > 0.85:
        return MatchResult('high_similar', best_match, best_score)
    elif best_score > 0.60:
        return MatchResult('medium_similar', best_match, best_score)
    else:
        return MatchResult('new', None, best_score)
```

**审计动作匹配算法**:

```python
def match_audit_procedure(new_procedure: str, existing_procedures: List[dict]) -> MatchResult:
    """
    审计动作语义匹配
    
    阈值说明：审计动作的相似度阈值比审计项更宽松
    因为同一审计项的不同动作可能有细微差异
    """
    if not existing_procedures:
        return MatchResult('new', None, 0.0)
    
    new_vector = model.encode(new_procedure)
    
    best_match = None
    best_score = 0.0
    
    for proc in existing_procedures:
        proc_vector = proc.get('procedure_vector') or model.encode(proc['procedure_text'])
        score = cosine_similarity(new_vector, proc_vector)
        
        if score > best_score:
            best_score = score
            best_match = proc
    
    # 审计动作阈值：0.80
    if best_score > 0.80:
        return MatchResult('similar', best_match, best_score)
    else:
        return MatchResult('new', None, best_score)
```

**相似度阈值配置**:

| 匹配对象 | 高相似阈值 | 中相似阈值 | 处理方式 |
|----------|-----------|-----------|----------|
| 审计项 | 0.85 | 0.60 | 高相似自动合并，中相似人工确认 |
| 审计动作 | 0.80 | - | 高相似跳过，低相似新增 |

#### 3.1.4 LLM校验设计

> **设计目的**: 向量模型只能计算语义相似度，无法进行逻辑判断。需要LLM对清洗结果进行二次校验，避免错误合并。

**校验时机**: 在语义匹配完成后、入库之前

**校验场景**:

| 场景 | 触发条件 | 校验目的 |
|------|----------|----------|
| 审计项合并校验 | 语义相似度 >= 0.85 | 确认是否真的是同一检查项 |
| 审计动作合并校验 | 语义相似度 >= 0.80 | 确认检查方法是否真的相同 |
| 维度一致性校验 | 审计项合并时维度不一致 | 确认维度分类是否合理 |

**校验流程**:

```
向量模型初筛
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 筛选需要LLM校验的候选                                        │
│   - 审计项: 相似度 >= 0.85                                   │
│   - 审计动作: 相似度 >= 0.80                                 │
│   - 维度: 不一致且相似度 >= 0.85                             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 批量LLM校验（一次性校验）                                    │
│   - 将筛选后的候选打包成JSON                                 │
│   - 使用详细的Prompt模板（含案例）                           │
│   - 一次LLM调用完成所有校验                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 应用校验结果                                                 │
│   - 解析LLM返回的JSON                                        │
│   - 应用到合并建议中                                         │
│   - 标记需要人工确认的项                                     │
└─────────────────────────────────────────────────────────────┘
```

**LLM校验Prompt模板（V2）**:

```python
PROMPT_TEMPLATE_V2 = """你是一个IT审计专家，负责审核审计项的合并决策是否正确。

## 待审核内容

我将提供三类需要审核的内容，请分别判断：

### 1. 审计项合并审核

以下审计项对被向量模型标记为"相似度>=0.85"，请判断是否真的是同一检查项：

{item_merges_json}

**判断标准：**
- **应该合并（reuse）**：检查重点相同、检查对象相同、只是表述不同
- **应该分离（create）**：检查重点不同、存在包含关系、检查角度不同

**典型案例参考：**
- 案例1（应合并）：
  - A: "公司是否建立IT治理委员会"
  - B: "是否设立IT治理委员会"
  - 判断：同一检查项，合并

- 案例2（应分离）：
  - A: "是否建立IT治理委员会"
  - B: "IT治理委员会是否有效运作"
  - 判断：A检查"有没有"，B检查"运作效果"，应分离

### 2. 审计动作合并审核

以下审计动作对被向量模型标记为"相似度>=0.80"，请判断是否真的是同一检查方法：

{procedure_merges_json}

**判断标准：**
- **应该复用（reuse_procedure）**：检查方法相同、检查对象相同
- **应该新建（create_procedure）**：检查方法不同、检查对象不同

**典型案例参考：**
- 案例1（应复用）：
  - A: "查阅IT治理委员会成立发文"
  - B: "检查公司是否制定IT治理委员会成立文件"
  - 判断：同一检查方法，复用

- 案例2（应新建）：
  - A: "查阅IT治理委员会成立发文"
  - B: "查阅IT治理委员会会议记录"
  - 判断：A查"成立文件"，B查"会议记录"，应新建

### 3. 维度一致性审核

以下审计项的维度分类可能存在不一致，请判断是否合理：

{dimension_checks_json}

**判断标准：**
- 根据审计项内容判断维度分类是否合理
- 如不合理，建议正确的维度

## 输出格式

请以JSON格式输出审核结果：

{{
    "review_status": "confirmed/adjusted",
    "item_merge_decisions": [
        {{
            "suggestion_id": "M001",
            "is_same_item": true/false,
            "decision": "reuse/create",
            "reason": "判断理由（30字内）"
        }}
    ],
    "procedure_merge_decisions": [
        {{
            "suggestion_id": "M001",
            "is_same_procedure": true/false,
            "decision": "reuse_procedure/create_procedure",
            "reason": "判断理由（30字内）"
        }}
    ],
    "dimension_adjustments": [
        {{
            "suggestion_id": "M001",
            "is_correct": true/false,
            "suggested_dimension": "建议的维度（如需调整）",
            "reason": "判断理由（30字内）"
        }}
    ]
}}
"""
```

**核心代码实现**:

```python
class LLMVerifier:
    def _filter_candidates_for_llm(self, merge_result: Dict) -> Dict:
        """
        筛选需要LLM校验的候选
        
        筛选条件：
        1. 审计项相似度 >= 0.85（高相似度，需要LLM确认）
        2. 审计动作相似度 >= 0.80（高相似度，需要LLM确认）
        3. 维度不一致但标题相似（相似度 >= 0.85）
        """
        candidates = {
            'item_merges': [],      # 需要校验的审计项合并
            'procedure_merges': [], # 需要校验的审计动作合并
            'dimension_checks': []  # 需要校验的维度
        }
        
        existing_items_cache = merge_result.get('existing_items_cache', {})
        
        for suggestion in merge_result.get('merge_suggestions', []):
            match_result = suggestion.get('match_result', {})
            
            # 1. 审计项合并候选（相似度>=0.85且action为reuse）
            if match_result.get('action') == 'reuse':
                similarity = match_result.get('similarity', 0)
                if similarity >= 0.85:
                    candidates['item_merges'].append({...})
                    
                    # 3. 维度不一致检查
                    existing_item_id = match_result.get('existing_item_id', '')
                    if existing_item_id in existing_items_cache:
                        existing_item = existing_items_cache[existing_item_id]
                        if existing_item.get('dimension') != new_item.get('dimension'):
                            candidates['dimension_checks'].append({...})
            
            # 2. 审计动作合并候选（相似度>=0.80且action为reuse_procedure）
            procedure_match = suggestion.get('procedure_match', {})
            if procedure_match and procedure_match.get('action') == 'reuse_procedure':
                proc_similarity = procedure_match.get('similarity', 0)
                if proc_similarity >= 0.80:
                    candidates['procedure_merges'].append({...})
        
        return candidates
    
    def _build_verification_prompt(self, candidates: Dict) -> str:
        """构建校验Prompt"""
        item_merges_json = json.dumps(candidates.get('item_merges', []), ...)
        procedure_merges_json = json.dumps(candidates.get('procedure_merges', []), ...)
        dimension_checks_json = json.dumps(candidates.get('dimension_checks', []), ...)
        
        return self.PROMPT_TEMPLATE_V2.format(...)
    
    def apply_detailed_adjustments(self, merge_result: Dict, review_result: Dict) -> Dict:
        """应用详细审核调整到合并建议"""
        details = review_result.get('details', [])
        detail_map = {d['suggestion_id']: d for d in details}
        
        for suggestion in merge_result.get('merge_suggestions', []):
            sid = suggestion.get('suggestion_id')
            if sid in detail_map:
                detail = detail_map[sid]
                
                # 应用审计项决策
                item_decision = detail.get('item_decision')
                if item_decision:
                    suggestion['match_result']['action'] = item_decision
                
                # 应用程序决策
                procedure_decision = detail.get('procedure_decision')
                if procedure_decision and 'procedure_match' in suggestion:
                    suggestion['procedure_match']['action'] = procedure_decision
                
                # 应用维度调整
                dimension_adjustment = detail.get('dimension_adjustment')
                if dimension_adjustment:
                    suggestion['new_item']['dimension'] = dimension_adjustment
        
        return merge_result
```

**校验结果处理**:

| LLM判断 | 处理方式 |
|---------|----------|
| decision=reuse | 执行合并 |
| decision=create | 创建新记录 |
| procedure_decision=reuse_procedure | 复用审计动作 |
| procedure_decision=create_procedure | 新建审计动作 |
| dimension_adjustment有值 | 更新维度后入库 |

**典型错误案例**:

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

案例3: 维度错配
- 审计项: "是否制定网络安全应急预案"
- 自动归类维度: "IT运维"
- LLM判断: 应归入"事件与应急管理"
  - 该审计项更符合应急管理维度
```

#### 3.1.5 列名映射配置

```python
# 列名映射规则（可配置）
COLUMN_MAPPING = {
    "item_code": {
        "standard": "item_code",
        "aliases": ["问题序号", "检查项编号", "序号", "编号", "ID", "Control_ID"],
        "required": True,
        "auto_generate": True  # 如果没有，自动生成
    },
    "title": {
        "standard": "title",
        "aliases": ["标题", "检查项", "问题", "项目名称"],
        "required": True
    },
    "description": {
        "standard": "description",
        "aliases": ["存在问题", "检查内容", "描述", "问题描述", "详细描述"],
        "required": True
    },
    "dimension": {
        "standard": "dimension",
        "aliases": ["项目", "审计领域", "检查类别", "维度", "领域"],
        "required": True,
        "lookup": True  # 需要查维度表
    },
    "severity": {
        "standard": "severity",
        "aliases": ["严重程度", "风险等级", "重要性", "优先级"],
        "required": False,
        "default": "中"
    }
}

# 严重程度标准化映射
SEVERITY_MAPPING = {
    "高": ["高", "重大", "关键", "严重", "high", "critical", "major"],
    "中": ["中", "一般", "medium", "moderate"],
    "低": ["低", "轻微", "low", "minor"]
}
```

#### 3.1.4 冲突检测策略

**基于语义相似度的冲突检测**

使用Sentence-BERT模型计算审计项之间的语义相似度，而非简单的字符匹配。

```python
# 相似度计算引擎配置
SIMILARITY_ENGINE = {
    "model": {
        "name": "paraphrase-multilingual-MiniLM-L12-v2",
        "type": "sentence-transformer",
        "language": "multilingual",
        "vector_dim": 384,
        "description": "多语言句子编码模型，支持中文语义理解",
        "local_path": "model/Sentence-BERT"  # 本地模型路径
    },

    "alternative_models": {
        "chinese_optimized": "shibing624/text2vec-base-chinese",
        "lightweight": "distiluse-base-multilingual-cased-v2",
        "api_based": "openai/text-embedding-ada-002"
    },

    "computation": {
        "method": "cosine_similarity",
        "batch_size": 32,
        "device": "auto",  # auto/cpu/cuda
        "cache_embeddings": True  # 缓存向量避免重复计算
    }
}

# 冲突检测配置
CONFLICT_DETECTION = {
    # 完全重复：标题和描述完全相同
    "duplicate": {
        "enabled": True,
        "fields": ["title", "description"],
        "action": "merge"  # 自动合并
    },
    
    # 语义相似检测：使用Sentence-BERT
    "semantic_similar": {
        "enabled": True,
        "algorithm": "sentence_bert",
        "thresholds": {
            "high": 0.85,     # >85%：高相似，自动合并
            "medium": 0.60,   # 60-85%：中相似，人工审核
            "low": 0.60       # <60%：低相似，视为不同检查项
        },
        "fields": ["title", "procedure"],  # 对比审计项标题和审计程序
        "action": "manual_review"  # 中相似度需要人工审核
    },
    
    # 维度冲突：同一检查项在不同维度
    "dimension_conflict": {
        "enabled": True,
        "condition": "same_title_diff_dimension",
        "action": "manual_review"
    }
}

# 语义相似度计算示例
"""
示例1：高相似（>85%）
- 审计项A: "公司是否设置首席信息官岗位"
- 审计项B: "是否设立CIO职位"
- 语义相似度: 92%（意思相同，用词不同）
- 处理: 自动合并

示例2：中相似（60-85%）
- 审计项A: "是否建立IT治理委员会"
- 审计项B: "IT治理委员会是否由高管组成"
- 语义相似度: 72%（相关但不完全相同）
- 处理: 人工审核

示例3：低相似（<60%）
- 审计项A: "是否制定网络安全保障方案"
- 审计项B: "是否定期对系统容量进行检查"
- 语义相似度: 35%（完全不同检查项）
- 处理: 视为新增审计项
"""

# 冲突处理选项
RESOLUTION_OPTIONS = {
    "merge": "合并检查项，保留标准ID",
    "keep_both": "保留两条检查项（视为不同检查点）",
    "keep_existing": "保留已有的，忽略新导入的",
    "keep_new": "保留新导入的，标记已有的为deprecated",
    "ignore": "忽略，不入库"
}
```

**语义相似度计算流程**

```python
class SemanticSimilarityCalculator:
    """基于Sentence-BERT的语义相似度计算器"""
    
    def __init__(self, model_name='paraphrase-multilingual-MiniLM-L12-v2'):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self.cache = {}  # 向量缓存
    
    def encode(self, text):
        """将文本编码为语义向量"""
        if text in self.cache:
            return self.cache[text]
        
        embedding = self.model.encode(text, convert_to_tensor=True)
        self.cache[text] = embedding
        return embedding
    
    def calculate_similarity(self, text1, text2):
        """计算两段文本的语义相似度"""
        from sentence_transformers import util
        
        emb1 = self.encode(text1)
        emb2 = self.encode(text2)
        
        # 计算余弦相似度
        cosine_score = util.cos_sim(emb1, emb2)
        return float(cosine_score[0][0])
    
    def find_best_matches(self, new_item, existing_items, top_k=5):
        """
        为新审计项找到最相似的已有审计项
        
        Returns:
            List[Tuple[item, similarity_score]]: 最相似的top_k个审计项
        """
        new_text = f"{new_item['title']} {new_item.get('procedure', '')}"
        new_emb = self.encode(new_text)
        
        scores = []
        for existing in existing_items:
            existing_text = f"{existing['title']} {existing.get('procedure', '')}"
            existing_emb = self.encode(existing_text)
            
            score = util.cos_sim(new_emb, existing_emb)
            scores.append((existing, float(score[0][0])))
        
        # 按相似度排序
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
```

**技术优势对比**

| 对比维度 | 字符匹配(SequenceMatcher) | 语义匹配(Sentence-BERT) |
|---------|--------------------------|------------------------|
| 匹配原理 | 编辑距离，看字符相同率 | 语义向量，看意思相近度 |
| 同义词处理 | 无法识别 | 可以识别（CIO=首席信息官）|
| 语序变化 | 敏感 | 鲁棒 |
| 计算速度 | 快 | 较慢（需模型推理）|
| 准确度 | 低（仅表面相似）| 高（真正语义相似）|
| 适用场景 | 精确匹配 | 语义去重、相似推荐 |

### 3.2 模块2：审计执行器 (Audit Executor)

#### 3.2.1 功能概述

- 输入：标准检查项（从SQLite）+ 被审计文档
- 处理：文档解析 → 语义匹配 → 符合性判断 → 证据提取
- 输出：审计结果（SQLite）

#### 3.2.2 处理流程

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 任务创建                                                      │
│    ├─ 接收被审计文档                                             │
│    ├─ 选择审计维度                                               │
│    └─ 创建审计任务记录                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. 文档解析                                                      │
│    ├─ Word文档解析                                               │
│    ├─ PDF文档解析（文字版/扫描版）                                │
│    └─ 文本提取和结构化                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. 语义匹配                                                      │
│    ├─ 分词和向量化                                               │
│    ├─ 相似度计算                                                 │
│    └─ 候选段落筛选                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. 符合性判断                                                    │
│    ├─ 逐项对照检查                                               │
│    ├─ 证据匹配                                                   │
│    └─ 结论确定                                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. 结果记录                                                      │
│    ├─ 写入审计结果表                                             │
│    ├─ 计算符合率                                                 │
│    └─ 生成审计摘要                                               │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.2.3 符合性判断标准

```python
# 符合性判断规则
COMPLIANCE_CRITERIA = {
    "符合": {
        "conditions": [
            "制度明确覆盖该检查项",
            "制度要求不低于检查标准",
            "有明确的执行记录"
        ],
        "evidence_required": ["制度条款", "执行记录"]
    },
    "部分符合": {
        "conditions": [
            "制度提及该检查项但不完整",
            "制度要求低于检查标准",
            "缺少明确的执行记录"
        ],
        "evidence_required": ["部分制度条款"]
    },
    "不符合": {
        "conditions": [
            "制度未覆盖该检查项",
            "制度要求与检查标准冲突",
            "存在违规行为"
        ],
        "evidence_required": []
    },
    "不适用": {
        "conditions": [
            "该检查项不适用于当前被审计对象",
            "业务场景不涉及该检查项"
        ],
        "evidence_required": []
    }
}
```

### 3.3 模块3：报告生成器 (Report Generator)

#### 3.3.1 功能概述

- 输入：审计结果（从SQLite）+ 报告模板
- 处理：模板填充 → 数据映射 → 格式转换
- 输出：审计报告（Word/Excel/PPT/PDF）

#### 3.3.2 支持的报告模板

| 模板类型 | 格式 | 用途 |
|---------|------|------|
| 整改报告 | Word | 向监管部门提交整改情况 |
| 审计工作底稿 | Excel | 审计过程记录和证据 |
| 管理层汇报 | PPT | 向管理层汇报审计结果 |
| 差距分析报告 | Word | 详细差距分析和建议 |
| 合规清单 | Excel | 逐项合规检查清单 |

#### 3.3.3 模板字段映射

```python
# 报告模板字段映射
TEMPLATE_MAPPING = {
    "整改报告": {
        "title": "审计发现与整改情况报告",
        "fields": {
            "audit_target": "target_name",
            "audit_date": "created_at",
            "findings_summary": "summary_findings",
            "compliance_rate": "compliance_rate",
            "findings": {
                "item": "title",
                "status": "status",
                "finding": "finding",
                "recommendation": "recommendation",
                "deadline": "deadline"
            }
        }
    },
    "审计工作底稿": {
        "sheet_name": "审计结果",
        "columns": [
            "检查项编码", "检查项标题", "维度",
            "符合性", "审计发现", "审计证据",
            "改进建议", "责任部门", "整改期限"
        ]
    }
}
```

---

## 四、Skill目录结构

```
knowledge-work-plugins/it-audit/
├── .claude-plugin/
│   └── plugin.json
│
├── commands/
│   ├── collect-audit-items.md      # 收集审计项命令
│   ├── run-audit.md                # 执行审计命令
│   └── generate-report.md          # 生成报告命令
│
├── skills/
│   │
│   ├── 1-audit-item-collector/     # 模块1：审计项收集
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   ├── column-mapping-guide.md
│   │   │   └── import-templates/
│   │   │       └── standard_template.xlsx
│   │   └── scripts/
│   │       ├── __init__.py
│   │       ├── collector.py
│   │       ├── excel_parser.py
│   │       ├── column_mapper.py
│   │       ├── conflict_detector.py
│   │       └── db_manager.py
│   │
│   ├── 2-audit-executor/           # 模块2：审计执行
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   ├── matching-rules.md
│   │   │   └── compliance-criteria.md
│   │   └── scripts/
│   │       ├── __init__.py
│   │       ├── executor.py
│   │       ├── document_parser.py
│   │       ├── semantic_matcher.py
│   │       ├── compliance_checker.py
│   │       └── db_manager.py
│   │
│   └── 3-report-generator/        # 模块3：报告生成
│       ├── SKILL.md
│       ├── references/
│       │   └── templates/
│       │       ├── rectification_report.docx
│       │       ├── audit_working_paper.xlsx
│       │       └── management_report.pptx
│       └── scripts/
│           ├── __init__.py
│           ├── generator.py
│           ├── template_engine.py
│           ├── format_converter.py
│           └── db_manager.py
│
└── data/
    ├── it_audit.db                 # SQLite数据库
    ├── import_templates/           # 导入模板
    └── report_templates/          # 报告模板
```

---

## 五、实施路线图

### 阶段1：基础框架（1周）

- [ ] 创建SQLite数据库结构
- [ ] 实现数据库管理模块
- [ ] 搭建三个模块的基础框架
- [ ] 实现基本的Excel解析功能

### 阶段2：模块1实现（2周）

- [ ] 实现列名映射配置
- [ ] 实现数据标准化
- [ ] 实现冲突检测
- [ ] 实现导入批次管理

### 阶段3：模块2实现（2周）

- [ ] 实现Word文档解析
- [ ] 实现PDF文档解析
- [ ] 实现语义匹配
- [ ] 实现符合性判断

### 阶段4：模块3实现（1周）

- [ ] 实现模板引擎
- [ ] 实现格式转换
- [ ] 制作标准报告模板

### 阶段5：测试与优化（1周）

- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化
- [ ] 用户验收

---

## 六、附录

### A. 数据库ER图

```
┌──────────────────┐       ┌──────────────────┐
│audit_dimensions │       │  audit_items     │
├──────────────────┤       ├──────────────────┤
│id (PK)           │◀──┐   │id (PK)           │
│code (UNIQUE)     │   │   │item_code(UNIQUE)│
│name              │   └───│dimension_id (FK) │
│parent_id (FK)    │       │title             │
│level             │       │description       │
│description       │       │severity          │
└──────────────────┘       │status            │
                          └────────┬─────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
┌──────────────────────┐ ┌──────────────────┐ ┌──────────────────────┐
│audit_item_sources   │ │regulatory_basis │ │ audit_item_conflicts │
├──────────────────────┤ ├──────────────────┤ ├──────────────────────┤
│id (PK)              │ │id (PK)          │ │id (PK)               │
│item_id (FK)         │ │item_id (FK)     │ │item_a_id (FK)        │
│source_type          │ │law_name         │ │item_b_id (FK)        │
│source_file          │ │article          │ │conflict_type         │
│source_row           │ │content          │ │similarity_score      │
│raw_data (JSON)      │ └──────────────────┘ │resolution            │
│import_batch         │                       └──────────────────────┘
└──────────────────────┘
              
              ┌────────────────────┐       ┌──────────────────────┐
              │   audit_tasks     │       │  audit_results      │
              ├────────────────────┤       ├──────────────────────┤
              │id (PK)            │◀──┐   │id (PK)              │
              │task_code(UNIQUE)  │   │   │task_id (FK)         │
              │task_name          │   └───│item_id (FK)         │
              │target_name        │       │status               │
              │status             │       │finding              │
              │auditor            │       │recommendation       │
              └────────────────────┘       └──────────────────────┘
```

### B. 配置示例

```python
# 数据库配置
DB_CONFIG = {
    "path": "knowledge-work-plugins/it-audit/data/it_audit.db",
    "backup_dir": "knowledge-work-plugins/it-audit/data/backups/"
}

# 列名映射配置（用户可自定义）
USER_COLUMN_MAPPING = {
    "dimension": {
        "aliases": ["审计领域", "项目", "检查类别"],
        "lookup": True
    },
    # 可添加更多自定义映射
}
```

### C. 版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| v2.3 | 2026-02-25 | **性能优化**：向量模型批量初筛 + LLM批量校验，大幅降低成本和时间 |
| v2.2 | 2026-02-25 | **LLM校验设计**：新增LLM二次校验机制，防止向量模型的假阳性合并 |
| v2.1 | 2026-02-25 | **模块一详细设计**：新增audit_procedures表，审计项与审计动作分离；完善语义清洗流程设计 |
| v2.0 | 2026-02-25 | 重新设计，采用SQLite数据库，三模块架构 |
| v1.0 | 2026-02-25 | 初始版本（已废弃） |

---

**文档结束**
