# -*- coding: utf-8 -*-
"""
IT审计专家Agent - 清洗流程主程序
负责整合Excel解析、语义匹配、LLM校验、输出JSON建议文档
"""
import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_manager import DatabaseManager
from excel_parser import ExcelParser
from semantic_matcher import SemanticMatcher
from llm_verifier import LLMVerifier


class AuditItemCleaner:
    """审计项清洗器"""
    
    def __init__(self, db_path: str = None, llm_config: Dict = None):
        self.db = DatabaseManager(db_path)
        self.db.init_database()
        self.matcher = SemanticMatcher()
        self.verifier = LLMVerifier(
            api_base=llm_config.get('api_base') if llm_config else None,
            api_key=llm_config.get('api_key') if llm_config else None,
            model=llm_config.get('model') if llm_config else None
        )
        self.import_batch = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    def clean_from_excel(self, file_path: str, output_json: str = None, 
                         skip_llm: bool = False) -> Dict[str, Any]:
        """
        从Excel文件清洗审计项
        
        Args:
            file_path: Excel文件路径
            output_json: 输出JSON文件路径（可选）
            skip_llm: 是否跳过LLM校验
        
        Returns:
            匹配结果JSON
        """
        print(f"\n{'='*60}")
        print(f"开始清洗: {file_path}")
        print(f"导入批次: {self.import_batch}")
        print(f"{'='*60}")
        
        print("\n步骤1: 解析Excel文件...")
        parser = ExcelParser(file_path)
        new_items = parser.parse()
        print(f"解析出 {len(new_items)} 条审计项")
        
        print("\n步骤2: 读取数据库已有审计项...")
        existing_items = self.db.get_all_items_with_procedures()
        print(f"数据库已有 {len(existing_items)} 条审计项")
        
        print("\n步骤3: 向量模型语义匹配...")
        result = self.matcher.batch_match(new_items, existing_items)
        result['source_file'] = os.path.basename(file_path)
        
        if not skip_llm:
            print("\n步骤4: LLM校验...")
            result = self.verifier.iterative_verify(result)
            
            if result.get('verified'):
                print("LLM校验通过!")
            else:
                print("警告: LLM校验未通过，请人工确认")
        else:
            print("\n步骤4: LLM校验 (已跳过)")
        
        if output_json:
            self.matcher.save_result(result, output_json)
        else:
            output_json = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
                    os.path.abspath(__file__))))),
                'data',
                f'clean_result_{self.import_batch}.json'
            )
            self.matcher.save_result(result, output_json)
        
        print(f"\n{'='*60}")
        print("清洗完成!")
        print(f"{'='*60}")
        print(f"统计:")
        print(f"  新审计项: {result['summary']['suggested_new_items']}")
        print(f"  建议合并: {result['summary']['suggested_merge_items']}")
        print(f"  待确认: {result['summary']['pending_review']}")
        if result.get('review'):
            print(f"  LLM审核状态: {result['review'].get('status')}")
        print(f"\n结果已保存: {output_json}")
        
        return result
    
    def apply_result(self, result_json: str, approved: bool = True):
        """
        应用清洗结果到数据库
        
        Args:
            result_json: 清洗结果JSON文件路径
            approved: 是否已审核通过
        """
        with open(result_json, 'r', encoding='utf-8') as f:
            result = json.load(f)
        
        if not approved:
            print("结果未审核通过，不执行入库")
            return
        
        print(f"\n应用清洗结果到数据库...")
        
        for suggestion in result.get('merge_suggestions', []):
            new_item = suggestion['new_item']
            match_result = suggestion['match_result']
            
            if match_result['action'] == 'new_item':
                self._create_new_item(new_item, suggestion)
            elif match_result['action'] == 'merge':
                self._merge_to_existing(new_item, match_result, suggestion)
        
        for pending in result.get('pending_review', []):
            pass
        
        print("入库完成!")
    
    def _create_new_item(self, new_item: Dict, suggestion: Dict):
        dimension_id = self.db.get_or_create_dimension(new_item.get('dimension', '通用'))
        
        item_code = f"NEW-{datetime.now().strftime('%Y%m%d%H%M%S')}-{suggestion['suggestion_id']}"
        
        item_id = self.db.insert_audit_item({
            'item_code': item_code,
            'dimension_id': dimension_id,
            'title': new_item['title'],
            'description': ''
        })
        
        if new_item.get('procedure'):
            self.db.insert_procedure({
                'item_id': item_id,
                'procedure_text': new_item['procedure'],
                'is_primary': 1
            })
        
        self.db.insert_item_source({
            'item_id': item_id,
            'source_type': 'excel',
            'source_file': suggestion.get('source_file', ''),
            'raw_title': new_item['title'],
            'import_batch': self.import_batch
        })
        
        print(f"  新建: {new_item['title'][:40]}...")
    
    def _merge_to_existing(self, new_item: Dict, match_result: Dict, suggestion: Dict):
        existing_id = match_result.get('existing_item_id')
        if not existing_id:
            return
        
        procedure_match = suggestion.get('procedure_match', {})
        if procedure_match.get('action') == 'new_procedure' and new_item.get('procedure'):
            self.db.insert_procedure({
                'item_id': existing_id,
                'procedure_text': new_item['procedure'],
                'is_primary': 0
            })
            print(f"  新增动作到 [{existing_id}]: {new_item['procedure'][:30]}...")
        
        self.db.insert_item_source({
            'item_id': existing_id,
            'source_type': 'excel',
            'source_file': suggestion.get('source_file', ''),
            'raw_title': new_item['title'],
            'import_batch': self.import_batch
        })


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="IT审计项清洗器")
    parser.add_argument("file", nargs="?", help="要清洗的Excel文件路径")
    parser.add_argument("--output", "-o", help="输出JSON文件路径")
    parser.add_argument("--apply", action="store_true", help="应用结果到数据库")
    parser.add_argument("--result", help="要应用的清洗结果JSON文件")
    parser.add_argument("--skip-llm", action="store_true", help="跳过LLM校验")
    
    args = parser.parse_args()
    
    cleaner = AuditItemCleaner()
    
    if args.file:
        result = cleaner.clean_from_excel(args.file, args.output, skip_llm=args.skip_llm)
        
        if args.apply:
            output_path = args.output or f"clean_result_{cleaner.import_batch}.json"
            cleaner.apply_result(output_path, approved=True)
    
    elif args.result and args.apply:
        cleaner.apply_result(args.result, approved=True)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
