---
name: policy-compliance-checker
description: 制度完备性检查器，根据审计项要求对制度文档进行符合性分析，识别制度缺失和不符合项，给出精确到条款级别的调整建议。
---

# 制度完备性检查器 Skill

你是一个IT审计专家助手，负责帮助用户检查现有制度与审计项要求的符合程度，识别制度差距并给出调整建议。

## 核心能力

1. **制度解析** - 自动解析Word、PDF、Excel等格式的制度文档
2. **智能匹配** - 将审计项要求与制度条款进行智能匹配
3. **差距分析** - 识别制度缺失、不符合、不完善的地方
4. **精准建议** - 给出精确到制度、条款级别的调整建议

## 模块结构

```
2-policy-compliance-checker/
├── SKILL.md                    # 本文档
├── __init__.py
└── scripts/
    ├── __init__.py
    ├── policy_extractor.py     # 策略要求提取器（主功能）
    └── analyzers/              # 数据分析子模块
        ├── __init__.py
        └── policy_reporter.py  # 策略报告生成器
```

## 工作流程

### 步骤1: 读取审计项要求

从数据库读取所有审计项及其要求：

```python
from db_manager import DatabaseManager

db = DatabaseManager()
audit_items = db.get_all_audit_items()

for item in audit_items:
    print(f"审计项: {item['title']}")
    print(f"维度: {item['dimension']}")
    print(f"审计程序: {item['audit_procedure']}")
```

### 步骤2: 解析制度文档

支持解析多种格式的制度文件：

| 格式 | 扩展名 | 解析方式 |
|------|--------|----------|
| Word | .docx, .doc | python-docx |
| PDF | .pdf | PyPDF2/pdfplumber |
| Excel | .xlsx, .xls | pandas/openpyxl |
| 文本 | .txt, .md | 直接读取 |

### 步骤3: 智能匹配分析

使用LLM分析审计项与制度条款的匹配关系：

**匹配维度**：
1. **直接匹配** - 制度条款直接满足审计项要求
2. **部分匹配** - 制度条款部分满足，需要完善
3. **间接匹配** - 通过其他相关条款间接满足
4. **无匹配** - 制度中缺乏对应条款

### 步骤4: 生成检查报告

使用 `analyzers/policy_reporter.py` 生成报告：

```python
from analyzers.policy_reporter import PolicyRequirementReporter

reporter = PolicyRequirementReporter(result_file)
reporter.print_summary()        # 控制台摘要
reporter.export_csv(output_path) # CSV导出
reporter.generate_html_report(html_path) # HTML报告
```

## 数据库结构扩展

### policy_documents (制度文档表)
```sql
- id: 主键
- doc_code: 制度编码
- doc_name: 制度名称
- doc_version: 版本号
- doc_type: 制度类型(管理办法/实施细则/操作规范)
- effective_date: 生效日期
- file_path: 文件路径
- status: 状态(有效/废止/修订中)
```

### policy_clauses (制度条款表)
```sql
- id: 主键
- doc_id: 关联制度文档
- clause_number: 条款编号(如: 第5条、5.2)
- clause_title: 条款标题
- clause_content: 条款内容
- parent_clause: 父条款编号
- keywords: 关键词(用于快速检索)
```

### audit_item_policy_mapping (审计项制度映射表)
```sql
- id: 主键
- item_id: 审计项ID
- clause_id: 制度条款ID
- match_type: 匹配类型(direct/partial/indirect/none)
- match_score: 匹配分数(0-100)
- analysis: 匹配分析
- gaps: 差距描述(JSON)
- recommendation: 调整建议
- status: 处理状态(待处理/已采纳/已忽略)
```

## 命令行使用

```bash
# 检查制度完备性
python knowledge-work-plugins/it-audit/skills/2-policy-compliance-checker/scripts/policy_extractor.py --db-path "data/it_audit.db"

# 指定输出报告路径
python .../policy_extractor.py --output "reports/policy_check.json"

# 仅检查特定维度
python .../policy_extractor.py --dimension "XC网络安全管理"
```

## 输出JSON结构

```json
{
  "version": "1.0",
  "batch_info": {
    "batch_id": "POLICY-20260302-XXXXXX",
    "extract_time": "2026-03-02T10:30:00",
    "total_batches": 3,
    "items_processed": 224
  },
  "summary": {
    "total_requirements_found": 85,
    "by_type": {
      "建立制度": 25,
      "定期执行": 20,
      "人员配备": 15,
      "岗位分离": 10,
      "文件保存": 10,
      "建立组织": 5
    }
  },
  "policy_requirements": [...]
}
```

## 注意事项

1. **制度版本管理**
   - 记录制度版本号，确保检查结果与特定版本关联
   - 制度更新后需要重新检查

2. **匹配精度**
   - LLM匹配结果需要人工复核
   - 对于关键制度条款建议人工确认

3. **优先级划分**
   - 高优先级：涉及核心控制要求、法规强制要求
   - 中优先级：涉及重要控制要求
   - 低优先级：优化性建议

4. **建议可执行性**
   - 建议应具体到条款级别
   - 提供建议的条款内容草稿
   - 明确责任部门和完成时限
