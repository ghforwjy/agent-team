# 阶段二：LLM 精细分析实现方案（修正版）

## 一、重新理解需求

### 1.1 阶段一（向量筛选）已完成的工作

**向量模型已经做了：**
1. ✅ 判断审计程序是否包含制度要求（通过相似度阈值）
2. ✅ 建议制度类型（建立制度/定期执行/人员配备/岗位分离/文件保存/建立组织）
3. ✅ 计算相似度分数

**置信度分级：**
- **高置信度（>0.70）**：向量模型非常确定 → **直接确认，无需 LLM**
- **中置信度（0.45-0.70）**：向量模型不太确定 → **需要 LLM 校验**
- **低置信度（<0.45）**：不包含制度要求 → **跳过**

### 1.2 阶段二（LLM）应该做什么

**LLM 只需要做一件事：校验向量模型的分类是否正确**

**输入**：
- 审计项基本信息（编码、标题、程序文本）
- 向量模型的建议类型
- 向量相似度

**输出**：
- ✅ 向量模型判断正确（confirmed）
- ❌ 向量模型判断错误，建议修正类型（adjusted）

---

## 二、简化的 LLM 提示词设计

### 2.1 系统角色

```python
SYSTEM_PROMPT = """你是一个 IT 审计专家，负责校验向量模型对审计项的分类是否正确。"""
```

### 2.2 单条校验 Prompt（极简版）

```python
VERIFICATION_PROMPT = """请校验向量模型对以下审计项的分类是否正确。

## 审计项信息
- 编码：{item_code}
- 标题：{item_title}
- 维度：{dimension}
- 审计程序：{procedure_text}

## 向量模型建议
- 建议类型：{vector_suggestion}
- 相似度：{similarity}

## 校验任务

判断向量模型的分类是否正确：
- 如果正确：回答"正确"
- 如果错误：回答"错误"，并给出正确的类型

## 制度类型定义

1. **建立制度**：要求制定、建立、编制制度/规定/办法/规程
2. **定期执行**：要求定期（每年/每季度）开展检查/评估/演练/审计
3. **人员配备**：要求配备人员、设置岗位、指定专人负责
4. **岗位分离**：要求职责分离、不相容岗位分离
5. **文件保存**：要求保存文档、留存记录、归档
6. **建立组织**：要求成立委员会、领导小组、工作机构

## 输出格式

请严格按照以下 JSON 格式输出：

{{
  "vector_suggestion_correct": true/false,
  "corrected_type": null 或 "正确的类型",
  "reasoning": "判断理由（30 字内）"
}}

## 示例

**输入：**
- 审计程序："检查是否建立信息安全管理制度"
- 向量模型建议："建立制度"，相似度 0.65

**输出：**
{{
  "vector_suggestion_correct": true,
  "corrected_type": null,
  "reasoning": "向量模型判断正确，确实要求建立制度"
}}

**输入：**
- 审计程序："检查是否每年开展安全检查"
- 向量模型建议："建立制度"，相似度 0.55

**输出：**
{{
  "vector_suggestion_correct": false,
  "corrected_type": "定期执行",
  "reasoning": "应为定期执行，不是建立制度"
}}
"""
```

### 2.3 批量校验 Prompt（生产用）

```python
BATCH_VERIFICATION_PROMPT = """请批量校验向量模型对以下审计项的分类是否正确。

## 待校验的审计项（共{count}条）

{items_json}

## 制度类型定义

1. **建立制度**：要求制定、建立、编制制度/规定/办法/规程
2. **定期执行**：要求定期（每年/每季度）开展检查/评估/演练/审计
3. **人员配备**：要求配备人员、设置岗位、指定专人负责
4. **岗位分离**：要求职责分离、不相容岗位分离
5. **文件保存**：要求保存文档、留存记录、归档
6. **建立组织**：要求成立委员会、领导小组、工作机构

## 输出格式

请严格按照以下 JSON 格式输出：

{{
  "verification_results": [
    {{
      "item_id": 123,
      "item_code": "NEW-xxx",
      "vector_suggestion_correct": true/false,
      "corrected_type": null 或 "正确的类型",
      "reasoning": "判断理由（30 字内）"
    }}
  ]
}}
"""
```

---

## 三、简化的代码实现

### 3.1 LLMVerifier 类（复用已有代码）

**直接复用模块 1 的 `LLMVerifier` 类**，只需要添加一个新的校验方法：

