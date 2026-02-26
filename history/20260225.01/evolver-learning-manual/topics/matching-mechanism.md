# 基因与胶囊的匹配机制

> 理解 Evolver 如何选择使用哪个基因或胶囊

---

## 核心概念

### 匹配优先级

Evolver 的匹配遵循 **"胶囊优先，基因兜底"** 的原则：

```
用户输入/场景
    ↓
1. 提取信号
    ↓
2. 匹配 Capsule（快速复用）✓ 成功 → 直接应用
    ↓ 失败
3. 匹配 Gene（获取策略）✓ 成功 → 按策略执行
    ↓ 失败
4. 使用默认策略
```

### 为什么这样设计？

| 优先级 | 原因 |
|--------|------|
| **Capsule 优先** | 胶囊是成功案例，直接复用最快 |
| **Gene 兜底** | 基因是策略模板，指导如何处理 |
| **默认策略** | 确保任何情况都有响应 |

---

## 详细解释

### 信号提取

匹配的第一步是从用户输入中提取**信号**（关键词、上下文）。

#### 信号类型

| 信号类别 | 示例 | 说明 |
|----------|------|------|
| **错误信号** | `error`, `exception`, `failed` | 表示出现问题 |
| **概念信号** | `是什么`, `概念`, `原理` | 表示知识性问题 |
| **技术信号** | `python`, `gene`, `capsule` | 表示具体技术 |
| **动作信号** | `修复`, `优化`, `重构` | 表示操作意图 |

#### 提取过程

```
用户输入: "我的 Python 代码报错了，ModuleNotFoundError"
    ↓
分词: ["我的", "Python", "代码", "报错", "ModuleNotFoundError"]
    ↓
关键词匹配:
  - "Python" → python 信号
  - "报错" → error 信号
  - "ModuleNotFoundError" → import_error 信号
    ↓
信号列表: ["python", "error", "import_error"]
```

### 胶囊匹配

胶囊通过 `trigger` 字段定义触发条件。

#### 匹配逻辑

```javascript
function matchCapsule(signals, capsules) {
    for (const capsule of capsules) {
        // 计算匹配度
        const matched = capsule.trigger.filter(t => signals.includes(t));
        const score = matched.length / capsule.trigger.length;
        
        // 匹配度超过阈值（如 0.6）则认为匹配成功
        if (score >= 0.6) {
            return capsule;
        }
    }
    return null;
}
```

#### 示例匹配

```
信号: ["python", "error", "import_error", "ModuleNotFoundError"]

胶囊 A:
  trigger: ["python", "import", "ModuleNotFoundError"]
  匹配: ["python", "ModuleNotFoundError"] → 2/3 = 0.67 ✓

胶囊 B:
  trigger: ["gene", "capsule", "概念"]
  匹配: [] → 0/3 = 0 ✗

结果: 匹配胶囊 A
```

### 基因匹配

基因通过 `signals_match` 字段定义匹配的信号。

#### 匹配逻辑

```javascript
function matchGene(signals, genes) {
    return genes.filter(gene => {
        // 基因的信号是否被用户信号包含
        return gene.signals_match.some(s => signals.includes(s));
    });
}
```

#### 示例匹配

```
信号: ["是什么", "概念", "gene", "capsule"]

基因 A:
  signals_match: ["knowledge_question", "concept_explanation"]
  匹配: ["概念"] ✓

基因 B:
  signals_match: ["error", "exception", "failed"]
  匹配: [] ✗

基因 C:
  signals_match: ["gene", "capsule"]
  匹配: ["gene", "capsule"] ✓

结果: 匹配基因 A 和 C，按置信度排序
```

---

## 类比理解

### 医院分诊类比

