# IT审计专家Agent设计方案

> 版本: v2.0
> 创建日期: 2026-02-25
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

#### 2.2.2 检查项表 (audit_items)

```sql
CREATE TABLE audit_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code VARCHAR(30) UNIQUE NOT NULL, -- 检查项编码：IT-GOV-001, ITGC-AC-001
    dimension_id INTEGER NOT NULL,         -- 关联维度ID
    title VARCHAR(200) NOT NULL,           -- 检查项标题
    description TEXT,                       -- 检查内容描述
    audit_procedure TEXT,                   -- 审计程序/检查方法
    criteria TEXT,                         -- 判断标准
    severity VARCHAR(10),                  -- 严重程度：高/中/低
    evidence_required TEXT,                -- 所需证据（JSON数组）
    status VARCHAR(20) DEFAULT 'active',   -- 状态：active/deprecated
    version VARCHAR(20) DEFAULT 'v1',     -- 版本号
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dimension_id) REFERENCES audit_dimensions(id)
);
```

#### 2.2.3 法规依据表 (regulatory_basis)

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
- 处理：解析Excel → 列名映射 → 数据清洗 → 冲突检测 → 入库
- 输出：标准检查项库（SQLite）

#### 3.1.2 处理流程

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Excel解析                                                     │
│    ├─ 读取Excel文件                                             │
│    ├─ 识别Sheet结构                                              │
│    └─ 提取原始数据                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. 列名映射配置                                                  │
│    ├─ 系统预设标准列名                                           │
│    ├─ 用户自定义映射规则                                         │
│    └─ 映射示例：                                                 │
│       原始列名 "存在问题" ──▶ 标准字段 "description"             │
│       原始列名 "问题序号" ──▶ 标准字段 "item_code"              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. 数据标准化                                                    │
│    ├─ 字段提取与映射                                             │
│    ├─ 数据类型校验                                               │
│    └─ 必填字段检查                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. 冲突检测与处理                                               │
│    ├─ 完全重复检测                                               │
│    ├─ 相似度检测                                                 │
│    └─ 维度冲突检测                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. 入库                                                          │
│    ├─ 写入检查项表                                               │
│    ├─ 写入法规依据表                                             │
│    ├─ 写入来源追溯表                                             │
│    └─ 生成导入批次号                                             │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.1.3 列名映射配置

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
        "description": "多语言句子编码模型，支持中文语义理解"
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
| v2.0 | 2026-02-25 | 重新设计，采用SQLite数据库，三模块架构 |
| v1.0 | 2026-02-25 | 初始版本（已废弃） |

---

**文档结束**
