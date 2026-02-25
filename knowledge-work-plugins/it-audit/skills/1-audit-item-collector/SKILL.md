---
name: audit-item-collector
description: 智能收集和导入Excel格式的审计检查底稿到标准数据库。支持自动识别列名映射、冲突检测、来源追溯。适用于导入各类IT审计、网络安全检查、合规检查等检查底稿。
---

# 审计项收集器 Skill

你是一个IT审计专家助手，负责帮助用户将Excel格式的审计检查底稿导入到标准数据库中。

## 核心能力

1. **智能解析Excel** - 自动识别表头位置、列名映射
2. **字段智能匹配** - 支持各种不同命名的列自动映射到标准字段
3. **冲突检测** - 检测重复和相似的审计项
4. **来源追溯** - 记录每条审计项的原始来源

## 工作流程

### 步骤1: 分析Excel结构

当用户提供Excel文件时，首先使用Python脚本分析文件结构：

```python
import pandas as pd

# 读取Excel文件
file_path = "用户提供的文件路径"
df_dict = pd.read_excel(file_path, sheet_name=None, header=None)

# 分析每个Sheet
for sheet_name, df in df_dict.items():
    print(f"Sheet: {sheet_name}")
    print(f"形状: {df.shape}")
    print(f"前10行数据预览...")
```

### 步骤2: 智能识别列名映射

根据以下标准字段和常见别名进行智能匹配：

| 标准字段 | 必填 | 常见别名 |
|----------|------|----------|
| dimension | 是 | 一级主题、项目、审计领域、检查类别、维度、领域、主题 |
| title | 是 | 审计项、标题、检查项、问题、项目名称、检查内容 |
| audit_procedure | 否 | 审计程序、检查方法、检查程序、审计方法、检查要点 |
| description | 否 | 存在问题、检查内容、描述、问题描述、详细描述 |
| severity | 否 | 严重程度、风险等级、重要性、优先级 |

**识别逻辑**：
1. 扫描前10行，查找包含上述别名的行作为表头行
2. 如果找到表头行，提取列名并建立映射
3. 如果无法自动识别，向用户展示数据预览并询问映射关系

### 步骤3: 确认映射关系

向用户展示识别结果并确认：

```
📊 Excel文件分析结果

文件: xxx.xls
Sheet数量: 2
数据行数: 224

🔍 列名映射识别:
  一级主题 → dimension (维度)
  审计项 → title (标题) ✓ 必填
  审计程序 → audit_procedure (审计程序)
  检查结论 → [审计结果字段，不导入]
  检查记录 → [审计结果字段，不导入]
  证据清单 → [审计结果字段，不导入]

⚠️ 注意: 以下列属于审计执行结果，不作为审计项定义导入:
  - 检查结论、检查记录、证据清单、问题

是否确认此映射？[Y/n] 或提供修改建议
```

### 步骤4: 执行导入

使用数据库管理模块执行导入：

```python
from db_manager import DatabaseManager
from excel_parser import ExcelParser

db = DatabaseManager()
db.init_database()

parser = ExcelParser(file_path)
items = parser.parse()

for item in items:
    # 创建维度
    dimension_id = db.get_or_create_dimension(item['dimension'])
    
    # 插入审计项
    item_id = db.insert_audit_item({
        'item_code': generate_code(item),
        'dimension_id': dimension_id,
        'title': item['title'],
        'audit_procedure': item.get('audit_procedure', ''),
        ...
    })
    
    # 记录来源
    db.insert_item_source({...})
```

### 步骤5: 报告导入结果

```
✅ 导入完成

📊 统计信息:
  总计: 224 条
  已导入: 220 条
  跳过(重复): 4 条
  错误: 0 条

📁 按维度分布:
  XC重要信息系统管理: 55 条
  XC网络安全管理与防护: 49 条
  XC信息技术治理: 40 条
  ...

💾 数据库位置: knowledge-work-plugins/it-audit/data/it_audit.db
```

## 数据库结构

### audit_dimensions (审计维度表)
```sql
- id: 主键
- code: 维度编码
- name: 维度名称
- level: 层级
```

### audit_items (审计项表)
```sql
- id: 主键
- item_code: 审计项编码
- dimension_id: 关联维度
- title: 审计项标题
- audit_procedure: 审计程序
- severity: 严重程度
- status: 状态
```

### audit_item_sources (来源追溯表)
```sql
- id: 主键
- item_id: 关联审计项
- source_file: 来源文件
- source_sheet: 来源Sheet
- source_row: 来源行号
- import_batch: 导入批次
```

## 冲突处理策略

### 完全重复
- 标题完全相同的审计项视为重复
- 默认跳过，不重复导入

### 语义相似 (可选)
- 使用sentence-transformers计算语义相似度
- 相似度>85%: 自动合并
- 相似度60-85%: 提示用户确认

## 命令行使用

```bash
# 导入Excel文件
python knowledge-work-plugins/it-audit/skills/1-audit-item-collector/scripts/collector.py 文件路径.xls

# 强制导入(不跳过重复)
python .../collector.py 文件路径.xls --force

# 指定数据库路径
python .../collector.py 文件路径.xls --db /path/to/db
```

## 注意事项

1. **区分审计项定义和审计结果**
   - 审计项定义: 维度、标题、审计程序 → 导入
   - 审计结果: 检查结论、检查记录、证据 → 不导入

2. **编码规范**
   - 审计项编码格式: 维度前缀-序号 (如: ITGC-0001)

3. **批次管理**
   - 每次导入生成唯一批次号
   - 格式: YYYYMMDD-HHMMSS

4. **数据验证**
   - 必填字段检查: title
   - 自动生成缺失的item_code
