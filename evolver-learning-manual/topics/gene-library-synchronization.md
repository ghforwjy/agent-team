# 基因库同步问题

> 为什么不同智能体看到的基因数量不一致

---

## 问题现象

**用户反馈**：
> "我去问另一个智能体，他和你使用同一个evolver mcp服务，他的回答怎么还是只有4个基因"

**现象描述**：
- 智能体A（我）：报告5个基因
- 智能体B（另一个）：报告4个基因
- 两者使用同一个 Evolver MCP 服务

---

## 根本原因

### 基因存储的"分裂"设计

Evolver 基因库采用了**分散存储**的设计：

```
evolver/assets/gep/
├── genes.json                    ← 主索引文件
│   └── 包含：3个核心基因（实际应该包含全部）
│
└── genes/
    ├── gene_knowledge_accumulation.json    ← 独立文件
    └── gene_prevent_cognitive_bias.json    ← 独立文件
```

### 问题分析

| 问题 | 说明 |
|------|------|
| **主索引不完整** | `genes.json` 只包含3个核心基因，缺少独立文件中的基因 |
| **读取逻辑不一致** | 不同智能体可能采用不同的读取策略 |
| **缺乏同步机制** | 独立文件的基因没有自动同步到主索引 |

### 智能体行为差异

| 智能体 | 读取策略 | 看到的基因数 |
|--------|----------|--------------|
| 智能体A | 读取 `genes.json` + 扫描 `genes/` 目录 | 5个 |
| 智能体B | 只读取 `genes.json` | 4个 |

---

## 解决方案

### 方案1：统一主索引（已实施）

将所有基因定义统一到 `genes.json` 中：

```json
{
  "version": 1,
  "genes": [
    { "id": "gene_gep_repair_from_errors", ... },
    { "id": "gene_gep_optimize_prompt_and_assets", ... },
    { "id": "gene_gep_innovate_from_opportunity", ... },
    { "id": "gene_prevent_cognitive_bias", ... },      // ← 新增
    { "id": "gene_knowledge_accumulation", ... }       // ← 新增
  ]
}
```

**优点**：
- 所有智能体看到一致的基因库
- 读取逻辑简单可靠
- 易于版本控制

**缺点**：
- 文件体积增大
- 基因详细定义需要简化

### 方案2：建立索引同步机制

保持分散存储，但建立自动同步：

```javascript
// 伪代码：同步脚本
function syncGeneIndex() {
  const mainIndex = readJson('genes.json');
  const geneFiles = glob('genes/*.json');
  
  for (const file of geneFiles) {
    const gene = readJson(file);
    if (!mainIndex.genes.find(g => g.id === gene.id)) {
      mainIndex.genes.push(extractSummary(gene));
    }
  }
  
  writeJson('genes.json', mainIndex);
}
```

**优点**：
- 保留详细定义的独立文件
- 主索引保持轻量

**缺点**：
- 需要额外的同步步骤
- 可能出现同步延迟

### 方案3：动态扫描（推荐）

智能体启动时动态扫描所有基因文件：

```javascript
// 伪代码：动态加载
function loadAllGenes() {
  const genes = [];
  
  // 1. 读取主索引
  const mainIndex = readJson('genes.json');
  genes.push(...mainIndex.genes);
  
  // 2. 扫描独立文件
  const geneFiles = glob('genes/*.json');
  for (const file of geneFiles) {
    const gene = readJson(file);
    if (!genes.find(g => g.id === gene.id)) {
      genes.push(gene);
    }
  }
  
  return genes;
}
```

**优点**：
- 最灵活，支持动态扩展
- 不需要手动维护索引

**缺点**：
- 启动时间略增
- 需要处理重复和冲突

---

## 实施记录

### 修复操作（2026-02-24）

1. **问题识别**：发现 `genes.json` 缺少 `gene_knowledge_accumulation`
2. **修复措施**：将 `gene_knowledge_accumulation` 添加到 `genes.json`
3. **验证结果**：主索引现在包含全部5个基因

### 修复后的基因库

| # | 基因ID | 在主索引 | 在独立文件 |
|---|--------|----------|------------|
| 1 | `gene_gep_repair_from_errors` | ✅ | ❌ |
| 2 | `gene_gep_optimize_prompt_and_assets` | ✅ | ❌ |
| 3 | `gene_gep_innovate_from_opportunity` | ✅ | ❌ |
| 4 | `gene_knowledge_accumulation` | ✅ | ✅ |
| 5 | `gene_prevent_cognitive_bias` | ✅ | ✅ |

---

## 最佳实践建议

### 对于基因开发者

1. **创建新基因时**：
   - 同时更新 `genes.json` 主索引
   - 在 `genes/` 目录创建详细定义文件（可选）

2. **修改基因时**：
   - 检查所有存储位置的一致性
   - 更新版本号

### 对于智能体实现者

1. **读取基因库时**：
   ```javascript
   // 推荐：动态扫描策略
   const genes = loadAllGenes(); // 读取主索引 + 扫描目录
   ```

2. **缓存策略**：
   - 启动时加载全部基因
   - 运行时监听文件变化
   - 热更新基因库

---

## 相关话题

- [Evolver 架构解析](./evolver-architecture.md) - 分层架构理解
- [认知偏差预防机制](./cognitive-bias-prevention.md) - 第5个基因的设计

---

## 参考链接

- [基因主索引文件](../../evolver/assets/gep/genes.json)
- [基因独立文件目录](../../evolver/assets/gep/genes/)

---

*本话题记录了 Evolver 基因库同步问题的发现与解决*
*创建时间: 2026-02-24*
