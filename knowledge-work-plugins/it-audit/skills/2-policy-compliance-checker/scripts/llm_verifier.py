# -*- coding: utf-8 -*-
"""
LLM 校验器 - 对向量模型的分类结果进行校验

功能：
- 批量校验中置信度审计项的向量模型分类是否正确
- 如果错误，给出正确的类型建议
"""
import os
import json
import re
import time
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class VerificationResult:
    """LLM 校验结果"""
    item_id: int
    item_code: str
    vector_suggestion_correct: bool
    corrected_type: str | None
    reasoning: str


class PolicyLLMVerifier:
    """制度分类 LLM 校验器"""
    
    # 制度要求类型
    REQUIREMENT_TYPES = [
        '建立制度', '定期执行', '人员配备',
        '岗位分离', '文件保存', '建立组织'
    ]
    
    # 批量校验 Prompt
    BATCH_VERIFICATION_PROMPT = """请批量校验向量模型对以下审计项的分类是否正确。

## 待校验的审计项（共{count}条）

{items_json}

## 制度类型定义（6 种）

1. **建立制度**：要求制定、建立、编制、完善、包含某种制度/规定/办法/规程
   - 关键词：制定、建立、编制、完善、包含、制度、规定、办法、规程
   - 示例："制定信息安全管理制度"、"变更管理制度是否包含审批流程"
   - 注意：不仅包括"建立新制度"，也包括"制度应包含某内容"

2. **定期执行**：要求定期（每年/每季度）开展检查/评估/演练/审计
   - 关键词：每年、每季度、定期、开展、进行、检查、评估、演练
   - 示例："每年开展安全检查"、"定期进行风险评估"

3. **人员配备**：要求配备人员、设置岗位、指定专人负责
   - 关键词：配备、设置、指定、人员、岗位、专人
   - 示例："配备专职安全人员"、"设置安全管理岗位"

4. **岗位分离**：要求职责分离、不相容岗位分离
   - 关键词：分离、不相容、职责、分工、制衡
   - 示例："职责分离"、"不相容岗位分离"

5. **文件保存**：要求保存文档、留存记录、归档
   - 关键词：保存、留存、归档、文档、记录、档案
   - 示例："保存检查记录"、"留存审计文档"

6. **建立组织**：要求成立委员会、领导小组、工作机构
   - 关键词：成立、建立、设立、委员会、小组、机构
   - 示例："成立信息安全委员会"、"建立领导小组"

## 判断规则

**重要：以下情况都属于"建立制度"类型**：
- 明确要求建立新制度
- 要求现有制度应包含特定内容（如"XX 制度是否包含 YY 条款"）
- 要求完善、修订现有制度

**如果向量模型建议的类型正确**，设置 `vector_suggestion_correct` 为 `true`，`corrected_type` 为 `null`

**如果向量模型建议的类型错误**，设置 `vector_suggestion_correct` 为 `false`，并在 `corrected_type` 中给出正确的类型（必须是上述 6 种之一）

**如果不包含任何制度要求**（纯技术检查、现状检查），设置 `vector_suggestion_correct` 为 `false`，`corrected_type` 为 `null`

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

## 示例

**示例 1：建立制度（包含制度内容）**
- 审计程序："变更管理制度是否包含审批流程"
- 向量模型建议："建立制度"
- 输出：
{{
  "vector_suggestion_correct": true,
  "corrected_type": null,
  "reasoning": "要求制度包含特定内容，属于建立制度类型"
}}

**示例 2：建立制度（建立新制度）**
- 审计程序："检查是否建立信息安全管理制度"
- 向量模型建议："建立制度"
- 输出：
{{
  "vector_suggestion_correct": true,
  "corrected_type": null,
  "reasoning": "明确要求建立制度"
}}

**示例 3：定期执行**
- 审计程序："检查是否每年开展安全检查"
- 向量模型建议："建立制度"
- 输出：
{{
  "vector_suggestion_correct": false,
  "corrected_type": "定期执行",
  "reasoning": "应为定期执行，不是建立制度"
}}
"""
    
    def __init__(self, api_base: str = None, api_key: str = None, model: str = None):
        """
        初始化 LLM 校验器
        
        Args:
            api_base: LLM API 基础 URL
            api_key: LLM API 密钥
            model: 使用的模型名称
        """
        self.api_base = api_base or os.environ.get('ARK_BASE_URL') or os.environ.get('LLM_API_BASE', '')
        self.api_key = api_key or os.environ.get('ARK_API_KEY') or os.environ.get('LLM_API_KEY', '')
        self.model = model or os.environ.get('ARK_CHAT_MODEL') or os.environ.get('LLM_MODEL', 'gpt-3.5-turbo')
        
        # 批量处理配置
        self.batch_size = 20  # 每批最多处理 20 条（经过测试的最优批量）
        self.max_retries = 3  # 最大重试次数
        self.temperature = 0.1  # 低温，保证输出稳定
    
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
        if not items:
            return []
        
        results = []
        total_start_time = time.time()
        
        # 分批处理
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_start_time = time.time()
            print(f"LLM 校验批次 {i//self.batch_size + 1}: {len(batch)} 条...")
            
            batch_results = self._process_batch(batch)
            results.extend(batch_results)
            
            batch_elapsed = time.time() - batch_start_time
            print(f"  批次耗时：{batch_elapsed:.2f} 秒")
        
        total_elapsed = time.time() - total_start_time
        print(f"LLM 校验完成，共处理 {len(results)} 条，总耗时：{total_elapsed:.2f} 秒 ({len(results)/total_elapsed:.1f} 条/秒)")
        return results
    
    def _process_batch(self, batch: List[Dict]) -> List[VerificationResult]:
        """
        处理单个批次
        
        Args:
            batch: 一批审计项
        
        Returns:
            校验结果列表
        """
        # 构建 Prompt
        prompt = self._build_verification_prompt(batch)
        
        # 调用 LLM（带重试）
        response = None
        for attempt in range(self.max_retries):
            try:
                response = self._call_llm(prompt)
                break
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"LLM 调用失败，重试 ({attempt + 1}/{self.max_retries}): {e}")
                else:
                    raise
        
        # 解析响应
        results = self._parse_response(response, batch)
        
        return results
    
    def _build_verification_prompt(self, batch: List[Dict]) -> str:
        """
        构建批量校验 Prompt
        
        Args:
            batch: 一批审计项
        
        Returns:
            格式化后的 Prompt
        """
        items_json = json.dumps([
            {
                'item_id': item['item_id'],
                'item_code': item['item_code'],
                'item_title': item['item_title'][:100],  # 限制长度
                'dimension': item['dimension_name'],
                'procedure_text': item['procedure_text'][:300],  # 限制长度
                'vector_suggestion': item.get('suggested_type'),
                'similarity': round(item.get('similarity', 0), 4)
            }
            for item in batch
        ], ensure_ascii=False, indent=2)
        
        return self.BATCH_VERIFICATION_PROMPT.format(
            count=len(batch),
            items_json=items_json
        )
    
    def _call_llm(self, prompt: str) -> str:
        """
        调用 LLM API
        
        Args:
            prompt: 用户 Prompt
        
        Returns:
            LLM 响应文本
        """
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
                temperature=self.temperature,
                max_tokens=3000
            )
            
            return response.choices[0].message.content
        
        except ImportError:
            error_msg = "错误：openai 库未安装，请运行：pip install openai"
            print(error_msg)
            raise ImportError(error_msg)
        
        except Exception as e:
            error_msg = f"LLM 调用失败：{str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def _parse_response(self, response: str, batch: List[Dict]) -> List[VerificationResult]:
        """
        解析 LLM 响应
        
        Args:
            response: LLM 响应文本
            batch: 原始批次数据（用于校验）
        
        Returns:
            校验结果列表
        """
        # 提取 JSON
        json_match = re.search(r'\{[\s\S]*\}', response)
        if not json_match:
            raise ValueError("LLM 响应中未找到 JSON 格式数据")
        
        json_str = json_match.group()
        
        # 尝试解析 JSON，如果失败则清理特殊字符
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            # 清理特殊字符：换行符、制表符等
            json_str_clean = json_str.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
            try:
                data = json.loads(json_str_clean)
            except json.JSONDecodeError as e2:
                raise ValueError(f"JSON 解析失败：{str(e2)}")
        
        # 解析结果
        results = []
        verification_results = data.get('verification_results', [])
        
        for item_data in verification_results:
            # 校验必需字段
            if 'item_id' not in item_data or 'vector_suggestion_correct' not in item_data:
                continue
            
            # 校验 corrected_type 是否合法
            corrected_type = item_data.get('corrected_type')
            if corrected_type is not None and corrected_type not in self.REQUIREMENT_TYPES:
                print(f"警告：LLM 返回了不合法的 corrected_type: {corrected_type}")
                corrected_type = None
            
            result = VerificationResult(
                item_id=item_data['item_id'],
                item_code=item_data.get('item_code', ''),
                vector_suggestion_correct=item_data['vector_suggestion_correct'],
                corrected_type=corrected_type,
                reasoning=item_data.get('reasoning', '')
            )
            results.append(result)
        
        # 校验结果数量
        if len(results) != len(batch):
            print(f"警告：LLM 返回 {len(results)} 条结果，但期望 {len(batch)} 条")
        
        return results
    
    def _mock_response(self, batch: List[Dict]) -> str:
        """
        生成模拟响应（用于测试）
        
        Args:
            batch: 一批审计项
        
        Returns:
            模拟的 JSON 响应
        """
        mock_results = [
            {
                'item_id': item['item_id'],
                'item_code': item['item_code'],
                'vector_suggestion_correct': True,
                'corrected_type': None,
                'reasoning': '模拟响应：向量模型判断正确'
            }
            for item in batch
        ]
        
        return json.dumps({
            'verification_results': mock_results
        }, ensure_ascii=False)