```python
# -*- coding: utf-8 -*-
"""
LLM 校验器 - 对向量模型的分类结果进行校验
"""
import os
import json
import re
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class VerificationResult:
    """校验结果"""
    item_id: int
    item_code: str
    vector_suggestion_correct: bool
    corrected_type: str | None
    reasoning: str


class PolicyLLMVerifier:
    """制度分类 LLM 校验器"""
    
    REQUIREMENT_TYPES = [
        '建立制度', '定期执行', '人员配备',
        '岗位分离', '文件保存', '建立组织'
    ]
    
    def __init__(self, api_base: str = None, api_key: str = None, model: str = None):
        # 复用 LLMVerifier 的配置
        self.api_base = api_base or os.environ.get('ARK_BASE_URL') or os.environ.get('LLM_API_BASE', '')
        self.api_key = api_key or os.environ.get('ARK_API_KEY') or os.environ.get('LLM_API_KEY', '')
        self.model = model or os.environ.get('ARK_CHAT_MODEL') or os.environ.get('LLM_MODEL', 'gpt-3.5-turbo')
    
    def verify_classification(self, items: List[Dict]) -> List[VerificationResult]:
        """
        批量校验向量模型的分类结果
        
        Args:
            items: 中置信度审计项列表（来自向量筛选）
                   每项包含：item_id, item_code, item_title, dimension_name, 
                           procedure_text, suggested_type, similarity
        
        Returns:
            校验结果列表
        """
        # 构建 Prompt
        prompt = self._build_verification_prompt(items)
        
        # 调用 LLM
        response = self._call_llm(prompt)
        
        # 解析响应
        results = self._parse_response(response, items)
        
        return results
    
    def _build_verification_prompt(self, items: List[Dict]) -> str:
        """构建批量校验 Prompt"""
        items_json = json.dumps([
            {
                'item_id': item['item_id'],
                'item_code': item['item_code'],
                'item_title': item['item_title'],
                'dimension': item['dimension_name'],
                'procedure_text': item['procedure_text'][:200],  # 限制长度
                'vector_suggestion': item.get('suggested_type'),
                'similarity': item.get('similarity')
            }
            for item in items
        ], ensure_ascii=False, indent=2)
        
        return BATCH_VERIFICATION_PROMPT.format(
            count=len(items),
            items_json=items_json
        )
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM API（复用 LLMVerifier 的实现）"""
        try:
            import openai
            
            client = openai.OpenAI(
                base_url=self.api_base,
                api_key=self.api_key
            )
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个 IT 审计专家，负责校验向量模型对审计项的分类是否正确。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=3000
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"LLM 调用失败：{e}")
            raise
    
    def _parse_response(self, response: str, items: List[Dict]) -> List[VerificationResult]:
        """解析 LLM 响应"""
        # 提取 JSON
        json_match = re.search(r'\{[\s\S]*\}', response)
        if not json_match:
            raise ValueError("LLM 响应中未找到 JSON")
        
        data = json.loads(json_match.group())
        
        results = []
        for item_data in data.get('verification_results', []):
            result = VerificationResult(
                item_id=item_data['item_id'],
                item_code=item_data['item_code'],
                vector_suggestion_correct=item_data['vector_suggestion_correct'],
                corrected_type=item_data.get('corrected_type'),
                reasoning=item_data.get('reasoning', '')
            )
            results.append(result)
        
        return results
```

### 3.2 集成到 PolicyRequirementExtractor

```python
# 修改 policy_extractor.py
class PolicyRequirementExtractor:
    """制度要求提取器 - 向量+LLM 两阶段"""
    
    def __init__(self, db_path: str, force_full: bool = False, output_dir: str = None):
        self.db_path = db_path
        self.force_full = force_full
        self.db = PolicyDatabaseManager(db_path)
        self.screener = PolicyVectorScreener()
        self.verifier = PolicyLLMVerifier()  # 新增：LLM 校验器
        self.output_dir = output_dir or ...
    
    def extract(self) -> Dict:
        """执行提取流程（完整两阶段）"""
        batch_id = self._generate_batch_id()
        
        # 加载未筛选的审计项
        items = self._load_unscreened_items()
        if not items:
            return {'status': 'no_items', 'batch_id': batch_id}
        
        self.db.init_policy_tables()
        
        # === 阶段 1：向量语义筛选 ===
        high_confidence, medium_confidence, skipped = self.screener.screen(items)
        
        # 保存高置信度结果（直接确认）
        if high_confidence:
            records = self._convert_to_records(high_confidence, 'confirmed')
            self.db.batch_save_screening_results(records, batch_id)
        
        # === 阶段 2：LLM 校验 ===
        if medium_confidence:
            print("\n=== 阶段 2：LLM 校验向量模型分类 ===")
            
            # LLM 校验
            verification_results = self.verifier.verify_classification(medium_confidence)
            
            # 根据 LLM 结果更新状态
            confirmed_count = 0
            adjusted_count = 0
            
            for ver_result in verification_results:
                # 找到对应的向量筛选结果
                vector_result = next(
                    r for r in medium_confidence 
                    if r.item_id == ver_result.item_id
                )
                
                if ver_result.vector_suggestion_correct:
                    # 向量模型正确，确认
                    record = self._convert_to_record(vector_result, 'confirmed')
                    record.llm_verified = True
                    self.db.save_screening_result(record)
                    confirmed_count += 1
                else:
                    # 向量模型错误，修正类型
                    vector_result.suggested_type = ver_result.corrected_type
                    record = self._convert_to_record(vector_result, 'confirmed')
                    record.llm_verified = True
                    self.db.save_screening_result(record)
                    adjusted_count += 1
            
            print(f"LLM 校验完成：确认 {confirmed_count} 条，修正 {adjusted_count} 条")
        
        # 生成统计
        result = {
            'status': 'success',
            'batch_id': batch_id,
            'total_items': len(items),
            'high_confidence': len(high_confidence),
            'medium_confidence': len(medium_confidence),
            'llm_verified': len(medium_confidence),
            'llm_adjusted': adjusted_count
        }
        
        return result
```

