# 模块1 测试场景设计

> 版本: v2.0
> 最后更新: 2026-03-02

## 一、测试数据

**测试数据位置**: `tests/test_data/`

| 文件 | 说明 |
|------|------|
| test_it_audit.db | 测试数据库 |
| audit_items_2021.xlsx | 2021年审计项数据 |
| audit_items_2022.xlsx | 2022年审计项数据 |

**运行命令**:
```bash
python tests/test_module1_cleaner.py
```

**测试结果输出**: `tests/results/`

## 二、测试场景

### 场景1：首次导入（空数据库）

**目的**: 验证基础导入功能

**步骤**:
1. 清空数据库（或新建测试数据库）
2. 从测试数据中提取2021年审计项并导入
3. 验证：
   - 所有审计项成功导入
   - 维度正确创建
   - 审计动作正确关联
   - 来源追溯记录完整

**预期结果**:
- 导入224条审计项
- 所有审计项使用 `create` 动作
- 224条来源追溯记录

### 场景2：增量导入（完全重复）

**目的**: 验证重复检测逻辑（向量模型初筛 + LLM最终判定）

**步骤**:
1. 在场景1基础上，再次导入相同的2021年审计项
2. 向量模型初筛：计算相似度≈1.0，建议`reuse`
3. LLM审核：对整个匹配结果进行审核
4. 执行`reuse`动作
5. 记录来源追溯

**预期结果**:
- 向量模型相似度≈1.0
- LLM判定：全部"是同一审计项"
- 最终动作：`reuse`
- 审计项数量不变，每条审计项有2条来源记录

### 场景3：跨年度导入（向量+LLM迭代审核）

**目的**: 验证向量模型+LLM迭代审核的完整流程

**步骤**:
1. 数据库已有2021年审计项
2. 从测试数据中提取2022年审计项并导入
3. 执行完整清洗流程：
   - 向量模型初筛
   - LLM审核
   - 根据审核意见调整
   - LLM再审核（最多3次循环）

**验证点**:

| 相似度范围 | 向量模型判断 | LLM审核 | 最终动作 |
|-----------|-------------|---------|---------|
| >0.85 | 建议reuse | 确认/调整 | reuse或create |
| 0.60-0.85 | pending_review | 判断 | 根据LLM建议决定 |
| <0.60 | create | 确认 | create |

**预期结果**:
- LLM能识别向量模型的误判
- 迭代调整机制正常工作
- 3次内审核通过

### 场景4：审计动作积累验证

**目的**: 验证同一审计项下多个审计动作的积累

**步骤**:
1. 完成场景3的导入
2. 查询数据库中通过`reuse`导入的审计项
3. 验证审计动作是否正确积累

**验证点**:
- 程序相似度<0.80时新增程序
- 程序相似度≥0.80时跳过
- 同一审计项可有多条来源记录

**数据库验证查询**:
```sql
SELECT 
    ai.id,
    ai.title,
    COUNT(ap.id) as procedure_count,
    GROUP_CONCAT(ap.procedure_text, ' | ') as procedures
FROM audit_items ai
JOIN audit_procedures ap ON ai.id = ap.item_id
GROUP BY ai.id
HAVING COUNT(ap.id) > 1;
```

### 场景5：边界情况测试

**目的**: 验证异常情况处理

| 测试项 | 测试数据 | 验证点 |
|--------|----------|--------|
| 空审计程序 | 审计程序为空的记录 | 正确处理空值，不报错 |
| 特殊字符 | 包含换行、引号的审计项 | 正确清洗和存储 |
| 超长文本 | 超过500字的审计项 | 正确截断或存储 |
| 维度变化 | 同标题不同维度 | 正确识别并记录 |

## 三、JSON格式规范

### 3.1 向量模型输出格式

```json
{
  "version": "1.0",
  "created_at": "ISO8601时间戳",
  "source_file": "源文件名",
  "summary": {
    "total_new_items": 224,
    "total_existing_items": 0,
    "suggested_new_items": 224,
    "suggested_reuse_items": 0,
    "pending_review": 0
  },
  "merge_suggestions": [
    {
      "suggestion_id": "M001",
      "new_item": {
        "title": "审计项标题",
        "dimension": "审计维度",
        "procedure": "审计程序"
      },
      "match_result": {
        "existing_item_id": "已有审计项ID（create时为null）",
        "similarity": 0.92,
        "action": "create 或 reuse"
      },
      "procedure_match": {
        "similarity": 0.75,
        "action": "create_procedure 或 reuse_procedure"
      }
    }
  ]
}
```

### 3.2 LLM审核输出格式

```json
{
  "review_status": "confirmed/adjusted/failed",
  "review_round": 1,
  "total_items": 224,
  "confirmed_items": 200,
  "adjusted_items": 24,
  "details": [
    {
      "suggestion_id": "M001",
      "is_same_item": true,
      "item_decision": "reuse",
      "item_reason": "判断理由",
      "is_same_procedure": false,
      "procedure_decision": "create",
      "procedure_reason": "判断理由"
    }
  ]
}
```

### 3.3 最终执行结果格式

```json
{
  "execution_status": "success/partial/failed",
  "total_items": 224,
  "created_items": 50,
  "reused_items": 174,
  "created_procedures": 80,
  "reused_procedures": 318,
  "source_records": 224,
  "failed_items": [],
  "execution_time": "120.5s"
}
```

## 四、成功标准

### 4.1 功能正确性

| 测试项 | 通过标准 |
|--------|---------|
| 首次导入 | 100%成功导入，无报错 |
| 重复检测 | 100%识别重复项，不新建审计项 |
| 向量+LLM迭代审核 | LLM能识别误判，3次内通过 |
| 审计动作积累 | 程序相似度<0.80时新增，≥0.80时跳过 |
| 来源追溯 | 每次导入都记录，同一审计项可有多条来源 |

### 4.2 性能指标

| 指标 | 目标值 |
|------|--------|
| 向量计算速度 | 224条×224条 < 30秒 |
| LLM调用次数 | 每轮审核 < 10次（批量调用） |
| 总处理时间 | 224条 < 2分钟（不含LLM）|

## 五、版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| v2.0 | 2026-03-02 | 文档重组，精简内容 |
| v1.0 | 2026-02-26 | 初始设计 |
