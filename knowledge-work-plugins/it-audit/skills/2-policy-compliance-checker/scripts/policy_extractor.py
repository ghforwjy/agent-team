# -*- coding: utf-8 -*-
"""
制度要求提取器
从审计项中提取制度建设要求
"""

import os
import json
import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class PolicyRequirement:
    """制度要求数据类"""
    requirement_id: str
    batch_id: str
    batch_seq: int
    extract_time: str
    source_item_code: str
    source_item_title: str
    source_dimension: str
    source_procedure: str
    requirement_type: str
    what: str
    scope: Optional[str]
    content: str
    frequency: Optional[str]
    quantity: Optional[str]
    qualification: Optional[str]
    retention_period: Optional[str]
    related_clues: List[str]
    confidence: float


class PolicyRequirementExtractor:
    """制度要求提取器"""
    
    def __init__(self, db_path: str, llm_client, output_dir: str = None):
        """
        初始化提取器
        
        Args:
            db_path: 数据库路径
            llm_client: LLM客户端（需实现chat方法）
            output_dir: 输出目录，默认为当前目录下的results
        """
        self.db_path = db_path
        self.llm = llm_client
        self.batch_id = self._generate_batch_id()
        self.batch_size = 100
        self.output_dir = output_dir or os.path.join(os.getcwd(), 'results')
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 验证数据库存在
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"数据库文件不存在: {db_path}")
    
    def _generate_batch_id(self) -> str:
        """生成批次号: POLICY-YYYYMMDD-XXXXXX"""
        date_str = datetime.now().strftime("%Y%m%d")
        short_uuid = uuid.uuid4().hex[:6].upper()
        return f"POLICY-{date_str}-{short_uuid}"
    
    def _load_audit_items(self) -> List[Dict]:
        """从数据库加载审计项"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询所有审计项及其维度信息
        cursor.execute('''
            SELECT 
                ai.id,
                ai.item_code,
                ai.title,
                ai.description,
                ai.severity,
                ad.id as dimension_id,
                ad.name as dimension_name,
                ad.code as dimension_code
            FROM audit_items ai
            JOIN audit_dimensions ad ON ai.dimension_id = ad.id
            WHERE ai.status = 'active'
            ORDER BY ai.id
        ''')
        
        items = []
        for row in cursor.fetchall():
            item = dict(row)
            # 加载该审计项的审计程序
            cursor.execute('''
                SELECT procedure_text 
                FROM audit_procedures 
                WHERE item_id = ? 
                ORDER BY is_primary DESC, id
            ''', (item['id'],))
            item['procedures'] = [r[0] for r in cursor.fetchall()]
            items.append(item)
        
        conn.close()
        return items
    
    def _split_batches(self, items: List[Dict]) -> List[List[Dict]]:
        """将审计项分批"""
        batches = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batches.append(batch)
        return batches
    
    def _build_prompt(self, batch: List[Dict], batch_num: int) -> str:
        """构建LLM提示词"""
        extract_time = datetime.now().isoformat()
        
        # 构建审计项列表文本
        items_text = []
        for i, item in enumerate(batch, 1):
            procedures_text = '\n'.join([f"  - {p}" for p in item['procedures']])
            item_text = f"""【审计项{i}】
编码: {item['item_code']}
维度: {item['dimension_name']}
标题: {item['title']}
程序:
{procedures_text}
"""
            items_text.append(item_text)
        
        all_items_text = '\n'.join(items_text)
        
        prompt = f"""你是一个IT审计专家，擅长从审计程序中提取制度建设要求。

请分析以下审计项批次，提取其中的制度建设要求。

【批次信息】
- 批次号: {self.batch_id}
- 批次序号: {batch_num}
- 审计项数量: {len(batch)}
- 提取时间: {extract_time}

【审计项列表】
{all_items_text}

请按以下JSON格式输出分析结果：

{{
  "batch_id": "{self.batch_id}",
  "extract_time": "{extract_time}",
  "total_items": {len(batch)},
  "policy_requirements": [
    {{
      "requirement_id": "REQ-001",
      "source_item_code": "审计项编码",
      "source_item_title": "审计项标题",
      "source_procedure": "来源的审计程序内容",
      "requirement_type": "建立制度/建立组织/人员配备/定期执行/岗位分离/文件保存",
      "requirement_detail": {{
        "what": "要求建立什么",
        "scope": "适用范围",
        "content": "具体要求内容",
        "frequency": "执行频率（定期执行类）",
        "quantity": "数量要求（人员配备类）",
        "qualification": "资格要求（人员配备类）",
        "retention_period": "保存期限（文件保存类）"
      }},
      "related_clues": ["关键词1", "关键词2", "关键词3"],
      "confidence": 0.95
    }}
  ],
  "statistics": {{
    "total_requirements": 30,
    "by_type": {{
      "建立制度": 12,
      "建立组织": 3,
      "人员配备": 5,
      "定期执行": 8,
      "岗位分离": 1,
      "文件保存": 1
    }}
  }}
}}

