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
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

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


@dataclass
class BatchResult:
    """批次处理结果"""
    index: int
    success: bool
    response: Optional[str]
    error: Optional[str]


VALID_REQUIREMENT_TYPES = ['建立制度', '定期执行', '人员配备', '岗位分离', '文件保存', '建立组织']


class LLMClient:
    """LLM客户端 - 使用OpenAI接口"""

    def __init__(self, api_base: str = None, api_key: str = None, model: str = None, max_workers: int = 5):
        self.api_base = api_base or os.environ.get('ARK_BASE_URL') or os.environ.get('LLM_API_BASE', '')
        self.api_key = api_key or os.environ.get('ARK_API_KEY') or os.environ.get('LLM_API_KEY', '')
        self.model = model or os.environ.get('POLICY_MODEL') or os.environ.get('ARK_CHAT_MODEL') or os.environ.get('LLM_MODEL', 'gpt-3.5-turbo')
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def chat(self, prompt: str, timeout: int = 120) -> str:
        """调用LLM API"""
        try:
            import openai

            client = openai.OpenAI(
                base_url=self.api_base,
                api_key=self.api_key,
                timeout=timeout
            )

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个IT审计专家，擅长从审计程序中提取制度建设要求。请严格按照指定的JSON格式输出。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )

            return response.choices[0].message.content

        except ImportError:
            print("警告: openai库未安装，使用模拟响应")
            return self._mock_response(prompt)
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return self._mock_response(prompt)

    def chat_batch(self, prompts: List[str], timeout: int = 120) -> List[BatchResult]:
        """
        并行调用LLM API处理多个prompt
        
        Args:
            prompts: prompt列表
            timeout: 单个请求超时时间（秒）
            
        Returns:
            List[BatchResult]: 每个prompt的处理结果，包含成功/失败状态
        """
        results: List[BatchResult] = [None] * len(prompts)
        
        def call_with_index(args):
            idx, prompt = args
            try:
                response = self.chat(prompt, timeout)
                return BatchResult(index=idx, success=True, response=response, error=None)
            except Exception as e:
                error_msg = str(e)
                print(f"批次 {idx} 调用失败: {error_msg}")
                return BatchResult(index=idx, success=False, response=None, error=error_msg)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(call_with_index, (i, p)): i for i, p in enumerate(prompts)}
            for future in as_completed(futures):
                result = future.result()
                results[result.index] = result
        
        return results
    
    def chat_batch_with_retry(self, prompts: List[str], timeout: int = 120, max_retries: int = 2) -> List[BatchResult]:
        """
        并行调用LLM API，支持失败重试
        
        Args:
            prompts: prompt列表
            timeout: 单个请求超时时间（秒）
            max_retries: 最大重试次数
            
        Returns:
            List[BatchResult]: 每个prompt的处理结果
        """
        results = self.chat_batch(prompts, timeout)
        
        retry_count = 0
        while retry_count < max_retries:
            failed_indices = [r.index for r in results if not r.success]
            if not failed_indices:
                break
            
            print(f"重试 {len(failed_indices)} 个失败的批次 (第{retry_count + 1}次重试)...")
            retry_prompts = [prompts[i] for i in failed_indices]
            retry_results = self.chat_batch(retry_prompts, timeout)
            
            for rr in retry_results:
                if rr.success:
                    results[rr.index] = rr
            
            retry_count += 1
        
        failed_count = sum(1 for r in results if not r.success)
        if failed_count > 0:
            print(f"警告: {failed_count} 个批次最终失败")
        
        return results

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
    """制度要求提取器 - 两阶段处理"""

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
        self.stage1_batch_size = 50
        self.stage2_batch_size = 25
        self.output_dir = output_dir or os.path.join(os.getcwd(), 'audit-analysis-tool', 'output', 'module2_policy')

        os.makedirs(self.output_dir, exist_ok=True)

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
        """将审计项分批（旧方法，保留兼容）"""
        batches = []
        for i in range(0, len(items), self.stage2_batch_size):
            batch = items[i:i + self.stage2_batch_size]
            batches.append(batch)
        return batches

    def _split_stage1_batches(self, items: List[Dict]) -> List[List[Dict]]:
        """阶段1分批：50条/批"""
        batches = []
        for i in range(0, len(items), self.stage1_batch_size):
            batch = items[i:i + self.stage1_batch_size]
            batches.append(batch)
        return batches

    def _split_stage2_batches(self, items: List[Dict]) -> List[List[Dict]]:
        """阶段2分批：25条/批"""
        batches = []
        for i in range(0, len(items), self.stage2_batch_size):
            batch = items[i:i + self.stage2_batch_size]
            batches.append(batch)
        return batches

    def _build_stage1_prompt(self, items: List[Dict], batch_num: int) -> str:
        """
        构建阶段1提示词：快速筛选
        输入：编码 + 程序文本
        输出：编码###是
        """
        items_text = []
        for item in items:
            procedures = ' '.join(item['procedures'])
            items_text.append(f"{item['item_code']}: {procedures}")
        
        all_items_text = '\n'.join(items_text)
        
        prompt = f"""你是IT审计专家，判断审计项是否包含制度建设要求。

【制度要求类型】
- 建立制度：制定/建立制度、规定、办法、规程
- 定期执行：每年/每季度/定期开展检查、评估、演练
- 人员配备：配备/设置/指定岗位/人员
- 岗位分离：职责分离/不相容岗位分离
- 文件保存：保存/留存/归档文档、记录
- 建立组织：成立/建立委员会、小组、部门

【排除项 - 不提取】
- 专项任务：建党100周年、冬奥会、世博会等临时性保障
- 临时清单：自查清单、检查清单、临时方案
- 一次性工作：单次评估、临时检查

【审计项】
{all_items_text}

【输出格式】
只返回包含制度要求的项，格式：编码###是

【注意】
- 只输出包含制度要求的审计项
- 不包含制度要求的项不要输出"""
        return prompt

    def _parse_stage1_response(self, response: str, items: List[Dict]) -> Dict:
        """
        解析阶段1响应
        格式：编码###是
        """
        item_map = {item['item_code']: item for item in items}
        
        filtered_items = []
        
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('【') or line.startswith('以下是') or line.startswith('以上是'):
                continue
            
            parts = line.split('###')
            if len(parts) >= 2:
                code = parts[0].strip()
                flag = parts[1].strip()
                
                if flag == '是' and code in item_map:
                    filtered_items.append(item_map[code])
        
        return {'filtered_items': filtered_items}

    def _stage1_quick_filter(self, items: List[Dict]) -> List[Dict]:
        """
        阶段1：LLM快速筛选
        判断审计项是否包含制度要求
        """
        print(f"\n=== 阶段1：快速筛选 ===")
        print(f"输入: {len(items)} 条审计项")
        
        batches = self._split_stage1_batches(items)
        print(f"划分为 {len(batches)} 个批次 (每批{self.stage1_batch_size}条)")
        
        prompts = []
        for i, batch in enumerate(batches, 1):
            prompt = self._build_stage1_prompt(batch, i)
            prompts.append(prompt)
        
        print(f"并行调用LLM处理 {len(prompts)} 个批次...")
        results = self.llm.chat_batch_with_retry(prompts, timeout=120, max_retries=2)
        
        all_filtered = []
        success_count = 0
        failed_batches = []
        
        for i, result in enumerate(results):
            if result.success:
                parsed = self._parse_stage1_response(result.response, batches[i])
                all_filtered.extend(parsed['filtered_items'])
                success_count += 1
            else:
                failed_batches.append(i)
                print(f"  警告: 批次 {i+1} 处理失败: {result.error}")
        
        print(f"阶段1完成: {success_count}/{len(batches)} 批次成功")
        print(f"筛选出 {len(all_filtered)} 条可能包含制度要求的审计项")
        
        if failed_batches:
            print(f"失败批次: {failed_batches}")
        
        return all_filtered

    def _build_stage2_prompt(self, items: List[Dict], batch_num: int) -> str:
        """
        构建阶段2提示词：详细分类
        输入：编码 + 维度 + 标题 + 程序
        输出：编码###类型###置信度
        """
        items_text = []
        for i, item in enumerate(items, 1):
            procedures = ' | '.join(item['procedures'])
            item_text = f"{i}|{item['item_code']}|{item.get('dimension_name', '')}|{item.get('title', '')}|{procedures}"
            items_text.append(item_text)
        
        all_items_text = '\n'.join(items_text)
        
        prompt = f"""你是IT审计专家，分析审计程序并提取制度建设要求。

【审计项】格式:序号|编码|维度|标题|程序
{all_items_text}

【分类标准】
- 建立制度：制定/建立/编制**制度、规定、办法、规程**（常态化管理制度）
- 定期执行：每年/每季度/每月/**定期**开展检查、评估、演练（周期性工作）
- 人员配备：配备/设置/**指定**某岗位/人员（长期人员配置）
- 岗位分离：职责分离/不相容岗位分离（岗位制衡机制）
- 文件保存：保存/**留存**/**归档**文档、记录（档案管理）
- 建立组织：成立/**建立**委员会、小组、部门（组织架构）

【输出格式】每行一条：审计项编码###要求类型###置信度

【要求】
1. 一个审计项可能对应多个要求类型，分别列出
2. 类型只能是：建立制度/定期执行/人员配备/岗位分离/文件保存/建立组织
3. 置信度0-1"""
        return prompt

    def _parse_stage2_response(self, response: str, items: List[Dict]) -> Dict:
        """
        解析阶段2响应
        格式：编码###类型###置信度
        """
        item_map = {item['item_code']: item for item in items}
        
        requirements = []
        
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('【') or line.startswith('以下是') or line.startswith('以上是'):
                continue
            
            parts = line.split('###')
            if len(parts) >= 3:
                code = parts[0].strip()
                req_type = parts[1].strip()
                try:
                    confidence = float(parts[2].strip())
                except ValueError:
                    confidence = 0.5
                
                if req_type not in VALID_REQUIREMENT_TYPES:
                    continue
                
                item = item_map.get(code, {})
                
                requirements.append({
                    'source_item_code': code,
                    'source_item_title': item.get('title', ''),
                    'source_dimension': item.get('dimension_name', ''),
                    'requirement_type': req_type,
                    'confidence': confidence
                })
        
        return {'policy_requirements': requirements}

    def _stage2_detailed_classify(self, items: List[Dict]) -> Dict:
        """
        阶段2：LLM详细分类
        确定具体制度要求类型
        """
        print(f"\n=== 阶段2：详细分类 ===")
        print(f"输入: {len(items)} 条审计项")
        
        if not items:
            return {'policy_requirements': []}
        
        batches = self._split_stage2_batches(items)
        print(f"划分为 {len(batches)} 个批次 (每批{self.stage2_batch_size}条)")
        
        prompts = []
        for i, batch in enumerate(batches, 1):
            prompt = self._build_stage2_prompt(batch, i)
            prompts.append(prompt)
        
        print(f"并行调用LLM处理 {len(prompts)} 个批次...")
        results = self.llm.chat_batch_with_retry(prompts, timeout=120, max_retries=2)
        
        all_requirements = []
        success_count = 0
        failed_batches = []
        
        for i, result in enumerate(results):
            if result.success:
                parsed = self._parse_stage2_response(result.response, batches[i])
                all_requirements.extend(parsed['policy_requirements'])
                success_count += 1
            else:
                failed_batches.append(i)
                print(f"  警告: 批次 {i+1} 处理失败: {result.error}")
        
        print(f"阶段2完成: {success_count}/{len(batches)} 批次成功")
        print(f"提取出 {len(all_requirements)} 条制度要求")
        
        if failed_batches:
            print(f"失败批次: {failed_batches}")
        
        return {'policy_requirements': all_requirements}

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
        执行两阶段提取流程

        Returns:
            总结果文件路径
        """
        print(f"开始提取制度要求（两阶段处理）...")
        print(f"批次号: {self.batch_id}")

        # 1. 读取审计项
        print("\n读取审计项...")
        audit_items = self._load_audit_items()
        print(f"共读取 {len(audit_items)} 条审计项")

        # 2. 阶段1：快速筛选
        filtered_items = self._stage1_quick_filter(audit_items)

        # 3. 阶段2：详细分类
        stage2_result = self._stage2_detailed_classify(filtered_items)

        # 4. 构建最终结果
        type_counts = {
            "建立制度": 0,
            "建立组织": 0,
            "人员配备": 0,
            "定期执行": 0,
            "岗位分离": 0,
            "文件保存": 0
        }

        requirements = stage2_result.get('policy_requirements', [])
        for i, req in enumerate(requirements, 1):
            req['requirement_id'] = f"REQ-{i:03d}"
            req_type = req.get('requirement_type', '')
            if req_type in type_counts:
                type_counts[req_type] += 1

        final_result = {
            "version": "2.0",
            "batch_info": {
                "batch_id": self.batch_id,
                "extract_time": datetime.now().isoformat(),
                "stage1_batch_size": self.stage1_batch_size,
                "stage2_batch_size": self.stage2_batch_size,
                "total_items": len(audit_items),
                "filtered_items": len(filtered_items)
            },
            "summary": {
                "total_requirements_found": len(requirements),
                "by_type": type_counts
            },
            "policy_requirements": requirements
        }

        # 5. 保存结果
        output_path = self._save_results(final_result)
        print(f"\n结果已保存: {output_path}")
        print(f"总计发现 {len(requirements)} 条制度要求")

        return output_path


if __name__ == '__main__':
    # 主程序入口
    db_path = r"e:\mycode\agent-team\tests\test_data\test_it_audit.db"

    # 创建提取器（自动使用环境变量中的LLM配置）
    extractor = PolicyRequirementExtractor(db_path)

    # 执行提取
    result_path = extractor.extract()
    print(f"\n提取完成！结果文件: {result_path}")
