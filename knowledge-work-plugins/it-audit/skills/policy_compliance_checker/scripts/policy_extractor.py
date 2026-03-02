# -*- coding: utf-8 -*-
"""
制度要求提取器
从审计项中提取制度建设要求
"""

import os
import json
import sqlite3
import uuid
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


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


class LLMClient:
    """LLM客户端 - 使用OpenAI接口"""

    def __init__(self, api_base: str = None, api_key: str = None, model: str = None):
        # 支持两种环境变量命名：Agent框架使用的 ARK_* 和传统的 LLM_*
        self.api_base = api_base or os.environ.get('ARK_BASE_URL') or os.environ.get('LLM_API_BASE', '')
        self.api_key = api_key or os.environ.get('ARK_API_KEY') or os.environ.get('LLM_API_KEY', '')
        # 模块2专用模型配置：优先使用 POLICY_MODEL，其次 ARK_CHAT_MODEL，最后默认
        self.model = model or os.environ.get('POLICY_MODEL') or os.environ.get('ARK_CHAT_MODEL') or os.environ.get('LLM_MODEL', 'gpt-3.5-turbo')

    def chat(self, prompt: str) -> str:
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
                    {"role": "system", "content": "你是一个IT审计专家，擅长从审计程序中提取制度建设要求。请严格按照指定的JSON格式输出。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=8000
            )

            return response.choices[0].message.content

        except ImportError:
            print("警告: openai库未安装，使用模拟响应")
            return self._mock_response(prompt)
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        """模拟LLM响应（用于测试）"""
        # 从prompt中提取批次信息
        batch_id_match = re.search(r'批次号:\s*(\S+)', prompt)
        batch_id = batch_id_match.group(1) if batch_id_match else "MOCK"

        extract_time = datetime.now().isoformat()

        # 解析审计项数量
        items_match = re.search(r'审计项数量:\s*(\d+)', prompt)
        total_items = int(items_match.group(1)) if items_match else 0

        return json.dumps({
            "batch_id": batch_id,
            "extract_time": extract_time,
            "total_items": total_items,
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
        }, ensure_ascii=False)


class PolicyRequirementExtractor:
    """制度要求提取器"""

    def __init__(self, db_path: str, llm_client: Optional[LLMClient] = None, output_dir: str = None):
        """
        初始化提取器

        Args:
            db_path: 数据库路径
            llm_client: LLM客户端（可选，默认使用环境变量配置）
            output_dir: 输出目录，默认为当前目录下的results
        """
        self.db_path = db_path
        self.llm = llm_client or LLMClient()
        self.batch_id = self._generate_batch_id()
        self.batch_size = 100
        self.output_dir = output_dir or os.path.join(os.getcwd(), 'audit-analysis-tool', 'output', 'module2_policy')

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
        """构建LLM提示词 - 精简版"""
        extract_time = datetime.now().isoformat()

        # 构建审计项列表文本 - 压缩格式
        items_text = []
        for i, item in enumerate(batch, 1):
            # 合并审计程序为一个字符串，减少格式开销
            procedures = ' | '.join(item['procedures'])
            # 精简格式：编号|维度|标题|程序
            item_text = f"{i}|{item['item_code']}|{item['dimension_name']}|{item['title']}|{procedures}"
            items_text.append(item_text)

        all_items_text = '\n'.join(items_text)

        prompt = f"""你是IT审计专家，分析审计程序并提取制度建设要求。

【批次】{self.batch_id}|{batch_num}|{len(batch)}|{extract_time}

【审计项】格式:序号|编码|维度|标题|程序
{all_items_text}

【分类标准】
- 建立制度：制定/建立/编制**制度、规定、办法、规程**（常态化管理制度）
- 定期执行：每年/每季度/每月/**定期**开展检查、评估、演练（周期性工作）
- 人员配备：配备/设置/**指定**某岗位/人员（长期人员配置）
- 岗位分离：职责分离/不相容岗位分离（岗位制衡机制）
- 文件保存：保存/**留存**/**归档**文档、记录（档案管理）
- 建立组织：成立/**建立**委员会、小组、部门（组织架构）

【排除项 - 不提取】
- 专项任务：建党100周年、冬奥会、世博会等临时性保障
- 临时清单：自查清单、检查清单、临时方案
- 一次性工作：单次评估、临时检查

【输出格式】每行一条：审计项编码###要求类型###置信度

【示例】
NEW-001###建立制度###0.95
NEW-002###定期执行###0.90
NEW-003###人员配备###0.85

【要求】
1.只返回有制度要求的审计项编码和类型
2.一个审计项可能对应多个要求类型，分别列出
3.type只能是：建立制度/定期执行/人员配备/岗位分离/文件保存/建立组织
4.置信度0-1
5.无要求的审计项不输出"""
        return prompt

    def _parse_response(self, response: str, batch_items: List[Dict]) -> Dict:
        """解析LLM响应 - 精简格式，从数据库查询完整信息"""
        # 建立审计项编码到完整信息的映射
        item_map = {item['item_code']: item for item in batch_items}

        normalized = {
            'policy_requirements': []
        }

        lines = response.strip().split('\n')
        req_counter = 1

        for line in lines:
            line = line.strip()
            if not line or line.startswith('【') or line.startswith('示例') or line.startswith('格式'):
                continue

            # 解析精简格式: icode###type###conf
            parts = line.split('###')
            if len(parts) >= 3:
                icode = parts[0]
                req_type = parts[1]
                conf = float(parts[2]) if parts[2] else 0.5

                # 从数据库查询完整信息
                item = item_map.get(icode, {})

                normalized_req = {
                    'requirement_id': f"REQ-{req_counter:03d}",
                    'source_item_code': icode,
                    'source_item_title': item.get('title', ''),
                    'source_dimension': item.get('dimension_name', ''),
                    'requirement_type': req_type,
                    'requirement_content': '',  # 可从审计程序生成
                    'related_clues': [],
                    'confidence': conf
                }
                normalized['policy_requirements'].append(normalized_req)
                req_counter += 1

        return normalized

    def _process_batch(self, batch: List[Dict], batch_num: int) -> Dict:
        """处理单个批次"""
        # 1. 构建提示词
        prompt = self._build_prompt(batch, batch_num)

        # 2. 调用LLM
        print(f"  调用LLM分析批次 {batch_num}...")
        response = self.llm.chat(prompt)

        # 3. 解析结果（传入batch用于查询完整信息）
        result = self._parse_response(response, batch)

        # 4. 添加批次信息
        result['batch_seq'] = batch_num
        result['batch_id'] = self.batch_id
        result['total_items'] = len(batch)

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

        req_counter = 1
        for result in batch_results:
            reqs = result.get('policy_requirements', [])
            for req in reqs:
                # 重新编号
                req['requirement_id'] = f"REQ-{req_counter:03d}"
                all_requirements.append(req)
                req_counter += 1

                # 统计类型
                req_type = req.get('requirement_type', '')
                if req_type in type_counts:
                    type_counts[req_type] += 1

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
    # 主程序入口
    db_path = r"e:\mycode\agent-team\tests\test_data\test_it_audit.db"

    # 创建提取器（自动使用环境变量中的LLM配置）
    extractor = PolicyRequirementExtractor(db_path)

    # 执行提取
    result_path = extractor.extract()
    print(f"\n提取完成！结果文件: {result_path}")