---

## 四、为什么不需要 keywords？

### 4.1 keywords 的作用

**keywords 是给向量模型用的**，不是给 LLM 用的：

```python
# 在 vector_screener.py 中
VECTOR_TEMPLATES = {
    '建立制度': [
        '制定制度', '建立制度', '编制制度',  # ← 这些是关键词组合
        ...
    ],
    ...
}
```

向量模型用这些关键词生成模板向量，用于计算相似度。

### 4.2 LLM 不需要 keywords

**LLM 做的是逻辑判断**，它理解自然语言，不需要关键词提示：

```python
# LLM 只需要知道类型定义
1. **建立制度**：要求制定、建立、编制制度/规定/办法/规程
2. **定期执行**：要求定期（每年/每季度）开展检查/评估/演练/审计
...
```

---

## 五、为什么只需要一种提示词？

### 5.1 单条 vs 批量

**不需要区分单条和批量**，因为：
- 批量处理效率更高（一次 API 调用处理多条）
- LLM 能很好地理解批量任务
- 减少 API 调用次数，节省成本

### 5.2 只需要一个 Prompt

```python
BATCH_VERIFICATION_PROMPT = """请批量校验向量模型对以下审计项的分类是否正确。

## 待校验的审计项（共{count}条）
{items_json}

## 制度类型定义
1. **建立制度**：要求制定、建立、编制制度/规定/办法/规程
2. **定期执行**：要求定期（每年/每季度）开展检查/评估/演练/审计
3. **人员配备**：要求配备人员、设置岗位、指定专人负责
4. **岗位分离**：要求职责分离、不相容岗位分离
5. **文件保存**：要求保存文档、留存记录、归档
6. **建立组织**：要求成立委员会、领导小组、工作机构

## 输出格式
{{
  "verification_results": [
    {{
      "item_id": 123,
      "vector_suggestion_correct": true/false,
      "corrected_type": null 或 "正确的类型",
      "reasoning": "判断理由（30 字内）"
    }}
  ]
}}
"""
```

---

## 六、实施步骤（简化版）

### Step 1: 创建 LLM 校验器
- 文件：`llm_verifier.py`（新增）
- 类名：`PolicyLLMVerifier`
- 功能：批量校验向量模型分类
- 代码量：~150 行
- 时间：1 小时

### Step 2: 集成到提取器
- 修改：`policy_extractor.py`
- 添加 LLM 校验调用
- 更新数据库记录
- 时间：1 小时

### Step 3: 测试
- 使用测试数据库
- 验证 LLM 校验效果
- 调整 Prompt
- 时间：1 小时

**总预计时间：3 小时**

---

## 七、总结

### 核心理念

**LLM 只做一件事：校验向量模型的分类结果**

- ✅ 正确 → confirmed
- ❌ 错误 → adjusted（给出正确类型）

### 简化后的架构

```
阶段 1（向量筛选）：
  - 输入：审计项列表
  - 处理：计算与模板的相似度
  - 输出：
    - 高置信度（>0.70）→ 直接确认
    - 中置信度（0.45-0.70）→ 待 LLM 校验
    - 低置信度（<0.45）→ 跳过

阶段 2（LLM 校验）：
  - 输入：中置信度项 + 向量建议类型
  - 处理：逻辑判断分类是否正确
  - 输出：
    - 正确 → confirmed
    - 错误 → adjusted（修正类型）
```

### 优势

1. **职责清晰**：向量做语义匹配，LLM 做逻辑校验
2. **代码简洁**：只需一个校验器类，一个 Prompt
3. **效率高**：批量处理，减少 API 调用
4. **成本低**：LLM 只处理中置信度项（约 20-30%）
