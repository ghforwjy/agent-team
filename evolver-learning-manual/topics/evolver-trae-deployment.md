# Evolver 在 Trae 中的部署实践

> 完整的 MCP Server 部署流程、配置方法、进化流程和最佳实践

---

## 核心概念

### 是什么？

将 Evolver 自我进化引擎通过 **MCP (Model Context Protocol)** 协议集成到 Trae IDE 中，使 Trae 的 AI Agent 具备自我分析和持续进化的能力。

### 关键要点

- **MCP 协议** - 标准化的 AI 工具调用协议
- **MCP Server** - 本地运行的服务端，暴露 Evolver 能力
- **项目规则** - 指导 Trae Agent 自动使用 Evolver 工具
- **信号驱动** - 根据编程场景自动触发进化分析
- **完整进化流程** - 创建事件、胶囊、应用表观遗传标记

---

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────┐
│              Trae IDE                   │
│  ┌─────────┐      ┌─────────────────┐  │
│  │  Agent  │◄────►│   MCP Client    │  │
│  └─────────┘      └────────┬────────┘  │
└────────────────────────────┼───────────┘
                             │ MCP Protocol
┌────────────────────────────┼───────────┐
│         Evolver MCP Server │           │
│  ┌─────────────────────────┘           │
│  │  ┌──────────────┐  ┌─────────────┐ │
│  └──►│ 工具路由     │──►│ 进化引擎    │ │
│     └──────────────┘  └─────────────┘ │
│            │                │          │
│     ┌──────┴──────┐  ┌─────┴─────┐   │
│     │  Genes      │  │ Capsules  │   │
│     └─────────────┘  └───────────┘   │
└───────────────────────────────────────┘
```

### MCP 与 Evolver 协同机制

```
┌─────────────────────────────────────────────────────────────┐
│  用户完成编程任务                                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  analyze_session (MCP 工具)                                 │
│     ├── 提取信号 (error, pattern, change)                   │
│     ├── 选择匹配基因 (根据 signals_match)                   │
│     ├── 创建 mutation/personality_state                     │
│     └── 写入 last_run 状态                                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  evolve_capability (MCP 工具)                               │
│     ├── 创建 EvolutionEvent → events.jsonl                  │
│     ├── 创建 Capsule → capsules.json                        │
│     └── 应用表观遗传标记 → genes.json                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  优胜劣汰机制 (Evolver 核心)                                 │
│     ├── 成功强化基因 (+0.05 boost)                          │
│     ├── 失败抑制基因 (-0.1 boost)                           │
│     └── 连续失败封禁 (2次)                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## MCP Server 版本演进

### v1.0.0 的问题

| 工具 | 原始行为 | 缺失功能 |
|------|---------|---------|
| `analyze_session` | 只分析会话，返回信号 | 不创建 solidify 需要的状态文件 |
| `evolve_capability` | 只返回进化提示 | 不调用 solidify 执行进化 |

**结果**：
- 学习手册胶囊 ≠ 系统胶囊
- 没有进化事件记录
- 没有表观遗传标记

### v2.0.0 改进

```
analyze_session
    ├── 提取信号 ✅
    ├── 选择匹配基因 ✅ NEW
    ├── 创建 mutation ✅ NEW
    ├── 创建 personality_state ✅ NEW
    ├── 写入 last_run 状态 ✅ NEW
    └── 返回分析结果 ✅

evolve_capability
    ├── 创建 EvolutionEvent ✅ NEW
    ├── 创建 Capsule ✅ NEW
    ├── 应用表观遗传标记 ✅ NEW
    └── 返回进化结果 ✅
```

---

## 部署流程

### 1. 安装依赖
```bash
cd evolver/
npm install @modelcontextprotocol/sdk
```

### 2. 创建 MCP Server

四个核心工具：

| 工具 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `analyze_session` | 分析会话，提取信号 | sessionId, messages, codeChanges, errors | signals, selectedGene, shouldEvolve |
| `suggest_improvement` | 提供改进建议 | context, issue, signals | recommendations |
| `get_best_practice` | 获取最佳实践 | problem, language, framework | solutions |
| `evolve_capability` | 执行进化循环 | signals, mode, summary | eventId, capsuleId, epigeneticApplied |

### 3. Trae 配置 MCP

```json
{
  "mcpServers": {
    "evolver": {
      "command": "node",
      "args": ["path/to/mcp-server.js"],
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

### 4. 配置项目规则

在 `.trae/rules/` 中定义 Agent 行为：

```markdown
# Evolver 自我进化规则

每次完成任务后，必须自动调用 `evolver.analyze_session` 分析会话。

