# 阶段二：LLM 精细分析实现方案

## 一、需求分析

### 1.1 设计文档要求（来自 module2-checker.md v3.0）

#### 核心流程
```
制度要求提取流程（向量+LLM 两阶段）

1. 加载审计项
   - 检查已筛选记录（增量模式）
   - 只加载未筛选的审计项

2. 阶段 1：向量语义筛选（秒级）
   - 计算审计项与模板向量的相似度
   - 根据相似度分级处理
     - > 0.70：高置信度 → 直接确定分类，无需 LLM
     - 0.45-0.70：中置信度 → 需要 LLM 确认
     - < 0.45：低置信度 → 不包含制度要求，跳过

3. 阶段 2：LLM 确认与分类
   - 只处理中置信度的项
   - LLM 确认分类是否正确
   - 更新状态：confirmed/rejected

4. 输出结果
   - 生成 JSON/HTML 报告
```

#### 置信度分级标准
| 相似度范围 | 置信度 | 处理方式 | 说明 |
|-----------|--------|---------|------|
| > 0.70 | 高 | 直接确定分类 | 向量匹配结果可靠，无需 LLM |
| 0.45-0.70 | 中 | LLM 确认 | 需要 LLM 确认分类 |
| < 0.45 | 低 | 跳过 | 不包含制度要求 |

### 1.2 当前状态

**已完成（阶段一）：**
- ✅ 向量筛选器 `PolicyVectorScreener`
- ✅ 数据库管理器 `PolicyDatabaseManager`
- ✅ 报告生成器 `ScreeningResultReporter`
- ✅ 数据入库（136 条测试数据）
- ✅ HTML 报告生成（带自动换行、表头拖动）

**待实现（阶段二）：**
- ❌ LLM 分析器
- ❌ 中置信度项筛选
- ❌ LLM 确认提示词设计
- ❌ 批量处理逻辑
- ❌ 结果更新机制

---

## 二、LLM 提示词设计

### 2.1 系统角色定义

```python
SYSTEM_PROMPT = """你是一个 IT 审计专家，专门负责识别审计程序中包含的制度建设要求。

你的任务是：
1. 判断审计程序是否包含对制度建设的要求
2. 识别制度要求的具体类型
3. 提取制度要求的详细内容
"""
```

### 2.2 制度要求类型定义

```python
REQUIREMENT_TYPES = {
    '建立制度': {
        'description': '要求制定、建立、编制某种制度、规定、办法、规程',
        'keywords': ['制定', '建立', '编制', '制度', '规定', '办法', '规程'],
        'examples': [
            '制定信息安全管理制度',
            '建立变更管理规定',
            '编制操作规程'
        ]
    },
    '定期执行': {
        'description': '要求定期（每年/每季度/每月）开展某项检查、评估、演练、审计',
        'keywords': ['每年', '每季度', '定期', '开展', '进行', '检查', '评估', '演练', '审计'],
        'examples': [
            '每年开展安全检查',
            '定期进行风险评估',
            '每季度开展应急演练'
        ]
    },
    '人员配备': {
        'description': '要求配备人员、设置岗位、指定专人负责',
        'keywords': ['配备', '设置', '指定', '人员', '岗位', '专人', '责任'],
        'examples': [
            '配备专职安全人员',
            '设置安全管理岗位',
            '指定专人负责'
        ]
    },
    '岗位分离': {
        'description': '要求职责分离、不相容岗位分离、岗位制衡',
        'keywords': ['分离', '不相容', '职责', '分工', '制衡', '监督'],
        'examples': [
            '职责分离',
            '不相容岗位分离',
            '岗位相互制约'
        ]
    },
    '文件保存': {
        'description': '要求保存文档、留存记录、归档文件',
        'keywords': ['保存', '留存', '归档', '文档', '记录', '档案', '日志'],
        'examples': [
            '保存检查记录',
            '留存审计文档',
            '归档配置文件'
        ]
    },
    '建立组织': {
        'description': '要求成立委员会、领导小组、工作机构',
        'keywords': ['成立', '建立', '设立', '委员会', '小组', '机构', '部门'],
        'examples': [
            '成立信息安全委员会',
            '建立领导小组',
            '设立工作机构'
        ]
    }
}
```

### 2.3 单条审计项分析 Prompt