| Evolver 组件 | 医院对应 | 作用 |
|--------------|----------|------|
| **信号提取** | 分诊台 | 了解症状，初步分类 |
| **Capsule 匹配** | 常见病例库 | 感冒、发烧等常见病直接给标准药方 |
| **Gene 匹配** | 专科医生 | 复杂病情按诊疗流程处理 |
| **默认策略** | 急诊 | 确保任何病人都能得到处理 |

### 流程示例

```
病人: "我感冒发烧了"
    ↓
分诊: 症状=["感冒", "发烧"]
    ↓
查常见病例库: ✓ 匹配 "感冒治疗方案"
    ↓
直接给标准药方（Capsule）

---

病人: "我胸闷、心悸、不明原因疼痛"
    ↓
分诊: 症状=["胸闷", "心悸", "疼痛"]
    ↓
查常见病例库: ✗ 无精确匹配
    ↓
转心内科（Gene: 心脏病诊疗流程）
    ↓
按流程检查→诊断→治疗
    ↓
治疗成功
    ↓
记录为新的常见病例（生成 Capsule）
```

---

## 实际示例

### 示例 1: 精确匹配胶囊

```
用户: "Gene 和 Capsule 是什么？"

信号提取:
  ["gene", "capsule", "是什么", "概念"]

胶囊匹配:
  capsule-gene-capsule-concept:
    trigger: ["gene", "capsule", "概念"]
    匹配度: 3/4 = 0.75 ✓

结果:
  直接返回话题文档内容
  不需要重新整理知识
```

### 示例 2: 匹配基因创建新内容

```
用户: "GEP 协议是什么？"

信号提取:
  ["gep", "protocol", "是什么", "概念"]

胶囊匹配:
  无精确匹配 ✗

基因匹配:
  gene_knowledge_accumulation:
    signals_match: ["knowledge_question", "concept_explanation"]
    匹配: ["是什么", "概念"] ✓

结果:
  执行知识积累策略:
    1. 解释 GEP 协议概念
    2. 整理成结构化文档
    3. 创建 topics/gep-protocol.md
    4. 更新 README.md 索引
    5. 生成胶囊 capsule-gep-protocol.json
```

### 示例 3: 处理错误

```
用户: "代码运行报错了"

信号提取:
  ["code", "error", "runtime"]

胶囊匹配:
  无精确匹配（太笼统）✗

基因匹配:
  gene_gep_repair_from_errors:
    signals_match: ["error", "exception", "failed"]
    匹配: ["error"] ✓

结果:
  执行错误修复策略:
    1. 分析错误类型
    2. 定位错误位置
    3. 编写修复代码
    4. 验证修复结果
```

---

## 最佳实践

### 如何设计好的触发条件

#### 胶囊 Trigger 设计

```json
{
  "trigger": ["python", "import", "ModuleNotFoundError"]
}
```

**原则**:
- **具体** - 包含技术栈、错误类型等具体信息
- **适度** - 3-5 个关键词，太少易误匹配，太多难匹配
- **分层** - 从通用到具体：`["python", "import", "ModuleNotFoundError"]`

#### 基因 Signals_Match 设计

```json
{
  "signals_match": ["knowledge_question", "concept_explanation"]
}
```

**原则**:
- **抽象** - 表示意图类别，而非具体内容
- **覆盖** - 涵盖多种表达方式
- **互斥** - 不同基因的信号尽量不重叠

### 匹配冲突处理

当多个胶囊或基因都匹配时：

```
胶囊 A: 匹配度 0.9
胶囊 B: 匹配度 0.7

选择: 胶囊 A（匹配度最高）
```

```
基因 A: 匹配信号 2 个
基因 B: 匹配信号 1 个

选择: 基因 A（匹配更多信号）
```

---

## 相关话题

- [Gene 与 Capsule](./gene-and-capsule.md) - 核心概念解析
- [Signal 信号系统](./signal-system.md) - 如何提取和使用信号
- [GEP 协议详解](./gep-protocol.md) - 进化协议的完整说明

---

*话题创建时间: 2026-02-24*
*最后更新: 2026-02-24*
