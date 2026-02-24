# Gene 与 Capsule

> Evolver 核心概念解析：策略模板与成功案例

---

## 核心概念

### 是什么？

**Gene（基因）** 和 **Capsule（胶囊）** 是 Evolver 自我进化系统的两大核心组件，分别代表**策略模板**和**成功案例**。

### 关键要点

- **Gene** = 面对某类问题的**标准处理流程**（How to do）
- **Capsule** = 某个具体问题的**成功解决记录**（What was done）
- Gene 指导行动，Capsule 加速复用
- 两者配合实现知识的积累和传承

---

## 详细解释

### Gene（基因）

#### 定义
Gene 是**进化策略的模板**，定义了面对特定信号时应该采取的行动方案。

#### 结构组成

```json
{
  "type": "Gene",
  "id": "gene_gep_repair_from_errors",
  "category": "repair",           // repair/optimize/innovate
  "signals_match": ["error", "exception"],
  "strategy": ["步骤1", "步骤2", ...],
  "constraints": {"max_files": 20},
  "validation": ["验证命令"]
}
```

#### 作用
1. **标准化处理** - 同类问题有标准解法
2. **知识传承** - 成功经验可复用
3. **自动决策** - 根据信号自动选择策略

### Capsule（胶囊）

#### 定义
Capsule 是**成功案例的快照**，记录了某个具体问题是如何被解决的。

#### 结构组成

```json
{
  "type": "Capsule",
  "id": "capsule_python_import_error",
  "trigger": ["python", "import", "ModuleNotFoundError"],
  "gene": "gene_gep_repair_from_errors",
  "summary": "Python 导入错误的标准修复流程",
  "confidence": 0.95,
  "blast_radius": {"files": 2, "lines": 10}
}
```

#### 作用
1. **快速匹配** - 遇到类似问题快速找到方案
2. **经验积累** - 记录成功修复案例
3. **避免重复推理** - 不需要每次都从头分析

### Gene vs Capsule 对比

| 特性 | Gene | Capsule |
|------|------|---------|
| **本质** | 策略模板 | 成功案例 |
| **内容** | 处理步骤 | 解决结果 |
| **复用方式** | 按步骤执行 | 直接应用方案 |
| **创建时机** | 预定义/手动创建 | 成功解决问题后自动生成 |
| **数量** | 较少（几十到几百） | 较多（可以成千上万） |

---

## 类比理解

### 生活类比

| 概念 | 类比 | 说明 |
|------|------|------|
| **Gene** | 菜谱 | 告诉你做菜的步骤和配料 |
| **Capsule** | 成品菜照片 | 记录这道菜的成功案例，下次可以直接参考 |
| **工作流程** | 厨师做菜 | 先看菜谱（Gene），做完拍照记录（Capsule） |

### 技术类比

| 概念 | 类比 | 说明 |
|------|------|------|
| **Gene** | 设计模式 | 解决某类问题的通用方案 |
| **Capsule** | 代码片段 | 某个具体问题的实现代码 |
| **关系** | 模式 vs 实现 | 设计模式指导代码实现 |

---

## 实际示例

### 示例 1: Python 导入错误

**第一次遇到（使用 Gene）**：
```
错误：ModuleNotFoundError: No module named 'pandas'
    ↓
匹配 Gene：gene_gep_repair_from_errors
    ↓
执行策略：
  1. 分析错误：缺少 pandas 包
  2. 定位：requirements.txt
  3. 修复：pip install pandas
  4. 验证：python -c "import pandas"
    ↓
解决成功
    ↓
生成 Capsule：capsule_python_import_error
```

**第二次遇到（使用 Capsule）**：
```
错误：ModuleNotFoundError: No module named 'numpy'
    ↓
匹配 Capsule：capsule_python_import_error（触发条件匹配）
    ↓
直接应用方案：pip install numpy
    ↓
快速解决（不需要重新推理）
```

### 示例 2: 代码重构

**Gene 指导重构流程**：
```
Gene: gene_refactoring_best_practice
Strategy:
  1. 识别代码坏味道
  2. 确定重构目标
  3. 编写测试用例
  4. 小步修改代码
  5. 运行测试验证
  6. 提交变更
```

**Capsule 记录成功案例**：
```
Capsule: capsule_refactor_long_method
Context: 将 200 行的函数拆分为 5 个小函数
Result: 代码可读性提升，测试覆盖率保持 100%
```

---

## 相关话题

- [GEP 协议详解](./gep-protocol.md) - Evolver 进化协议
- [Signal 信号系统](./signal-system.md) - 如何提取和使用信号
- [知识积累基因](../genes/gene_knowledge_accumulation.json) - 本手册的驱动基因

---

## 参考链接

- [Evolver GitHub](https://github.com/autogame-17/evolver)
- [EvoMap 网络](https://evomap.ai)

---

*话题创建时间: 2026-02-24*
*最后更新: 2026-02-24*