触发条件：
- 代码执行出错
- 用户要求优化/重构
- 大规模代码变更
- 完成重要功能
```

---

## 类比理解

### 餐厅服务类比

| 组件 | 类比 | 作用 |
|------|------|------|
| **Trae IDE** | 餐厅前台 | 接收客户需求 |
| **MCP Protocol** | 点餐系统 | 标准化通信 |
| **MCP Server** | 后厨 | 实际执行服务 |
| **Evolver 工具** | 厨师技能 | 分析、建议、进化 |
| **项目规则** | 服务标准 | 规定何时提供服务 |
| **Genes** | 菜谱 | 标准化解决方案 |
| **Capsules** | 成品菜 | 成功案例固化 |

### 流程
```
顾客(用户) → 前台(Trae) → 点餐系统(MCP) → 后厨(Evolver)
                ↓
         自动询问是否满意（analyze_session）
                ↓
         根据反馈改进菜品（evolve_capability）
                ↓
         记录成功经验（Capsule）
                ↓
         下次更快响应（表观遗传）
```

---

## 实际示例

### 示例 1: 完整的进化流程

```javascript
// 1. 分析会话
await evolver.analyze_session({
  sessionId: 'session-001',
  messages: [
    { role: 'user', content: '创建一个新基因' },
    { role: 'assistant', content: '已创建 gene_xxx' }
  ],
  codeChanges: ['genes/gene_xxx.json'],
  errors: []
});

// 返回
{
  "signals": ["gene_related", "config_change"],
  "selectedGene": { "id": "gene_gene_creation_protocol", "category": "optimize" },
  "shouldEvolve": true
}

// 2. 执行进化
await evolver.evolve_capability({
  signals: ['create_new_gene', 'optimization_pattern'],
  mode: 'optimize',
  summary: '创建新基因并记录知识',
  review: false
});

// 返回
{
  "status": "evolved",
  "gene": "gene_gene_creation_protocol",
  "eventId": "evt_1234567890",
  "capsuleId": "capsule_1234567890",
  "epigeneticApplied": true,
  "message": "进化完成：已创建事件、胶囊，并应用表观遗传标记"
}
```

### 示例 2: 验证进化结果

```javascript
// 查看胶囊
// capsules.json 中新增：
{
  "type": "Capsule",
  "id": "capsule_1234567890",
  "gene": "gene_gene_creation_protocol",
  "trigger": ["create_new_gene", "optimization_pattern"],
  "success_streak": 1
}

// 查看表观遗传标记
// genes.json 中基因新增：
{
  "epigenetic_marks": [
    {
      "context": "win32/x64/v20.11.1",
      "boost": 0.05,
      "reason": "reinforced_by_success"
    }
  ]
}
```

---

## 最佳实践

### 1. 信号设计
- **具体化**: 使用技术栈+错误类型，如 `["python", "import_error"]`
- **层次化**: 从通用到具体 `["error", "syntax_error", "indentation_error"]`
- **可扩展**: 预留新信号类型

### 2. 项目规则编写
- **明确触发条件** - 什么情况下必须调用
- **强制自动执行** - 不需要用户要求
- **透明反馈** - 告知用户正在分析

### 3. 文件组织
```
evolver/
├── mcp-server.js           # MCP Server 入口
├── memory/                 # 会话记录
│   └── trae-bridge/
│       ├── session_xxx.json
│       └── last_run.json
├── assets/gep/
│   ├── genes/              # 基因定义
│   ├── genes.json          # 主索引
│   ├── capsules.json       # 胶囊库
│   └── events.jsonl        # 进化事件
└── learning-manual/        # 知识积累
```

### 4. 故障排除

| 问题 | 原因 | 解决 |
|------|------|------|
| MCP 无法启动 | 依赖未安装 | `npm install` |
| Trae 无法连接 | 路径错误 | 检查绝对路径 |
| 工具无响应 | Server 未运行 | 确认 node 进程 |
| 进化未生效 | 版本过旧 | 升级到 v2.0.0 |

---

## 后续改进

1. **集成真实 solidify.js** - 当前是简化实现，应调用完整的 solidify 流程
2. **添加验证步骤** - 执行基因定义的验证命令
3. **支持回滚** - 进化失败时自动回滚
4. **A2A 广播** - 优质胶囊自动发布到 Hub

---

## 相关话题

- [Gene 与 Capsule](./gene-and-capsule.md) - 核心概念
- [匹配机制](./matching-mechanism.md) - 如何选择基因和胶囊
- [基因优胜劣汰机制](./gene-selection-and-elimination.md) - 表观遗传与封禁
- [规则遵循机制](./rule-compliance.md) - 确保规则自动执行

---

## 参考链接

- [MCP 官方文档](https://modelcontextprotocol.io)
- [Evolver GitHub](https://github.com/autogolve/evolver)
- [Trae 官方文档](https://trae.ai)

---

*话题创建时间: 2026-02-24*
*最后更新: 2026-02-25*
*基因驱动: gene_knowledge_accumulation*
