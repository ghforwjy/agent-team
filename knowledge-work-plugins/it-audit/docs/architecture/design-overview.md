# IT审计Agent 架构设计

> 版本: v3.0
> 最后更新: 2026-03-02

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
- 各模块独立运行
- 模块间通过标准JSON接口传递数据
- 每个模块可独立扩展和替换

**原则四：冲突可追溯**
- 记录每条审计项的来源
- 检测并记录冲突，支持人工审核和自动处理
- 保留历史版本，支持版本对比

### 1.2 总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     IT审计Agent架构                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│   │ 模块1:审计项收集 │    │ 模块2:策略合规   │    │场景测试器   │ │
│   │ (Item Collector)│    │(Compliance Check)│    │(Tester)    │ │
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

## 二、目录结构

```
knowledge-work-plugins/it-audit/
├── README.md                    # 主文档（文档索引入口）
├── docs/                        # 文档目录
│   ├── architecture/            # 架构设计
│   │   └── design-overview.md   # 本文档
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

## 三、模块说明

### 3.1 模块1：审计项收集器 (1-audit-item-collector)

负责从Excel文件中收集、清洗、存储审计项数据。

**核心功能**:
- Excel解析与列名映射
- 语义相似度匹配（向量模型）
- LLM校验（防止假阳性合并）
- 审计项与审计动作分离存储
- 来源追溯记录

**详细设计**: [module1-collector.md](./module1-collector.md)

### 3.2 模块2：策略合规检查器 (2-policy-compliance-checker)

负责从制度文档中提取审计要求，进行合规检查。

**核心功能**:
- 制度文档解析（Word/PDF）
- 条款索引与向量检索
- LLM深度分析匹配程度
- 差距分析与调整建议生成

**详细设计**: [module2-checker.md](./module2-checker.md)

### 3.3 场景测试器 (scenario-tester)

提供常态化场景测试功能，验证各模块功能的正确性。

**核心功能**:
- 模块1场景测试
- 模块2场景测试
- 测试结果报告生成

## 四、数据库设计

### 4.1 核心表结构

#### 审计维度表 (audit_dimensions)
```sql
CREATE TABLE audit_dimensions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    parent_id INTEGER,
    level INTEGER DEFAULT 1,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 审计项表 (audit_items)
```sql
CREATE TABLE audit_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code VARCHAR(30) UNIQUE NOT NULL,
    dimension_id INTEGER NOT NULL,
    title VARCHAR(500) NOT NULL,
    title_vector BLOB,
    description TEXT,
    severity VARCHAR(10),
    status VARCHAR(20) DEFAULT 'active',
    version VARCHAR(20) DEFAULT 'v1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 审计动作表 (audit_procedures)
```sql
CREATE TABLE audit_procedures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    procedure_text TEXT NOT NULL,
    procedure_type VARCHAR(50),
    procedure_vector BLOB,
    source_id INTEGER,
    is_primary BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 来源追溯表 (audit_item_sources)
```sql
CREATE TABLE audit_item_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    source_type VARCHAR(20) NOT NULL,
    source_file VARCHAR(200),
    source_sheet VARCHAR(100),
    source_row INTEGER,
    raw_title VARCHAR(200),
    import_batch VARCHAR(50),
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 五、数据库路径规则

> **重要**: 所有模块的数据库路径必须由调用者传入，不提供默认值。这是为了确保skills作为工具的独立性，由调用者决定数据存储位置。

**推荐路径约定**（调用者可自定义，但建议遵循以下约定）：

| 场景 | 推荐路径 | 说明 |
|------|----------|------|
| 正式使用 | `knowledge-work-plugins/it-audit/data/it_audit.db` | 项目标准数据库位置 |
| 测试使用 | `tests/test_data/test_it_audit.db` | 测试隔离，不影响正式数据 |

### 设计原则

1. **Skills是工具**: 数据库路径由调用者传入，模块自身不决定数据存储位置
2. **测试隔离**: 测试使用独立的测试数据库，不影响正式数据
3. **路径透明**: 调用者明确知道数据存储在哪里

## 六、数据流

```
输入层                    处理层                      输出层
─────────                ──────                      ──────

检查底稿Excel  ──▶  模块1:收集与标准化  ──▶  标准检查项库
                               │
                               ▼
                        向量模型初筛
                        LLM校验确认
                        入库SQLite
                               │
                               ▼              模块2:策略合规检查
被审计文档 ──────────────────────────────────────────────▶ 合规检查报告
(Word/PDF)                      │
                               ▼
                        文档解析
                        条款检索
                        LLM分析
```

## 七、技术选型

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 数据库 | SQLite | 轻量级，无需部署 |
| 向量模型 | paraphrase-multilingual-MiniLM-L12-v2 | 多语言支持，本地运行 |
| LLM | 豆包API | 用于校验和深度分析 |
| Excel解析 | openpyxl | 支持xlsx格式 |
| Word解析 | python-docx | 支持docx格式 |
| PDF解析 | pdfplumber | 稳定的PDF解析 |

## 八、版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| v3.0 | 2026-03-02 | 文档重组，更新目录结构，修正模块命名 |
| v2.3 | 2026-02-25 | 性能优化：向量模型批量初筛 + LLM批量校验 |
| v2.2 | 2026-02-25 | LLM校验设计：新增LLM二次校验机制 |
| v2.1 | 2026-02-25 | 模块一详细设计：新增audit_procedures表 |
| v2.0 | 2026-02-25 | 重新设计，采用SQLite数据库，三模块架构 |
| v1.0 | 2026-02-25 | 初始版本 |
