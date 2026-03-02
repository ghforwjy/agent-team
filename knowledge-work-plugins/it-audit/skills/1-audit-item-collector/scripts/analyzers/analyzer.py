# -*- coding: utf-8 -*-
"""
分析模块

对审计项和审计程序进行统计分析。
"""
from typing import List, Dict, Any, Optional
from collections import defaultdict

from .models import AuditItem, AuditProcedure, AnalysisResult, DimensionStats
from .data_loader import DatabaseLoader


class AuditAnalyzer:
    """审计数据分析器"""

    def __init__(self, loader: DatabaseLoader):
        self.loader = loader

    def analyze(self, dimension: Optional[str] = None) -> AnalysisResult:
        result = AnalysisResult()

        stats = self.loader.get_statistics()
        result.total_items = stats['total_items']
        result.total_procedures = stats['total_procedures']
        result.total_sources = stats['total_sources']
        result.total_dimensions = stats['total_dimensions']

        result.items = self.loader.load_items_with_details(dimension)
        result.procedures = self.loader.load_all_procedures()

        result.dimension_stats = self.loader.load_dimension_stats()

        if result.total_items > 0:
            result.avg_procedures_per_item = result.total_procedures / result.total_items
            result.avg_sources_per_item = result.total_sources / result.total_items

        self._calculate_procedure_distribution(result)

        return result

    def _calculate_procedure_distribution(self, result: AnalysisResult) -> None:
        max_count = 0
        multi_procedure_count = 0

        for item in result.items:
            count = len(item.procedures)
            item.procedure_count = count

            if count > max_count:
                max_count = count

            if count > 1:
                multi_procedure_count += 1

        result.max_procedures_count = max_count
        result.items_with_multiple_procedures = multi_procedure_count

    def get_items_with_multiple_procedures(self, min_count: int = 2) -> List[AuditItem]:
        items = self.loader.load_items_with_details()
        return [item for item in items if len(item.procedures) >= min_count]

    def get_procedure_length_stats(self) -> Dict[str, Any]:
        return self.loader.get_procedure_stats()

    def analyze_by_dimension(self) -> Dict[str, Dict[str, Any]]:
        dimension_stats = self.loader.load_dimension_stats()
        result = {}

        for stat in dimension_stats:
            dim_name = stat.dimension_name
            items = self.loader.load_items_with_details(dimension=dim_name)

            total_procs = sum(len(item.procedures) for item in items)
            avg_procs = total_procs / len(items) if items else 0

            result[dim_name] = {
                'item_count': stat.item_count,
                'procedure_count': stat.procedure_count,
                'avg_procedures_per_item': round(avg_procs, 2),
                'items': items
            }

        return result

    def get_empty_procedures(self) -> List[AuditProcedure]:
        procedures = self.loader.load_all_procedures()
        return [p for p in procedures if not p.procedure_text or not p.procedure_text.strip()]

    def get_long_procedures(self, min_length: int = 500) -> List[AuditProcedure]:
        procedures = self.loader.load_all_procedures()
        return [p for p in procedures if len(p.procedure_text) > min_length]

    def compare_items(self, item1_id: int, item2_id: int) -> Dict[str, Any]:
        items = self.loader.load_items_with_details()

        item1 = next((i for i in items if i.id == item1_id), None)
        item2 = next((i for i in items if i.id == item2_id), None)

        if not item1 or not item2:
            return {'error': '找不到指定的审计项'}

        return {
            'item1': item1.to_dict(),
            'item2': item2.to_dict(),
            'same_dimension': item1.dimension == item2.dimension,
            'procedure_count_diff': len(item1.procedures) - len(item2.procedures),
            'source_count_diff': len(item1.sources) - len(item2.sources)
        }

    def generate_summary_report(self) -> str:
        result = self.analyze()

        lines = [
            "=" * 60,
            "审计项清洗结果分析报告",
            "=" * 60,
            "",
            "【基础统计】",
            f"  审计项总数: {result.total_items}",
            f"  审计程序总数: {result.total_procedures}",
            f"  来源记录总数: {result.total_sources}",
            f"  维度总数: {result.total_dimensions}",
            "",
            "【平均值】",
            f"  平均程序数/项: {result.avg_procedures_per_item:.2f}",
            f"  平均来源数/项: {result.avg_sources_per_item:.2f}",
            "",
            "【程序分布】",
            f"  多程序审计项数: {result.items_with_multiple_procedures}",
            f"  最大程序数: {result.max_procedures_count}",
            "",
            "【维度分布】",
        ]

        for stat in result.dimension_stats:
            lines.append(f"  {stat.dimension_name}: {stat.item_count}项, {stat.procedure_count}程序")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)
