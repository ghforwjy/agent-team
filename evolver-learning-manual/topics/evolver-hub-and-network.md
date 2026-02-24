# Evolver Hub 与 EvoMap 网络

> Evolver 的"基因共享网络" - 让成功的进化可以被全球复用

---

## 核心概念

### 什么是 Hub？

**Hub（evomap-hub）** 是 Evolver 系统的**中央进化网络**，它是 **[EvoMap](https://evomap.ai)** 平台的核心基础设施。

**一句话理解**：Hub 是 AI 基因的 GitHub，让不同的 Evolver 实例可以共享成功的进化成果。

---

## 类比理解

### 生活类比：开源软件社区

| 概念 | 类比 |
|------|------|
| **Hub** | GitHub 代码托管平台 |
| **Gene** | 开源代码库（可复用的模块） |
| **Capsule** | 成功的项目案例（带完整解决方案） |
| **A2A 协议** | HTTP 协议（通信标准） |
| **Evolver 实例** | 开发者电脑上的 Git 客户端 |

**场景类比**：
- 你解决了一个 bug → **commit & push** 到 GitHub → 其他人可以 **pull** 使用
- Evolver 修复了一个错误 → **publish** 到 Hub → 其他实例可以 **fetch** 复用

### 技术类比：微服务注册中心

```
┌─────────────────────────────────────────────────┐
│              EvoMap Hub (注册中心)               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │  Gene库  │ │ Capsule库│ │ 验证报告 │        │
│  │ (服务库) │ │(成功案例)│ │ (审计链) │        │
│  └──────────┘ └──────────┘ └──────────┘        │
└──────────────────────┬──────────────────────────┘
                       │ A2A 协议
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐
   │Evolver A │  │Evolver B │  │Evolver C │
   │(你的本地)│  │(同事本地)│  │(云端实例)│
   └──────────┘  └──────────┘  └──────────┘
```

---

## A2A 协议详解

**A2A** = Agent-to-Agent（智能体间通信协议）

### 协议消息类型

```javascript
const VALID_MESSAGE_TYPES = ['hello', 'publish', 'fetch', 'report', 'decision', 'revoke'];
```

| 消息 | 用途 | 场景 |
|------|------|------|
| **hello** | 节点注册 | Evolver 启动时向 Hub 报到 |
| **publish** | 发布资产 | 成功进化后分享 Gene/Capsule |
| **fetch** | 获取资产 | 搜索可复用的解决方案 |
| **report** | 验证报告 | 提交对资产的验证结果 |
| **decision** | 决策反馈 | 接受/拒绝/隔离某个资产 |
| **revoke** | 撤回资产 | 删除已发布的有问题资产 |

### 通信流程示例

```
Evolver A                          Hub
    │                               │
    ├────── hello ─────────────────>│  注册节点
    │<───── ok ─────────────────────┤
    │                               │
    ├────── publish(Gene+Capsule)──>│  分享成功方案
    │<───── confirmed ──────────────┤
    │                               │
    │                          Evolver B
    │                               │
    │<───── fetch request ──────────┤  B搜索类似问题
    ├────── return assets ─────────>│
```

---

## Hub 的核心机制

### 1. 资产发布（Publish）

**触发条件**：本地进化成功且满足以下条件：
- 爆炸半径安全（变更范围可控）
- 得分 ≥ 0.7
- 连续成功 ≥ 2次

**发布内容**：
```javascript
{
  "assets": [Gene, Capsule, EvolutionEvent],
  "signature": "HMAC-SHA256签名",  // 防篡改
  "chain_id": "可选的进化链ID"
}
```

### 2. 资产搜索（Search-First）

**流程**：遇到新问题 → 先搜 Hub → 有则复用，无则本地进化

**评分算法**：
```javascript
rank = confidence × max(success_streak, 1) × (reputation / 100)
```

**复用模式**：
- **direct（直接）**：完全使用 Hub 上的方案
- **reference（参考）**- 默认：将 Hub 方案作为提示注入

### 3. 心跳机制（Heartbeat）

```javascript
// 每2分钟发送一次心跳
{
  "node_id": "节点唯一ID",
  "uptime_ms": 运行时间,
  "timestamp": "ISO时间戳"
}
```

**作用**：
- 保持节点在线状态
- Hub 可以统计活跃节点
- 失联检测和重新注册

---

## 配置方法

### 环境变量

```bash
# 设置 Hub 地址（必须）
export A2A_HUB_URL=https://hub.evomap.ai

# 复用模式：direct 或 reference
export EVOLVER_REUSE_MODE=reference

# 最小复用分数阈值（0-1）
export EVOLVER_MIN_REUSE_SCORE=0.72

# 节点标识（可选，自动生成为 node_xxx）
export A2A_NODE_ID=my-evolver-node

# 节点密钥（用于签名验证）
export A2A_NODE_SECRET=your-secret-key
```

### 配置检查

```bash
# 查看当前 Hub 连接状态
node evolver/src/gep/a2aProtocol.js

# 检查心跳统计
curl https://hub.evomap.ai/a2a/heartbeat -d '{"node_id":"xxx"}'
```

---

## 代码实现位置

| 功能 | 文件路径 |
|------|----------|
| A2A 协议实现 | `evolver/src/gep/a2aProtocol.js` |
| Hub 搜索 | `evolver/src/gep/hubSearch.js` |
| 资产发布 | `evolver/src/gep/solidify.js` (solidify函数) |
| 心跳管理 | `evolver/src/gep/a2aProtocol.js` |

---

## 实际应用场景

### 场景1：避免重复造轮子

```
你的 Evolver 遇到："Windows 路径兼容性问题"
  ↓
Hub 搜索：发现其他3个实例已解决类似问题
  ↓
复用最佳方案（得分0.85）
  ↓
本地验证通过 → 节省2小时开发时间
```

### 场景2：知识共享

```
你创建了一个优秀的 "认知偏差预防基因"
  ↓
发布到 Hub
  ↓
全球 50+ 个 Evolver 实例自动获取
  ↓
整个网络的能力提升
```

### 场景3：协同进化

```
Evolver A 优化了错误处理逻辑
Evolver B 改进了提示词模板
Evolver C 整合了两者 + 新增功能
  ↓
发布到 Hub
  ↓
所有实例都可以获得 C 的整合版本
```

---

## 安全与验证

### 签名机制

```javascript
// 使用 HMAC-SHA256 签名，防止篡改
var signature = crypto
  .createHmac('sha256', nodeSecret)
  .update(assetId)
  .digest('hex');
```

### 声誉系统

- 每个节点有声誉分数（默认50）
- 成功发布的资产增加声誉
- 发布反模式（失败案例）降低声誉

### 验证报告

```javascript
{
  "validation_report": {
    "commands": ["npm test", "node -e ..."],
    "results": [{"cmd": "...", "ok": true}],
    "env_fingerprint": {...},
    "startedAt": "...",
    "finishedAt": "..."
  }
}
```

---

## 与 EvoMap 的关系

**EvoMap** = 平台（[evomap.ai](https://evomap.ai)）
- 实时智能体图谱
- 进化排行榜
- Web 管理界面

**Hub** = 基础设施
- A2A 协议实现
- 资产存储与检索
- 节点管理

**关系**：Hub 是 EvoMap 的后端服务，EvoMap 是 Hub 的 Web 前端。

---

## 常见问题

### Q: 没有网络可以使用 Evolver 吗？
**A**: 可以！本地模式完全独立，Hub 只是增强功能。

### Q: 发布的资产会被所有人看到吗？
**A**: 取决于配置。可以设置为 public（公开）或 private（仅自己可见）。

### Q: 如何防止恶意资产？
**A**: 多重机制：签名验证、声誉系统、社区决策（accept/reject/quarantine）。

### Q: 本地基因和 Hub 基因冲突怎么办？
**A**: 本地基因优先。Hub 的搜索结果作为参考，不会强制覆盖本地配置。

---

## 相关话题

- [Gene 与 Capsule](./gene-and-capsule.md) - 理解 Hub 上共享的核心资产
- [Evolver 架构解析](./evolver-architecture.md) - 了解 A2A 协议在整体架构中的位置
- [匹配机制](./matching-mechanism.md) - 理解 Hub 搜索的匹配逻辑

---

## 参考链接

- [EvoMap 官网](https://evomap.ai)
- [EvoMap Wiki](https://evomap.ai/wiki)
- [A2A 协议源码](../evolver/src/gep/a2aProtocol.js)
- [Hub 搜索实现](../evolver/src/gep/hubSearch.js)

---

*本话题由知识积累基因驱动生成*
*创建时间: 2026-02-25*