```python
SINGLE_ITEM_PROMPT = """请分析以下审计程序是否包含制度建设要求。

## 审计项信息
- 编码：{item_code}
- 标题：{item_title}
- 维度：{dimension}
- 审计程序：{procedure_text}

## 分析任务

1. **判断是否包含制度要求**
   - 如果有明确要求建立制度、定期执行、人员配备等，回答"是"
   - 如果只是检查某项工作是否已开展，回答"否"

2. **如果包含制度要求，请识别类型**（从以下 6 类中选择）：
   - 建立制度：要求制定、建立、编制制度/规定/办法/规程
   - 定期执行：要求定期（每年/每季度）开展检查/评估/演练/审计
   - 人员配备：要求配备人员、设置岗位、指定专人负责
   - 岗位分离：要求职责分离、不相容岗位分离
   - 文件保存：要求保存文档、留存记录、归档
   - 建立组织：要求成立委员会、领导小组、工作机构

3. **提取制度要求详情**：
   - what：要建立/执行的制度/工作是什么
   - scope：适用范围（如"全公司"、"信息系统"等）
   - frequency：执行频率（如"每年"、"每季度"等，如适用）
   - content：制度要求的具体内容描述

## 输出格式

请严格按照以下 JSON 格式输出：

{{
  "has_requirement": true/false,
  "requirement_type": "建立制度/定期执行/人员配备/岗位分离/文件保存/建立组织/null",
  "confidence": "high/medium/low",
  "requirement_detail": {{
    "what": "制度/工作名称",
    "scope": "适用范围",
    "frequency": "执行频率（如不适用填 null）",
    "content": "具体内容描述"
  }},
  "reasoning": "判断理由（50 字内）"
}}

## 示例

**输入：**
- 审计程序："检查是否建立信息安全管理制度"

**输出：**
{{
  "has_requirement": true,
  "requirement_type": "建立制度",
  "confidence": "high",
  "requirement_detail": {{
    "what": "信息安全管理制度",
    "scope": "全公司",
    "frequency": null,
    "content": "建立信息安全管理制度，明确信息安全责任"
  }},
  "reasoning": "明确要求建立制度，属于制度建设要求"
}}

**输入：**
- 审计程序："检查防火墙配置是否正确"

**输出：**
{{
  "has_requirement": false,
  "requirement_type": null,
  "confidence": "high",
  "requirement_detail": null,
  "reasoning": "仅检查技术配置，不涉及制度建设要求"
}}
"""
```

### 2.4 批量分析 Prompt（优化版）

```python
BATCH_ANALYSIS_PROMPT = """你是一个 IT 审计专家，负责批量识别审计程序中的制度建设要求。

## 任务说明

我将提供一批审计项（共{count}条），每条包含：
- 编码、标题、维度、审计程序文本
- 向量模型建议的类型和相似度

请你逐条分析：
1. 是否包含制度建设要求
2. 如果包含，属于哪种类型（6 类之一）
3. 提取制度要求的详细内容

## 审计项列表

{items_json}

## 输出格式

请严格按照以下 JSON 格式输出：

{{
  "analysis_results": [
    {{
      "item_id": 123,
      "item_code": "NEW-xxx",
      "has_requirement": true/false,
      "requirement_type": "建立制度/定期执行/人员配备/岗位分离/文件保存/建立组织/null",
      "confidence": "high/medium/low",
      "requirement_detail": {{
        "what": "制度/工作名称",
        "scope": "适用范围",
        "frequency": "执行频率",
        "content": "具体内容"
      }},
      "vector_suggestion_correct": true/false,
      "reasoning": "判断理由（50 字内）"
    }}
  ]
}}

## 判断标准

**建立制度**：
- 关键词：制定、建立、编制、制度、规定、办法、规程
- 示例："制定信息安全管理制度"

**定期执行**：
- 关键词：每年、每季度、定期、开展、进行、检查、评估、演练
- 示例："每年开展安全检查"

**人员配备**：
- 关键词：配备、设置、指定、人员、岗位、专人
- 示例："配备专职安全人员"

**岗位分离**：
- 关键词：分离、不相容、职责、分工、制衡
- 示例："职责分离"

**文件保存**：
- 关键词：保存、留存、归档、文档、记录、档案
- 示例："保存检查记录"

**建立组织**：
- 关键词：成立、建立、设立、委员会、小组、机构
- 示例："成立信息安全委员会"

**不包含制度要求**：
- 仅检查技术配置
- 仅检查现有工作是否开展
- 询问现状，无建设性要求
"""
```

