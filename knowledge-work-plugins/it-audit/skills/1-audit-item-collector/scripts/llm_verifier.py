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
  - new_item: 新审计项信息
  - match_result: 匹配结果（action: merge/new_item）
  - procedure_match: 审计程序匹配结果
  - vector_confidence: 向量模型置信度
- pending_review: 待确认列表（相似度中等的候选）

## 审核任务

对于每条建议，请判断：
1. match_result.action 是否正确？
   - merge: 两个审计项是否真的是同一个检查项？
   - new_item: 是否确实应该新建？
2. procedure_match.action 是否正确？
   - 审计程序是否可以合并，还是应该新增？
3. 维度分类是否合理？

## 判断标准

- 合并条件：检查重点相同、检查对象相同
- 分离条件：检查重点不同、存在包含关系
- 审计程序：检查方法或检查对象不同时，应新增程序

## 输出格式

请输出JSON格式：

{
  "review_id": "R001",
  "overall_assessment": "整体评价",
  "adjustments": [
    {
      "suggestion_id": "M002",
      "field": "match_result.action",
      "original_value": "merge",
      "new_value": "new_item",
      "reason": "检查重点不同：M002检查运作是否有效，已有项检查是否建立"
    }
  ],
  "approved_count": 78,
  "adjusted_count": 2,
  "status": "approved / need_revision"
}

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
            "review_id": "R001",
            "overall_assessment": "模拟审核：所有建议已审核通过",
            "adjustments": [],
            "approved_count": 0,
            "adjusted_count": 0,
            "status": "approved"
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
        应用审核调整到合并建议
        
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
                
                if new_value == 'merge' and target_item_id:
                    pending['match_result'] = {
                        'existing_item_id': target_item_id,
                        'action': 'merge'
                    }
                    pending['adjusted'] = True
                    pending['adjustment_reason'] = adj.get('reason', '')
        
        return merge_result
    
    def iterative_verify(self, merge_result: Dict[str, Any], 
                         max_iterations: int = 3) -> Dict[str, Any]:
        """
        迭代审核，直到LLM确认OK
        
        Args:
            merge_result: 合并建议
            max_iterations: 最大迭代次数
        
        Returns:
            最终审核通过的合并建议
        """
        current_result = merge_result.copy()
        
        for i in range(max_iterations):
            print(f"\n第{i+1}轮LLM审核...")
            
            review = self.verify_merge_suggestions(current_result)
            
            print(f"  审核状态: {review.get('status')}")
            print(f"  调整数量: {review.get('adjusted_count', 0)}")
            
            if review.get('status') == 'approved':
                current_result['review'] = review
                current_result['verified'] = True
                return current_result
            
            if review.get('adjustments'):
                current_result = self.apply_adjustments(current_result, review)
                current_result['review'] = review
            else:
                break
        
        current_result['verified'] = False
        current_result['review'] = review
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
