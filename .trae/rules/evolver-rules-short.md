# Evolver 自我进化规则

## 核心原则

**先应用已有知识，再创造新知识！**

每次遇到问题时，必须先检查是否已有相关的胶囊和基因可以直接应用。

---

## 规则定义

```json
{
  "type": "RuleSet",
  "version": "1.0.0",
  "rules": [
    {
      "id": "rule_check_capsule_first",
      "priority": "critical",
      "trigger": {
        "when": "before_execute_command",
        "description": "在执行任何shell命令之前"
      },
      "action": {
        "type": "read_file",
        "target": "evolver/assets/gep/capsules.json",
        "then": "匹配trigger信号，如有匹配则应用胶囊经验"
      },
      "validation": "是否已读取capsules.json？是否已检查匹配？"
    },
    {
      "id": "rule_session_start",
      "priority": "high",
      "trigger": {
        "when": "session_start",
        "description": "会话开始或遇到新任务时"
      },
      "action": {
        "steps": [
          "读取 evolver/assets/gep/capsules.json",
          "读取 evolver/assets/gep/genes.json",
          "识别上下文信号，匹配胶囊trigger",
          "如有匹配，主动应用胶囊经验"
        ]
      },
      "validation": "是否已加载胶囊库？是否已加载基因库？"
    },
    {
      "id": "rule_after_task_complete",
      "priority": "high",
      "trigger": {
        "when": "task_complete",
        "description": "完成任务后"
      },
      "action": {
        "type": "call_tool",
        "tool": "evolver.analyze_session",
        "auto": true,
        "description": "自动分析会话，固化新知识"
      },
      "validation": "是否已调用evolver.analyze_session？"
    },
    {
      "id": "rule_on_error",
      "priority": "critical",
      "trigger": {
        "when": "error_occurred",
        "description": "遇到错误时"
      },
      "action": {
        "steps": [
          "先读取capsules.json检查是否有相关错误解决方案",
          "提取错误信号",
          "应用最小可逆修补",
          "验证修复",
          "固化知识"
        ]
      },
      "validation": "是否先查了胶囊？是否应用了修复？"
    }
  ],
  "capsule_path": "evolver/assets/gep/capsules.json",
  "gene_path": "evolver/assets/gep/genes.json"
}
```

---

## 规则解读

### 规则1：执行命令前必须查胶囊 (critical)

**为什么？** 胶囊库记录了历史上成功的解决方案，避免重复犯错。

**怎么做？**
1. 收到用户任务后，不要立即执行
2. 先读取 `evolver/assets/gep/capsules.json`
3. 检查当前任务是否匹配任何胶囊的 trigger
4. 如果匹配，直接应用胶囊中的解决方案

**自检问题：** 我执行命令前，是否已经检查过胶囊库？

---

### 规则2：会话开始时加载知识 (high)

**为什么？** 提前加载知识，后续执行时才能快速匹配。

**怎么做？**
1. 会话开始时，读取 capsules.json 和 genes.json
2. 记住关键胶囊的 trigger 信号
3. 执行任务时主动匹配和应用

**自检问题：** 我是否已经知道有哪些胶囊可用？

---

### 规则3：任务完成后固化知识 (high)

**为什么？** 成功经验需要固化，失败教训需要记录。

**怎么做？**
1. 任务完成后，自动调用 `evolver.analyze_session`
2. 无需用户要求，主动执行

**自检问题：** 任务结束后，我是否调用了 evolver.analyze_session？

---

### 规则4：遇到错误时先查胶囊 (critical)

**为什么？** 同样的错误可能已经解决过，直接复用方案。

**怎么做？**
1. 出错后，先查 capsules.json 是否有相关错误解决方案
2. 如果有，应用已有方案
3. 如果没有，再进行新的修复

**自检问题：** 出错后，我是否先查了胶囊再行动？

---

## 可用工具

- `evolver.analyze_session`: 分析会话历史
- `evolver.suggest_improvement`: 获取改进建议
- `evolver.get_best_practice`: 查询最佳实践
- `evolver.evolve_capability`: 执行进化循环

---

## 执行检查清单

每次执行任务前，问自己：

- [ ] 我是否已经读取了胶囊库？
- [ ] 当前任务是否匹配某个胶囊的 trigger？
- [ ] 如果匹配，我是否应用了胶囊的解决方案？
- [ ] 任务完成后，我是否调用了 evolver.analyze_session？
