# -*- coding: utf-8 -*-
"""
制度要求提取器
从审计项中提取制度建设要求 - 向量+LLM 两阶段处理
"""
import os
import json
import sqlite3
import uuid
import argparse
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from vector_screener import PolicyVectorScreener, ScreeningResult
from db_manager import PolicyDatabaseManager, ScreeningRecord
from llm_verifier import PolicyLLMVerifier, VerificationResult


class PolicyRequirementExtractor:
    """制度要求提取器 - 向量+LLM 两阶段"""
    
    def __init__(self, db_path: str, force_full: bool = False, output_dir: str = None):
        if not db_path:
            raise ValueError("数据库路径 (db_path) 必须传入，不能为空")
        
        self.db_path = db_path
        self.force_full = force_full
        self.db = PolicyDatabaseManager(db_path)
        self.screener = PolicyVectorScreener()
        self.verifier = PolicyLLMVerifier()  # LLM 校验器
        self.output_dir = output_dir or os.path.join(os.getcwd(), 'audit-analysis-tool', 'output', 'module2_screening')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _generate_batch_id(self) -> str:
        return self.db.generate_batch_id()
    
    def _load_all_audit_items(self) -> List[Dict]:
        """从数据库加载所有审计项"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
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
    
    def _load_unscreened_items(self) -> List[Dict]:
        """加载未筛选的审计项"""
        if self.force_full:
            print("强制全量筛选模式")
            return self._load_all_audit_items()
        
        screened_ids = self.db.get_screened_item_ids()
        all_items = self._load_all_audit_items()
        unscreened = [item for item in all_items if item['id'] not in screened_ids]
        
        print(f"增量筛选模式：已筛选 {len(screened_ids)} 条，待筛选 {len(unscreened)} 条")
        return unscreened
    
    def _convert_to_records(self, results: List[ScreeningResult], status: str) -> List[ScreeningRecord]:
        """将筛选结果转换为数据库记录"""
        records = []
        for r in results:
            record = ScreeningRecord(
                item_id=r.item_id,
                item_code=r.item_code,
                vector_similarity=r.similarity,
                screening_status=status,
                requirement_type=r.suggested_type,
                confidence=r.similarity,
                llm_verified=False,
                vector_suggested_type=r.suggested_type,  # 保存向量模型的原始建议
                item_title=r.item_title,
                dimension_name=r.dimension_name,
                procedure_text=r.procedure_text
            )
            records.append(record)
        return records
    
    def extract(self) -> Dict:
        """
        执行提取流程（阶段 1：向量筛选 + 阶段 2：LLM 校验）
        
        Returns:
            提取结果字典
        """
        print("=" * 60)
        print("制度要求提取器 - 向量+LLM 两阶段")
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
        
        high_count = 0
        medium_count = 0
        
        if high_confidence:
            records = self._convert_to_records(high_confidence, 'confirmed')
            high_count = self.db.batch_save_screening_results(records, batch_id)
            print(f"保存 {high_count} 条高置信度记录（直接确认）")
        
        if medium_confidence:
            records = self._convert_to_records(medium_confidence, 'pending')
            medium_count = self.db.batch_save_screening_results(records, batch_id)
            print(f"保存 {medium_count} 条中置信度记录（待 LLM 校验）")
        
        # === 阶段 2：LLM 校验 ===
        llm_verified_count = 0
        llm_adjusted_count = 0
        
        if medium_confidence:
            print("\n=== 阶段 2：LLM 校验向量模型分类 ===")
            stage2_start_time = time.time()
            
            # 准备 LLM 校验数据
            verification_items = []
            for result in medium_confidence:
                verification_items.append({
                    'item_id': result.item_id,
                    'item_code': result.item_code,
                    'item_title': result.item_title,
                    'dimension_name': result.dimension_name,
                    'procedure_text': result.procedure_text,
                    'suggested_type': result.suggested_type,
                    'similarity': result.similarity
                })
            
            # LLM 批量校验
            verification_results = self.verifier.verify_classification(verification_items)
            
            # 根据 LLM 结果更新状态
            for ver_result in verification_results:
                # 找到对应的向量筛选结果
                vector_result = next(
                    r for r in medium_confidence 
                    if r.item_id == ver_result.item_id
                )
                
                if ver_result.vector_suggestion_correct:
                    # 向量模型正确，确认
                    vector_result.suggested_type = ver_result.corrected_type or vector_result.suggested_type
                    confirmed = True
                else:
                    # 向量模型错误，修正类型
                    vector_result.suggested_type = ver_result.corrected_type
                    confirmed = False
                
                # 更新数据库记录
                record = ScreeningRecord(
                    item_id=vector_result.item_id,
                    item_code=vector_result.item_code,
                    vector_similarity=vector_result.similarity,
                    screening_status='confirmed',
                    requirement_type=vector_result.suggested_type,
                    confidence=vector_result.similarity,
                    llm_verified=True,
                    item_title=vector_result.item_title,
                    dimension_name=vector_result.dimension_name,
                    procedure_text=vector_result.procedure_text
                )
                self.db.update_screening_result(record)
                
                llm_verified_count += 1
                if not confirmed:
                    llm_adjusted_count += 1
            
            stage2_elapsed = time.time() - stage2_start_time
            print(f"阶段 2 总耗时：{stage2_elapsed:.2f} 秒")
        
        result = {
            'status': 'success',
            'batch_id': batch_id,
            'total_items': len(items),
            'high_confidence': len(high_confidence),
            'medium_confidence': len(medium_confidence),
            'skipped': skipped,
            'saved_high': high_count,
            'saved_medium': medium_count,
            'llm_verified': llm_verified_count,
            'llm_adjusted': llm_adjusted_count
        }
        
        result_path = self._save_result(result)
        result['result_path'] = result_path
        
        print(f"\n结果已保存：{result_path}")
        
        return result
    
    def _save_result(self, result: Dict) -> str:
        """保存结果到 JSON 文件"""
        filename = f"screening_{result['batch_id']}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def get_statistics(self) -> Dict:
        """获取筛选统计信息"""
        return self.db.get_screening_statistics()
    
    def get_all_results(self) -> List[Dict]:
        """获取所有筛选结果"""
        return self.db.get_all_screening_results()


def main():
    parser = argparse.ArgumentParser(description='制度要求提取器')
    parser.add_argument('--db-path', '-d', required=True, help='数据库路径')
    parser.add_argument('--force-full', '-f', action='store_true', help='强制全量筛选')
    parser.add_argument('--output', '-o', help='输出目录')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')
    
    args = parser.parse_args()
    
    extractor = PolicyRequirementExtractor(
        db_path=args.db_path,
        force_full=args.force_full,
        output_dir=args.output
    )
    
    if args.stats:
        stats = extractor.get_statistics()
        print("\n筛选统计信息:")
        print(f"  总数：{stats.get('total', 0)}")
        print(f"  按状态：{stats.get('by_status', {})}")
        print(f"  按类型：{stats.get('by_type', {})}")
        print(f"  按置信度：{stats.get('by_confidence', {})}")
        return
    
    result = extractor.extract()
    
    print("\n" + "=" * 60)
    print("提取完成!")
    print("=" * 60)
    print(f"批次号：{result.get('batch_id')}")
    print(f"总处理：{result.get('total_items', 0)} 条")
    print(f"高置信度：{result.get('high_confidence', 0)} 条")
    print(f"中置信度：{result.get('medium_confidence', 0)} 条")
    print(f"LLM 校验：{result.get('llm_verified', 0)} 条")
    print(f"LLM 修正：{result.get('llm_adjusted', 0)} 条")
    print(f"跳过：{result.get('skipped', 0)} 条")


if __name__ == '__main__':
    main()