注意：
1. 只输出包含制度建设要求的审计项
2. 如果一个审计项包含多个制度要求，请分别列出
3. related_clues用于后续匹配制度文档，请提取3-5个关键词
4. confidence表示你对此提取结果的置信度(0-1)
5. 请确保JSON格式正确
"""
        return prompt
    
    def _parse_response(self, response: str) -> Dict:
        """解析LLM响应"""
        try:
            # 尝试直接解析JSON
            result = json.loads(response)
            return result
        except json.JSONDecodeError as e:
            # 尝试从响应中提取JSON部分
            try:
                # 查找JSON开始和结束位置
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    result = json.loads(json_str)
                    return result
            except:
                pass
            raise ValueError(f"无法解析LLM响应: {e}")
    
    def _process_batch(self, batch: List[Dict], batch_num: int) -> Dict:
        """处理单个批次"""
        # 1. 构建提示词
        prompt = self._build_prompt(batch, batch_num)
        
        # 2. 调用LLM
        response = self.llm.chat(prompt)
        
        # 3. 解析结果
        result = self._parse_response(response)
        
        # 4. 添加批次信息
        result['batch_seq'] = batch_num
        result['batch_id'] = self.batch_id
        
        # 5. 保存批次结果
        self._save_batch_result(result, batch_num)
        
        return result
    
    def _save_batch_result(self, result: Dict, batch_num: int):
        """保存批次结果"""
        filename = f"policy_req_{self.batch_id}_batch{batch_num}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    def _merge_results(self, batch_results: List[Dict]) -> Dict:
        """合并批次结果"""
        all_requirements = []
        type_counts = {
            "建立制度": 0,
            "建立组织": 0,
            "人员配备": 0,
            "定期执行": 0,
            "岗位分离": 0,
            "文件保存": 0
        }
        
        for result in batch_results:
            reqs = result.get('policy_requirements', [])
            all_requirements.extend(reqs)
            
            # 统计各类别数量
            stats = result.get('statistics', {}).get('by_type', {})
            for req_type, count in stats.items():
                if req_type in type_counts:
                    type_counts[req_type] += count
        
        final_result = {
            "version": "1.0",
            "batch_info": {
                "batch_id": self.batch_id,
                "extract_time": datetime.now().isoformat(),
                "total_batches": len(batch_results),
                "items_processed": sum(r.get('total_items', 0) for r in batch_results)
            },
            "summary": {
                "total_requirements_found": len(all_requirements),
                "by_type": type_counts
            },
            "policy_requirements": all_requirements
        }
        
        return final_result
    
    def _save_results(self, result: Dict) -> str:
        """保存最终结果"""
        filename = f"policy_req_{self.batch_id}_all.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def extract(self) -> str:
        """
        执行提取流程
        
        Returns:
            总结果文件路径
        """
        print(f"开始提取制度要求...")
        print(f"批次号: {self.batch_id}")
        
        # 1. 读取审计项
        print("读取审计项...")
        audit_items = self._load_audit_items()
        print(f"共读取 {len(audit_items)} 条审计项")
        
        # 2. 分批处理
        batches = self._split_batches(audit_items)
        print(f"划分为 {len(batches)} 个批次")
        
        batch_results = []
        for i, batch in enumerate(batches, 1):
            print(f"处理批次 {i}/{len(batches)} ({len(batch)} 条)...")
            result = self._process_batch(batch, i)
            batch_results.append(result)
            print(f"  发现 {result.get('statistics', {}).get('total_requirements', 0)} 条制度要求")
        
        # 3. 合并结果
        print("合并结果...")
        final_result = self._merge_results(batch_results)
        
        # 4. 保存结果
        output_path = self._save_results(final_result)
        print(f"结果已保存: {output_path}")
        print(f"总计发现 {final_result['summary']['total_requirements_found']} 条制度要求")
        
        return output_path


if __name__ == '__main__':
    # 测试代码
    class MockLLM:
        def chat(self, prompt: str) -> str:
            # 返回模拟响应
            return json.dumps({
                "batch_id": "TEST",
                "extract_time": datetime.now().isoformat(),
                "total_items": 100,
                "policy_requirements": [],
                "statistics": {
                    "total_requirements": 0,
                    "by_type": {
                        "建立制度": 0,
                        "建立组织": 0,
                        "人员配备": 0,
                        "定期执行": 0,
                        "岗位分离": 0,
                        "文件保存": 0
                    }
                }
            })
    
    # 测试
    db_path = r"e:\mycode\agent-team\tests\test_data\test_it_audit.db"
    extractor = PolicyRequirementExtractor(db_path, MockLLM())
    print(f"批次号: {extractor.batch_id}")
    items = extractor._load_audit_items()
    print(f"审计项数: {len(items)}")
