# -*- coding: utf-8 -*-
"""
IT审计专家Agent - 审计项收集器
负责从Excel文件收集审计项并导入数据库
"""
import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_manager import DatabaseManager
from excel_parser import ExcelParser


class AuditItemCollector:
    """审计项收集器"""
    
    def __init__(self, db_path: str = None):
        self.db = DatabaseManager(db_path)
        self.db.init_database()
        self.import_batch = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.stats = {
            "total": 0,
            "imported": 0,
            "skipped": 0,
            "errors": 0
        }
    
    def collect_from_excel(self, file_path: str, skip_existing: bool = True) -> Dict[str, Any]:
        print(f"\n开始收集审计项: {file_path}")
        print(f"导入批次: {self.import_batch}")
        print("-" * 60)
        
        parser = ExcelParser(file_path)
        
        structure = parser.analyze_structure()
        print(f"文件结构: {len(structure['sheets'])} 个Sheet, 共 {structure['total_rows']} 行")
        
        items = parser.parse()
        self.stats["total"] = len(items)
        print(f"解析出 {len(items)} 条审计项")
        
        for i, item in enumerate(items, 1):
            try:
                self._import_item(item, parser, i, file_path, skip_existing)
            except Exception as e:
                self.stats["errors"] += 1
                print(f"  [错误] 第{i}条导入失败: {e}")
        
        print("\n" + "=" * 60)
        print("导入完成统计:")
        print(f"  总计: {self.stats['total']}")
        print(f"  已导入: {self.stats['imported']}")
        print(f"  已跳过(重复): {self.stats['skipped']}")
        print(f"  错误: {self.stats['errors']}")
        print("=" * 60)
        
        return self.stats
    
    def _import_item(self, item: Dict, parser: ExcelParser, index: int, 
                     file_path: str, skip_existing: bool):
        title = item.get("title", "")
        
        if skip_existing:
            existing_id = self.db.item_exists(title)
            if existing_id:
                self.stats["skipped"] += 1
                return
        
        dimension_name = item.get("dimension", "通用")
        dimension_id = self.db.get_or_create_dimension(dimension_name)
        
        item_code = parser.generate_item_code(item, index)
        
        audit_item = {
            "item_code": item_code,
            "dimension_id": dimension_id,
            "title": title,
            "audit_procedure": item.get("audit_procedure", ""),
            "description": item.get("description", ""),
            "severity": item.get("severity", "中")
        }
        
        item_id = self.db.insert_audit_item(audit_item)
        
        source = {
            "item_id": item_id,
            "source_type": "excel",
            "source_file": os.path.basename(file_path),
            "source_sheet": item.get("source_sheet", ""),
            "source_row": item.get("source_row", 0),
            "raw_title": title,
            "raw_data": json.dumps(item.get("raw_data", {}), ensure_ascii=False),
            "import_batch": self.import_batch
        }
        self.db.insert_item_source(source)
        
        self.stats["imported"] += 1
        
        if self.stats["imported"] <= 5 or self.stats["imported"] % 50 == 0:
            print(f"  [{self.stats['imported']}] {title[:50]}...")
    
    def get_database_stats(self) -> Dict:
        return self.db.get_statistics()


def main():
    import argparse
    
    arg_parser = argparse.ArgumentParser(description="IT审计项收集器")
    arg_parser.add_argument("file", nargs="?", 
                           default="训练材料/2021年网络安全专自查底稿.xls",
                           help="要导入的Excel文件路径")
    arg_parser.add_argument("--db", help="数据库路径")
    arg_parser.add_argument("--force", action="store_true", 
                           help="强制导入，不跳过重复项")
    
    args = arg_parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"错误: 文件不存在 - {args.file}")
        return
    
    collector = AuditItemCollector(args.db)
    
    collector.collect_from_excel(args.file, skip_existing=not args.force)
    
    stats = collector.get_database_stats()
    print(f"\n数据库统计:")
    print(f"  维度数: {stats['dimensions']}")
    print(f"  审计项总数: {stats['items']}")
    print(f"  来源记录数: {stats['sources']}")
    
    if stats['by_dimension']:
        print(f"\n按维度分布:")
        for dim_name, cnt in stats['by_dimension']:
            print(f"  {dim_name}: {cnt}")


if __name__ == '__main__':
    main()
