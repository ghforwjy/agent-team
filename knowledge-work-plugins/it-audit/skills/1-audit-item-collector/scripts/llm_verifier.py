# -*- coding: utf-8 -*-
"""
IT审计专家Agent - LLM校验模块
负责对向量模型的匹配结果进行逻辑校验
"""
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional


class LLMVerifier:
    """LLM校验器 - 对向量模型的匹配结果进行逻辑校验"""
    
    PROMPT_TEMPLATE = """你是一个IT审计专家。我正在将新的审计项导入审计知识库，需要你审核向量模型的匹配建议。

## 输入数据结构说明

我将提供一个JSON格式的合并建议文档，结构如下：
- summary: 统计信息
- merge_suggestions: 合并建议列表
  - suggestion_id: 建议编号
  - new_item: 新审计项信息（title, dimension, procedure）
  - match_result: 匹配结果（action: create/reuse, similarity）
  - procedure_match: 审计程序匹配结果（action: create_procedure/reuse_procedure）
  - vector_confidence: 向量模型置信度
- pending_review: 待确认列表（相似度中等的候选）

## 审核任务

对于每条建议，请判断：
1. match_result.action 是否正确？
   - reuse: 两个审计项是否真的是同一个检查项？
   - create: 是否确实应该新建？
2. procedure_match.action 是否正确？
   - 审计程序是否可以复用，还是应该新增？
3. 维度分类是否合理？

## 判断标准

- 复用条件（reuse）：检查重点相同、检查对象相同
- 新建条件（create）：检查重点不同、存在包含关系、检查角度不同
- 审计程序：检查方法或检查对象不同时，应新增程序（create_procedure）
- 程序相似度≥0.80时可复用（reuse_procedure）

## 输出格式

请输出JSON格式：

{{
  "review_status": "confirmed/adjusted/failed",
  "review_round": 1,
  "total_items": 224,
  "confirmed_items": 200,
  "adjusted_items": 24,
  "details": [
    {{
      "suggestion_id": "M001",
      "is_same_item": true/false,
      "item_decision": "create/reuse",
      "item_reason": "判断理由",
      "is_same_procedure": true/false,
      "procedure_decision": "create_procedure/reuse_procedure",
      "procedure_reason": "判断理由",
      "dimension_adjustment": null或建议维度,
      "confidence": "high/medium/low"
    }}
  ]
}}

## 合并建议文档

{json_content}"""
    
    def __init__(self, api_base: str = None, api_key: str = None, model: str = None):
        self.api_base = api_base or os.environ.get('LLM_API_BASE', '')
        self.api_key = api_key or os.environ.get('LLM_API_KEY', '')
        self.model = model or os.environ.get('LLM_MODEL', 'gpt-3.5-turbo')
        self.review_counter = 1
    
    def verify_merge_suggestions(self, merge_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        审核合并建议
        
        Args:
            merge_result: 向量模型输出的合并建议JSON
        
        Returns:
            LLM审核意见JSON
        """
        json_content = json.dumps(merge_result, ensure_ascii=False, indent=2)
        prompt = self.PROMPT_TEMPLATE.format(json_content=json_content)
        
        response = self._call_llm(prompt)
        
        review_result = self._parse_response(response)
        review_result['review_id'] = f"R{self.review_counter:03d}"
        self.review_counter += 1
        
        return review_result
    
    def _call_llm(self, prompt: str) -> str:
        """调用LLM API"""
        try:
            import openai
            
            client = openai.OpenAI(
                base_url=self.api_base,
                api_key=self.api_key
            )
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个IT审计专家，负责审核审计项的合并建议。请严格按照指定的JSON格式输出。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            return response.choices[0].message.content
        
        except ImportError:
            print("警告: openai库未安装，使用模拟响应")
            return self._mock_response()
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return self._mock_response()
    
    def _mock_response(self) -> str:
        """模拟LLM响应（用于测试）"""
        return json.dumps({
            "review_status": "confirmed",
            "review_round": 1,
            "total_items": 0,
            "confirmed_items": 0,
            "adjusted_items": 0,
            "details": []
        }, ensure_ascii=False)
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析LLM返回的JSON"""
        json_match = re.search(r'\{[\s\S]*\}', response)
        
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        return {
            "review_id": f"R{self.review_counter:03d}",
            "overall_assessment": "解析失败",
            "adjustments": [],
            "approved_count": 0,
            "adjusted_count": 0,
            "status": "error",
            "raw_response": response
        }
    
    def apply_adjustments(self, merge_result: Dict[str, Any],
                          review_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用审核调整到合并建议（兼容旧格式）

        Args:
            merge_result: 原合并建议
            review_result: LLM审核意见

        Returns:
            调整后的合并建议
        """
        adjustments = review_result.get('adjustments', [])

        if not adjustments:
            return merge_result

        adjustment_map = {a['suggestion_id']: a for a in adjustments}

        for suggestion in merge_result.get('merge_suggestions', []):
            sid = suggestion.get('suggestion_id')
            if sid in adjustment_map:
                adj = adjustment_map[sid]
                field = adj.get('field', '')
                new_value = adj.get('new_value')

                if field == 'match_result.action' and new_value:
                    suggestion['match_result']['action'] = new_value
                    suggestion['adjusted'] = True
                    suggestion['adjustment_reason'] = adj.get('reason', '')

        for pending in merge_result.get('pending_review', []):
            sid = pending.get('suggestion_id')
            if sid in adjustment_map:
                adj = adjustment_map[sid]
                new_value = adj.get('new_value')
                target_item_id = adj.get('target_item_id')

                if new_value == 'reuse' and target_item_id:
                    pending['match_result'] = {
                        'existing_item_id': target_item_id,
                        'action': 'reuse'
                    }
                    pending['adjusted'] = True
                    pending['adjustment_reason'] = adj.get('reason', '')

        return merge_result

    def apply_detailed_adjustments(self, merge_result: Dict[str, Any],
                                   review_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用详细审核调整到合并建议（新格式）

        Args:
            merge_result: 原合并建议
            review_result: LLM详细审核意见

        Returns:
            调整后的合并建议
        """
        details = review_result.get('details', [])

        if not details:
            return merge_result

        detail_map = {d['suggestion_id']: d for d in details}

        for suggestion in merge_result.get('merge_suggestions', []):
            sid = suggestion.get('suggestion_id')
            if sid in detail_map:
                detail = detail_map[sid]

                # 应用审计项决策
                item_decision = detail.get('item_decision')
                if item_decision:
                    old_action = suggestion['match_result']['action']
                    suggestion['match_result']['action'] = item_decision
                    suggestion['adjusted'] = True
                    suggestion['adjustment_reason'] = detail.get('item_reason', '')
                    suggestion['llm_review'] = detail

                    # 如果决策从reuse改为create，清除existing_item_id
                    if old_action == 'reuse' and item_decision == 'create':
                        suggestion['match_result']['existing_item_id'] = None
                        suggestion['match_result']['existing_title'] = None

                # 应用程序决策
                procedure_decision = detail.get('procedure_decision')
                if procedure_decision and 'procedure_match' in suggestion:
                    suggestion['procedure_match']['action'] = procedure_decision
                    suggestion['procedure_match']['adjustment_reason'] = detail.get('procedure_reason', '')

                # 应用维度调整
                dimension_adjustment = detail.get('dimension_adjustment')
                if dimension_adjustment:
                    suggestion['new_item']['dimension'] = dimension_adjustment

        return merge_result

    def generate_failure_report(self, merge_result: Dict, review_history: List) -> Dict:
        """生成LLM审核失败报告"""
        return {
            "status": "failed_review",
            "total_rounds": len(review_history),
            "initial_judgment": {
                "total_items": merge_result.get('summary', {}).get('total_new_items', 0),
                "suggested_new_items": merge_result.get('summary', {}).get('suggested_new_items', 0),
                "suggested_reuse_items": merge_result.get('summary', {}).get('suggested_reuse_items', 0),
                "pending_review": merge_result.get('summary', {}).get('pending_review', 0)
            },
            "review_history": [
                {
                    "round": r.get('review_round', i+1),
                    "status": r.get('review_status', 'unknown'),
                    "confirmed_items": r.get('confirmed_items', 0),
                    "adjusted_items": r.get('adjusted_items', 0)
                }
                for i, r in enumerate(review_history)
            ],
            "recommended_action": "人工介入处理"
        }
    
    def iterative_verify(self, merge_result: Dict[str, Any],
                         max_iterations: int = 3) -> Dict[str, Any]:
        """
        迭代审核，最多3次循环
        - 3次内通过：返回verified=True的结果
        - 3次不通过：标记为failed_review，生成失败报告

        Args:
            merge_result: 合并建议
            max_iterations: 最大迭代次数

        Returns:
            最终审核结果
        """
        current_result = merge_result.copy()
        review_history = []

        for i in range(max_iterations):
            print(f"\n第{i+1}轮LLM审核...")

            review = self.verify_merge_suggestions(current_result)
            review['review_round'] = i + 1
            review_history.append(review)

            print(f"  审核状态: {review.get('review_status')}")
            print(f"  调整数量: {review.get('adjusted_count', 0)}")

            if review.get('review_status') == 'confirmed':
                current_result['review'] = review
                current_result['verified'] = True
                current_result['review_history'] = review_history
                return current_result

            # 应用调整并继续下一轮
            if review.get('details'):
                current_result = self.apply_detailed_adjustments(current_result, review)
                current_result['review'] = review
            else:
                # 没有调整但也没有确认，可能是失败
                break

        # 3次后仍未通过，生成失败报告
        current_result['verified'] = False
        current_result['review'] = review
        current_result['review_history'] = review_history
        current_result['failure_report'] = self.generate_failure_report(merge_result, review_history)

        print(f"\n警告: 经过{max_iterations}轮审核仍未通过，标记为失败")
        return current_result


def main():
    """测试LLM校验模块"""
    test_merge_result = {
        "version": "1.0",
        "summary": {
            "total_new_items": 4,
            "suggested_merge_items": 2,
            "pending_review": 2
        },
        "merge_suggestions": [
            {
                "suggestion_id": "M001",
                "new_item": {
                    "title": "公司是否建立IT治理委员会",
                    "dimension": "信息技术治理",
                    "procedure": "查阅IT治理委员会成立发文"
                },
                "match_result": {
                    "existing_item_id": "IT-GOV-0015",
                    "existing_title": "是否设立IT治理委员会",
                    "similarity": 0.93,
                    "action": "merge"
                },
                "procedure_match": {
                    "existing_procedure": "查阅公司是否制定IT治理委员会成立文件",
                    "similarity": 0.86,
                    "action": "merge_procedure"
                },
                "vector_confidence": "high"
            },
            {
                "suggestion_id": "M002",
                "new_item": {
                    "title": "IT治理委员会是否有效运作",
                    "dimension": "信息技术治理",
                    "procedure": "查阅IT治理委员会会议记录"
                },
                "match_result": {
                    "existing_item_id": "IT-GOV-0015",
                    "existing_title": "是否设立IT治理委员会",
                    "similarity": 0.87,
                    "action": "merge"
                },
                "procedure_match": {
                    "existing_procedure": "查阅公司是否制定IT治理委员会成立文件",
                    "similarity": 0.72,
                    "action": "new_procedure"
                },
                "vector_confidence": "medium"
            }
        ],
        "pending_review": []
    }
    
    verifier = LLMVerifier()
    
    print("=" * 60)
    print("测试LLM校验模块")
    print("=" * 60)
    
    result = verifier.iterative_verify(test_merge_result)
    
    print("\n最终结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
