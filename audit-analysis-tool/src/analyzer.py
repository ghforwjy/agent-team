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
        """
        初始化分析器

        Args:
            loader: 数据库加载器实例
        """
        self.loader = loader

    def analyze(self, dimension: Optional[str] = None) -> AnalysisResult:
        """
        执行完整分析

        Args:
            dimension: 按维度筛选（可选）

        Returns:
            分析结果对象
        """
        result = AnalysisResult()

        # 加载基础统计数据
        stats = self.loader.get_statistics()
        result.total_items = stats['total_items']
        result.total_procedures = stats['total_procedures']
        result.total_sources = stats['total_sources']
        result.total_dimensions = stats['total_dimensions']

        # 加载详细数据
        result.items = self.loader.load_items_with_details(dimension)
        result.procedures = self.loader.load_all_procedures()

        # 加载维度统计
        result.dimension_stats = self.loader.load_dimension_stats()

        # 计算平均值
        if result.total_items > 0:
            result.avg_procedures_per_item = result.total_procedures / result.total_items
            result.avg_sources_per_item = result.total_sources / result.total_items

        # 计算多程序审计项统计
        self._calculate_procedure_distribution(result)

        return result

    def _calculate_procedure_distribution(self, result: AnalysisResult) -> None:
        """
        计算审计程序分布统计

        Args:
            result: 分析结果对象（会被修改）
        """
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
        """
        获取有多审计程序的审计项

        Args:
            min_count: 最少程序数（默认2）

        Returns:
            符合条件的审计项列表
        """
        items = self.loader.load_items_with_details()
        return [item for item in items if len(item.procedures) >= min_count]

    def get_procedure_length_stats(self) -> Dict[str, Any]:
        """
        获取审计程序长度统计

        Returns:
            长度统计信息
        """
        return self.loader.get_procedure_stats()

    def analyze_by_dimension(self) -> Dict[str, Dict[str, Any]]:
        """
        按维度分析

        Returns:
            各维度的分析结果字典
        """
        dimension_stats = self.loader.load_dimension_stats()
        result = {}

        for stat in dimension_stats:
            dim_name = stat.dimension_name
            items = self.loader.load_items_with_details(dimension=dim_name)

            # 计算该维度的平均程序数
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
        """
        获取空内容的审计程序

        Returns:
            空程序列表
        """
        procedures = self.loader.load_all_procedures()
        return [p for p in procedures if not p.procedure_text or not p.procedure_text.strip()]

    def get_long_procedures(self, min_length: int = 500) -> List[AuditProcedure]:
        """
        获取长内容的审计程序

        Args:
            min_length: 最小长度（默认500字符）

        Returns:
            长程序列表
        """
        procedures = self.loader.load_all_procedures()
        return [p for p in procedures if len(p.procedure_text) > min_length]

    def compare_items(self, item1_id: int, item2_id: int) -> Dict[str, Any]:
        """
        对比两个审计项

        Args:
            item1_id: 第一个审计项ID
            item2_id: 第二个审计项ID

        Returns:
            对比结果
        """
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
        """
        生成文本摘要报告

        Returns:
            报告文本
        """
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