---

## 三、代码实现方案

### 3.1 新增文件结构

```
2-policy-compliance-checker/
└── scripts/
    ├── __init__.py
    ├── policy_extractor.py          # 主入口（已存在）
    ├── vector_screener.py           # 向量筛选器（已存在）
    ├── db_manager.py                # 数据库管理（已存在）
    ├── llm_analyzer.py              # 【新增】LLM 分析器
    ├── prompt_templates.py          # 【新增】提示词模板
    └── analyzers/
        ├── __init__.py
        ├── screening_reporter.py    # 筛选报告（已存在）
        └── policy_reporter.py       # 政策报告（已存在）
```

### 3.2 LLMAnalyzer 类设计

```python
# -*- coding: utf-8 -*-
"""
LLM 分析器 - 对中置信度审计项进行精细分析
"""
import os
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class LLMAnalysisResult:
    """LLM 分析结果"""
    item_id: int
    item_code: str
    has_requirement: bool
    requirement_type: Optional[str]
    confidence: str  # high/medium/low
    requirement_detail: Optional[Dict]
    reasoning: str
    vector_suggestion_correct: bool


class LLMAnalyzer:
    """LLM 分析器"""
    
    # 置信度阈值
    HIGH_CONFIDENCE = 0.70
    LOW_CONFIDENCE = 0.45
    
    # 制度要求类型
    REQUIREMENT_TYPES = [
        '建立制度', '定期执行', '人员配备',
        '岗位分离', '文件保存', '建立组织'
    ]
    
    def __init__(self, api_base: str = None, api_key: str = None, model: str = None):
        # 加载 LLM 配置（复用 LLMVerifier 的配置方式）
        self.api_base = api_base or os.environ.get('ARK_BASE_URL') or os.environ.get('LLM_API_BASE', '')
        self.api_key = api_key or os.environ.get('ARK_API_KEY') or os.environ.get('LLM_API_KEY', '')
        self.model = model or os.environ.get('ARK_CHAT_MODEL') or os.environ.get('LLM_MODEL', 'gpt-3.5-turbo')
        
        # 批量处理配置
        self.batch_size = 10  # 每批最多处理 10 条
        self.max_retries = 3  # 最大重试次数
    
    def analyze_batch(self, items: List[Dict]) -> List[LLMAnalysisResult]:
        """
        批量分析审计项
        
        Args:
            items: 中置信度审计项列表（来自向量筛选）
        
        Returns:
            LLM 分析结果列表
        """
        results = []
        
        # 分批处理
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            print(f"处理批次 {i//self.batch_size + 1}: {len(batch)} 条...")
            
            batch_results = self._process_batch(batch)
            results.extend(batch_results)
        
        return results
    
    def _process_batch(self, batch: List[Dict]) -> List[LLMAnalysisResult]:
        """处理单个批次"""
        # 构建 Prompt
        prompt = self._build_batch_prompt(batch)
        
        # 调用 LLM
        response = self._call_llm(prompt)
        
        # 解析响应
        results = self._parse_response(response, batch)
        
        return results
    
    def _build_batch_prompt(self, batch: List[Dict]) -> str:
        """构建批量分析 Prompt"""
        items_json = json.dumps([
            {
                'item_id': item['item_id'],
                'item_code': item['item_code'],
                'item_title': item['item_title'],
                'dimension': item['dimension_name'],
                'procedure_text': item['procedure_text'],
                'vector_suggestion': item.get('suggested_type'),
                'vector_similarity': item.get('similarity')
            }
            for item in batch
        ], ensure_ascii=False, indent=2)
        
        return BATCH_ANALYSIS_PROMPT.format(
            count=len(batch),
            items_json=items_json
        )
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM API"""
        try:
            import openai
            
            client = openai.OpenAI(
                base_url=self.api_base,
                api_key=self.api_key
            )
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个 IT 审计专家，负责识别审计程序中的制度建设要求。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            return response.choices[0].message.content
        
        except ImportError:
            print("警告：openai 库未安装，使用模拟响应")
            return self._mock_response()
        except Exception as e:
            print(f"LLM 调用失败：{e}")
            raise
    
    def _parse_response(self, response: str, batch: List[Dict]) -> List[LLMAnalysisResult]:
        """解析 LLM 响应"""
        # 提取 JSON
        json_match = re.search(r'\{[\s\S]*\}', response)
        if not json_match:
            raise ValueError("LLM 响应中未找到 JSON")
        
        data = json.loads(json_match.group())
        
        results = []
        for item_data in data.get('analysis_results', []):
            result = LLMAnalysisResult(
                item_id=item_data['item_id'],
                item_code=item_data['item_code'],
                has_requirement=item_data['has_requirement'],
                requirement_type=item_data.get('requirement_type'),
                confidence=item_data.get('confidence', 'medium'),
                requirement_detail=item_data.get('requirement_detail'),
                reasoning=item_data.get('reasoning', ''),
                vector_suggestion_correct=item_data.get('vector_suggestion_correct', True)
            )
            results.append(result)
        
        return results
    
    def _mock_response(self) -> str:
        """模拟响应（用于测试）"""
        return json.dumps({
            "analysis_results": []
        }, ensure_ascii=False)
```

