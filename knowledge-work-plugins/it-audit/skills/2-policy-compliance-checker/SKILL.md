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

**制度解析内容提取**：
- 制度名称和版本
- 章节结构
- 条款内容（条款编号、条款标题、条款正文）
- 责任部门和执行要求

```python
from policy_parser import PolicyParser

parser = PolicyParser()
policy_docs = parser.parse_policy_folder("制度文件/")

for doc in policy_docs:
    print(f"制度: {doc['name']}")
    for clause in doc['clauses']:
        print(f"  条款 {clause['number']}: {clause['title']}")
```

### 步骤3: 智能匹配分析

使用LLM分析审计项与制度条款的匹配关系：

**匹配维度**：
1. **直接匹配** - 制度条款直接满足审计项要求
2. **部分匹配** - 制度条款部分满足，需要完善
3. **间接匹配** - 通过其他相关条款间接满足
4. **无匹配** - 制度中缺乏对应条款

**LLM分析Prompt示例**：

```
请分析以下审计项要求与制度条款的匹配程度：

【审计项要求】
维度: {dimension}
审计项: {title}
审计程序: {audit_procedure}

【待匹配制度条款】
{clause_list}

请输出JSON格式结果：
{
  "matched_clauses": [
    {
      "clause_number": "条款编号",
      "clause_title": "条款标题",
      "match_type": "direct|partial|indirect|none",
      "match_score": 0-100,
      "analysis": "匹配分析说明",
      "gaps": ["差距1", "差距2"]
    }
  ],
  "overall_assessment": "总体评估",
  "recommendation": "建议"
}
```

### 步骤4: 生成检查报告

输出制度完备性检查报告：

```
📋 制度完备性检查报告

📊 总体评估:
  审计项总数: 150
  已覆盖: 120 (80%)
  部分覆盖: 20 (13.3%)
  未覆盖: 10 (6.7%)
  总体符合度: 86.7%

📑 制度覆盖情况:
  ├─ 《信息安全管理制度》: 覆盖 45/50 项
  ├─ 《网络安全管理办法》: 覆盖 38/50 项
  ├─ 《数据安全管理制度》: 覆盖 25/30 项
  └─ 《系统运维管理制度》: 覆盖 12/20 项

⚠️ 不符合项清单 (10项):

  【高优先级】
  1. 审计项: 重要系统访问控制
     维度: XC重要信息系统管理
     问题: 制度中未明确重要系统的访问审批流程
     依据: 审计程序要求"检查重要系统访问是否经过审批"
     建议: 在《信息安全管理制度》第X章增加"重要系统访问审批"条款
     建议内容: [具体内容]

  2. 审计项: 数据备份策略
     维度: XC数据安全管理
     问题: 现有制度仅规定定期备份，未明确RPO/RTO要求
     依据: 审计程序要求"检查数据备份是否满足业务连续性要求"
     建议: 修订《数据安全管理制度》第X条，补充RPO/RTO指标要求
     建议内容: [具体内容]

  【中优先级】
  ...

📋 缺失制度清单 (3项):
  1. 维度: XC网络安全管理
     缺失内容: 供应链安全管理制度
     涉及审计项: 供应商安全评估、第三方接入管理
     建议: 新建《供应链安全管理制度》

✅ 制度调整建议汇总:
  共需调整: 15处
  - 新增制度: 3个
  - 修订条款: 10处
  - 补充说明: 2处
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

### policy_gaps (制度差距表)
```sql
- id: 主键
- item_id: 审计项ID
- gap_type: 差距类型(缺失/不完善/不符合)
- severity: 严重程度(高/中/低)
- description: 差距描述
- related_policy: 相关制度
- recommendation: 调整建议
- priority: 优先级
```

## 命令行使用

```bash
# 检查制度完备性
python knowledge-work-plugins/it-audit/skills/2-policy-compliance-checker/scripts/checker.py --policy-folder "制度文件/"

# 指定输出报告路径
python .../checker.py --policy-folder "制度文件/" --output "reports/policy_check_20240227.json"

# 仅检查特定维度
python .../checker.py --policy-folder "制度文件/" --dimension "XC网络安全管理"

# 应用检查结果到数据库
python .../checker.py --policy-folder "制度文件/" --apply
```

## 输出JSON结构

```json
{
  "version": "1.0",
  "created_at": "2024-02-27T10:30:00",
  "summary": {
    "total_audit_items": 150,
    "covered_items": 120,
    "partially_covered": 20,
    "uncovered_items": 10,
    "compliance_score": 86.7
  },
  "policy_coverage": [
    {
      "policy_name": "信息安全管理制度",
      "total_clauses": 35,
      "covered_items": 45,
      "coverage_rate": 90.0
    }
  ],
  "gaps": [
    {
      "item_id": "ITGC-001",
      "item_title": "重要系统访问控制",
      "dimension": "XC重要信息系统管理",
      "gap_type": "缺失",
      "severity": "高",
      "related_policy": "信息安全管理制度",
      "current_status": "制度中未明确重要系统的访问审批流程",
      "requirement": "审计程序要求检查重要系统访问是否经过审批",
      "recommendation": {
        "action": "新增条款",
        "target_policy": "信息安全管理制度",
        "target_clause": "第X章",
        "suggested_content": "重要系统访问应经过审批..."
      }
    }
  ],
  "missing_policies": [
    {
      "dimension": "XC网络安全管理",
      "missing_content": "供应链安全管理制度",
      "related_items": ["供应商安全评估", "第三方接入管理"],
      "recommendation": "新建《供应链安全管理制度》"
    }
  ]
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