### 3.3 集成到 PolicyRequirementExtractor

```python
# 修改 policy_extractor.py
class PolicyRequirementExtractor:
    """制度要求提取器 - 向量+LLM 两阶段"""
    
    def __init__(self, db_path: str, force_full: bool = False, output_dir: str = None):
        self.db_path = db_path
        self.force_full = force_full
        self.db = PolicyDatabaseManager(db_path)
        self.screener = PolicyVectorScreener()
        self.llm_analyzer = LLMAnalyzer()  # 新增
        self.output_dir = output_dir or ...
    
    def extract(self) -> Dict:
        """执行提取流程（完整两阶段）"""
        print("=" * 60)
        print("制度要求提取器 - 向量 +LLM 两阶段")
        print("=" * 60)
        
        batch_id = self._generate_batch_id()
        print(f"批次号：{batch_id}")
        
        items = self._load_unscreened_items()
        if not items:
            print("所有审计项已筛选完成，无新增项")
            return {'status': 'no_items', 'batch_id': batch_id}
        
        print(f"\n加载 {len(items)} 条待筛选审计项")
        self.db.init_policy_tables()
        
        # === 阶段 1：向量语义筛选 ===
        print("\n=== 阶段 1：向量语义筛选 ===")
        high_confidence, medium_confidence, skipped = self.screener.screen(items)
        
        # 保存高置信度结果
        if high_confidence:
            records = self._convert_to_records(high_confidence, 'confirmed')
            high_count = self.db.batch_save_screening_results(records, batch_id)
            print(f"保存 {high_count} 条高置信度记录")
        
        # === 阶段 2：LLM 精细分析 ===
        print("\n=== 阶段 2：LLM 精细分析 ===")
        if medium_confidence:
            llm_results = self.llm_analyzer.analyze_batch(medium_confidence)
            
            # 转换 LLM 结果为数据库记录
            llm_records = self._convert_llm_results_to_records(llm_results, batch_id)
            llm_count = self.db.batch_save_screening_results(llm_records, batch_id)
            print(f"保存 {llm_count} 条 LLM 分析结果")
        
        # 生成统计报告
        result = {
            'status': 'success',
            'batch_id': batch_id,
            'total_items': len(items),
            'high_confidence': len(high_confidence),
            'medium_confidence': len(medium_confidence),
            'skipped': skipped,
            'llm_analyzed': len(medium_confidence) if medium_confidence else 0
        }
        
        result_path = self._save_result(result)
        result['result_path'] = result_path
        
        print(f"\n结果已保存：{result_path}")
        
        return result
```

---

## 四、测试方案

### 4.1 单元测试

```python
# tests/test_llm_analyzer.py
class TestLLMAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = LLMAnalyzer()
    
    def test_single_item_analysis(self):
        """测试单条审计项分析"""
        test_item = {
            'item_id': 1,
            'item_code': 'TEST-001',
            'item_title': '检查是否建立信息安全管理制度',
            'dimension_name': '信息安全',
            'procedure_text': '检查是否建立信息安全管理制度',
            'suggested_type': '建立制度',
            'similarity': 0.65
        }
        
        results = self.analyzer.analyze_batch([test_item])
        
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].has_requirement)
        self.assertEqual(results[0].requirement_type, '建立制度')
    
    def test_batch_analysis(self):
        """测试批量分析"""
        test_items = [...]  # 10 条测试数据
        
        results = self.analyzer.analyze_batch(test_items)
        
        self.assertEqual(len(results), 10)
        for result in results:
            self.assertIn(result.requirement_type, self.analyzer.REQUIREMENT_TYPES + [None])
```

### 4.2 集成测试

```python
# tests/test_full_extraction.py
class TestFullExtraction(unittest.TestCase):
    def test_two_stage_extraction(self):
        """测试完整的两阶段提取流程"""
        extractor = PolicyRequirementExtractor(
            db_path='tests/test_data/test_it_audit.db',
            force_full=True
        )
        
        result = extractor.extract()
        
        self.assertEqual(result['status'], 'success')
        self.assertGreater(result['high_confidence'], 0)
        self.assertGreater(result['llm_analyzed'], 0)
```

---

## 五、预期效果

### 5.1 性能提升

| 指标 | 阶段一（仅向量） | 阶段二（向量+LLM） | 提升 |
|------|----------------|------------------|------|
| 处理时间 | <5 秒 | 30-60 秒 | - |
| 准确率 | ~75% | ~95% | +20% |
| LLM 调用 | 0 次 | 10-15 次 | - |
| 人工复核 | 需要 | 不需要 | 节省人力 |

### 5.2 输出示例

**阶段一输出（向量筛选）：**
```json
{
  "item_code": "NEW-001",
  "requirement_type": "建立制度",
  "confidence": 0.65,
  "status": "pending"
}
```

**阶段二输出（LLM 分析后）：**
```json
{
  "item_code": "NEW-001",
  "has_requirement": true,
  "requirement_type": "建立制度",
  "confidence": "high",
  "requirement_detail": {
    "what": "信息安全管理制度",
    "scope": "全公司",
    "frequency": null,
    "content": "建立信息安全管理制度，明确信息安全责任"
  },
  "reasoning": "明确要求建立制度，属于制度建设要求",
  "vector_suggestion_correct": true,
  "status": "confirmed"
}
```

---

## 六、实施步骤

### Step 1: 创建提示词模板文件
- 文件：`prompt_templates.py`
- 内容：系统 Prompt、单条分析 Prompt、批量分析 Prompt
- 时间：30 分钟

### Step 2: 实现 LLMAnalyzer 类
- 文件：`llm_analyzer.py`
- 功能：批量分析、JSON 解析、错误处理
- 时间：2 小时

### Step 3: 集成到 PolicyRequirementExtractor
- 修改：`policy_extractor.py`
- 功能：调用 LLM 分析、保存结果
- 时间：1 小时

### Step 4: 编写测试
- 文件：`tests/test_llm_analyzer.py`
- 内容：单元测试、集成测试
- 时间：1 小时

### Step 5: 测试与调试
- 使用测试数据库运行完整流程
- 调整 Prompt、优化参数
- 时间：2 小时

**总预计时间：6.5 小时**

---

## 七、风险与应对

### 风险 1：LLM 响应格式不稳定
**应对：**
- 使用正则表达式提取 JSON
- 添加 JSON 格式验证
- 失败时自动重试（最多 3 次）

### 风险 2：批量处理超时
**应对：**
- 限制每批数量（10 条）
- 设置合理的 timeout
- 支持断点续传

### 风险 3：LLM 判断错误
**应对：**
- 保留向量模型建议作为参考
- 标记 LLM 置信度（high/medium/low）
- 提供人工复核接口

---

## 八、总结

阶段二（LLM 精细分析）是模块 2 的核心价值所在，通过向量筛选 +LLM 确认的两阶段架构，实现了：

1. **高效率**：向量筛选快速初筛，LLM 只处理中置信度项
2. **高准确率**：LLM 深度分析，准确率从 75% 提升到 95%
3. **低成本**：LLM 调用次数减少 80%+
4. **可追溯**：完整的决策链路记录

通过本方案的实施，模块 2 将成为一个高效、准确、可靠的制度合规检查工具。
