# -*- coding: utf-8 -*-
"""
报告生成模块

生成控制台报告、CSV导出、HTML报告等。
"""
import csv
import json
from typing import List, Optional, TextIO
from pathlib import Path
from datetime import datetime

from .models import AuditItem, AuditProcedure, AnalysisResult
from .analyzer import AuditAnalyzer


class ConsoleReporter:
    """控制台报告生成器"""

    def __init__(self, analyzer: AuditAnalyzer):
        """
        初始化报告器

        Args:
            analyzer: 分析器实例
        """
        self.analyzer = analyzer

    def print_summary(self) -> None:
        """打印摘要报告"""
        report = self.analyzer.generate_summary_report()
        print(report)

    def print_items_table(self, items: Optional[List[AuditItem]] = None, limit: int = 50) -> None:
        """
        打印审计项表格

        Args:
            items: 审计项列表（默认加载所有）
            limit: 最多显示条数
        """
        if items is None:
            items = self.analyzer.loader.load_items_with_details()

        print("\n" + "=" * 100)
        print("审计项列表")
        print("=" * 100)
        print(f"{'ID':<6} {'代码':<12} {'维度':<10} {'程序数':<8} {'来源数':<8} {'标题':<50}")
        print("-" * 100)

        for item in items[:limit]:
            title = item.title[:47] + "..." if len(item.title) > 50 else item.title
            print(f"{item.id:<6} {item.item_code:<12} {item.dimension:<10} "
                  f"{item.procedure_count:<8} {item.source_count:<8} {title}")

        if len(items) > limit:
            print(f"\n... 还有 {len(items) - limit} 条记录 ...")

        print("=" * 100)
        print(f"总计: {len(items)} 条审计项")

    def print_procedures_table(self, procedures: Optional[List[AuditProcedure]] = None,
                               group_by_item: bool = True, limit: int = 50) -> None:
        """
        打印审计程序表格

        Args:
            procedures: 程序列表（默认加载所有）
            group_by_item: 是否按审计项分组显示
            limit: 最多显示条数
        """
        if procedures is None:
            procedures = self.analyzer.loader.load_all_procedures()

        print("\n" + "=" * 100)
        print("审计程序列表")
        print("=" * 100)

        if group_by_item:
            # 按审计项分组
            from collections import defaultdict
            grouped = defaultdict(list)
            for proc in procedures:
                grouped[proc.item_id].append(proc)

            count = 0
            for item_id, procs in sorted(grouped.items()):
                if count >= limit:
                    break

                item_title = procs[0].item_title or f"审计项 #{item_id}"
                print(f"\n【{item_title}】")
                print("-" * 80)

                for i, proc in enumerate(procs, 1):
                    primary_mark = " [主]" if proc.is_primary else ""
                    text = proc.procedure_text[:70] + "..." if len(proc.procedure_text) > 70 else proc.procedure_text
                    print(f"  {i}.{primary_mark} {text}")
                    count += 1
                    if count >= limit:
                        break
        else:
            # 平铺显示
            print(f"{'ID':<6} {'审计项ID':<10} {'主程序':<8} {'内容':<70}")
            print("-" * 100)

            for proc in procedures[:limit]:
                primary = "是" if proc.is_primary else "否"
                text = proc.procedure_text[:67] + "..." if len(proc.procedure_text) > 70 else proc.procedure_text
                print(f"{proc.id:<6} {proc.item_id:<10} {primary:<8} {text}")

        if len(procedures) > limit:
            print(f"\n... 还有 {len(procedures) - limit} 条记录 ...")

        print("=" * 100)
        print(f"总计: {len(procedures)} 条审计程序")

    def print_item_detail(self, item_id: int) -> None:
        """
        打印单个审计项详情

        Args:
            item_id: 审计项ID
        """
        items = self.analyzer.loader.load_items_with_details()
        item = next((i for i in items if i.id == item_id), None)

        if not item:
            print(f"找不到审计项 ID={item_id}")
            return

        print("\n" + "=" * 80)
        print("审计项详情")
        print("=" * 80)
        print(f"ID: {item.id}")
        print(f"代码: {item.item_code}")
        print(f"标题: {item.title}")
        print(f"维度: {item.dimension}")
        print(f"描述: {item.description or '无'}")
        print(f"严重程度: {item.severity}")
        print(f"状态: {item.status}")
        print(f"\n审计程序 ({len(item.procedures)}个):")
        print("-" * 80)

        for i, proc in enumerate(item.procedures, 1):
            primary = " [主程序]" if proc.is_primary else ""
            print(f"\n{i}.{primary}")
            print(f"  {proc.procedure_text}")

        print(f"\n来源记录 ({len(item.sources)}条):")
        print("-" * 80)

        for source in item.sources:
            print(f"  - {source.source_type}: {source.source_file or 'N/A'}")
            if source.raw_title:
                print(f"    原始标题: {source.raw_title}")

        print("=" * 80)


class CsvExporter:
    """CSV导出器"""

    def __init__(self, analyzer: AuditAnalyzer):
        """
        初始化导出器

        Args:
            analyzer: 分析器实例
        """
        self.analyzer = analyzer

    def export_items(self, filepath: str, items: Optional[List[AuditItem]] = None) -> None:
        """
        导出审计项到CSV

        Args:
            filepath: 输出文件路径
            items: 审计项列表（默认加载所有）
        """
        import os
        if items is None:
            items = self.analyzer.loader.load_items_with_details()

        # 确保目录存在
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)

        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', '代码', '标题', '维度', '描述', '严重程度', '状态',
                           '程序数', '来源数'])

            for item in items:
                writer.writerow([
                    item.id,
                    item.item_code,
                    item.title,
                    item.dimension,
                    item.description or '',
                    item.severity,
                    item.status,
                    item.procedure_count,
                    item.source_count
                ])

        print(f"审计项已导出到: {filepath}")

    def export_procedures(self, filepath: str, procedures: Optional[List[AuditProcedure]] = None) -> None:
        """
        导出审计程序到CSV

        Args:
            filepath: 输出文件路径
            procedures: 程序列表（默认加载所有）
        """
        import os
        if procedures is None:
            procedures = self.analyzer.loader.load_all_procedures()

        # 确保目录存在
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)

        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', '审计项ID', '审计项标题', '程序内容', '是否主程序'])

            for proc in procedures:
                writer.writerow([
                    proc.id,
                    proc.item_id,
                    proc.item_title or '',
                    proc.procedure_text,
                    '是' if proc.is_primary else '否'
                ])

        print(f"审计程序已导出到: {filepath}")


class JsonExporter:
    """JSON导出器"""

    def __init__(self, analyzer: AuditAnalyzer):
        """
        初始化导出器

        Args:
            analyzer: 分析器实例
        """
        self.analyzer = analyzer

    def export_analysis(self, filepath: str) -> None:
        """
        导出完整分析结果到JSON

        Args:
            filepath: 输出文件路径
        """
        result = self.analyzer.analyze()

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

        print(f"分析结果已导出到: {filepath}")


class HtmlReporter:
    """HTML报告生成器"""

    def __init__(self, analyzer: AuditAnalyzer):
        """
        初始化报告器

        Args:
            analyzer: 分析器实例
        """
        self.analyzer = analyzer

    def generate_report(self, output_path: str) -> None:
        """
        生成HTML报告

        Args:
            output_path: 输出文件路径
        """
        import os
        result = self.analyzer.analyze()

        # 确保目录存在
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)

        html_content = self._generate_html(result)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"HTML报告已生成: {output_path}")

    def _generate_html(self, result: AnalysisResult) -> str:
        """生成HTML内容 - 显示全部数据，审计项和程序对应展示"""
        
        # 生成维度统计行
        dim_rows = ""
        for stat in result.dimension_stats:
            dim_rows += f"""
            <tr>
                <td>{stat.dimension_name}</td>
                <td>{stat.item_count}</td>
                <td>{stat.procedure_count}</td>
            </tr>
            """
        
        # 准备来源数据用于JavaScript
        sources_data_js = []
        source_id_map = {}  # source_id -> source_info 映射
        for item in result.items:
            item_sources = []
            for source in item.sources:
                # 使用 source_file，如果为空则使用 source_type
                source_name = source.source_file if source.source_file else (source.source_type or '未知来源')
                item_sources.append({
                    'source_file': source_name,
                    'raw_title': source.raw_title or ''
                })
                # 构建 source_id 映射
                source_id_map[source.id] = {'source_file': source_name, 'raw_title': source.raw_title or ''}
            sources_data_js.append({'item_id': item.id, 'sources': item_sources})
        
        # 生成审计项和程序的对应表格 - 全部数据
        item_proc_rows = ""
        for item in result.items:
            # 生成来源角标
            source_badges = ""
            if item.sources:
                source_badges = f'<span class="source-badge" onclick="showSources({item.id})">{len(item.sources)}</span>'
            
            # 审计项基本信息行
            item_proc_rows += f"""
            <tr class="item-header">
                <td rowspan="{max(1, len(item.procedures))}">{item.id}</td>
                <td rowspan="{max(1, len(item.procedures))}">{item.item_code}</td>
                <td rowspan="{max(1, len(item.procedures))}">{item.dimension}</td>
                <td rowspan="{max(1, len(item.procedures))}" class="item-title">{item.title} {source_badges}</td>
            """
            
            if item.procedures:
                # 第一个程序
                proc = item.procedures[0]
                primary_badge = '<span class="badge primary">主</span>' if proc.is_primary else ''
                # 生成程序的来源角标
                proc_source_badge = ""
                if proc.source_id and proc.source_id in source_id_map:
                    proc_source_badge = f'<span class="source-badge" onclick="showProcSource({proc.source_id})">1</span>'
                item_proc_rows += f"""
                <td>{proc.id}</td>
                <td class="procedure-text">{primary_badge} {proc.procedure_text} {proc_source_badge}</td>
            </tr>
                """
                # 后续程序
                for proc in item.procedures[1:]:
                    primary_badge = '<span class="badge primary">主</span>' if proc.is_primary else ''
                    # 生成程序的来源角标
                    proc_source_badge = ""
                    if proc.source_id and proc.source_id in source_id_map:
                        proc_source_badge = f'<span class="source-badge" onclick="showProcSource({proc.source_id})">1</span>'
                    item_proc_rows += f"""
            <tr class="procedure-row">
                <td>{proc.id}</td>
                <td class="procedure-text">{primary_badge} {proc.procedure_text} {proc_source_badge}</td>
            </tr>
                    """
            else:
                item_proc_rows += """
                <td>-</td>
                <td class="no-procedure">无审计程序</td>
            </tr>
                """
        
        # 生成纯审计项列表（全部数据）
        item_rows = ""
        for item in result.items:
            item_rows += f"""
            <tr>
                <td>{item.id}</td>
                <td>{item.item_code}</td>
                <td>{item.dimension}</td>
                <td class="item-title">{item.title}</td>
                <td>{item.procedure_count}</td>
                <td>{item.source_count}</td>
            </tr>
            """
        
        # 生成纯程序列表（全部数据）
        proc_rows = ""
        for proc in result.procedures:
            is_primary = "是" if proc.is_primary else "否"
            proc_rows += f"""
            <tr>
                <td>{proc.id}</td>
                <td>{proc.item_id}</td>
                <td>{proc.item_title or ''}</td>
                <td class="procedure-text">{proc.procedure_text}</td>
                <td>{is_primary}</td>
            </tr>
            """

        # 使用字符串拼接构建HTML，避免f-string与JavaScript大括号冲突
        sources_data_json = json.dumps(sources_data_js, ensure_ascii=False)
        
        html_parts = []
        html_parts.append('<!DOCTYPE html>')
        html_parts.append('<html lang="zh-CN">')
        html_parts.append('<head>')
        html_parts.append('    <meta charset="UTF-8">')
        html_parts.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html_parts.append('    <title>审计项清洗结果分析报告</title>')
        html_parts.append('    <style>')
        html_parts.append('        * { margin: 0; padding: 0; box-sizing: border-box; }')
        html_parts.append('        body {')
        html_parts.append('            font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, \'Helvetica Neue\', Arial, sans-serif;')
        html_parts.append('            line-height: 1.6;')
        html_parts.append('            color: #333;')
        html_parts.append('            background: #f5f5f5;')
        html_parts.append('            padding: 20px;')
        html_parts.append('        }')
        html_parts.append('        .container {')
        html_parts.append('            max-width: 1600px;')
        html_parts.append('            margin: 0 auto;')
        html_parts.append('            background: white;')
        html_parts.append('            padding: 30px;')
        html_parts.append('            border-radius: 8px;')
        html_parts.append('            box-shadow: 0 2px 4px rgba(0,0,0,0.1);')
        html_parts.append('        }')
        html_parts.append('        h1 {')
        html_parts.append('            color: #2c3e50;')
        html_parts.append('            margin-bottom: 30px;')
        html_parts.append('            padding-bottom: 15px;')
        html_parts.append('            border-bottom: 3px solid #3498db;')
        html_parts.append('        }')
        html_parts.append('        h2 {')
        html_parts.append('            color: #34495e;')
        html_parts.append('            margin: 30px 0 15px 0;')
        html_parts.append('            padding-bottom: 10px;')
        html_parts.append('            border-bottom: 2px solid #ecf0f1;')
        html_parts.append('        }')
        html_parts.append('        .stats-grid {')
        html_parts.append('            display: grid;')
        html_parts.append('            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));')
        html_parts.append('            gap: 20px;')
        html_parts.append('            margin-bottom: 30px;')
        html_parts.append('        }')
        html_parts.append('        .stat-card {')
        html_parts.append('            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);')
        html_parts.append('            color: white;')
        html_parts.append('            padding: 20px;')
        html_parts.append('            border-radius: 8px;')
        html_parts.append('            text-align: center;')
        html_parts.append('        }')
        html_parts.append('        .stat-card h3 {')
        html_parts.append('            font-size: 14px;')
        html_parts.append('            font-weight: normal;')
        html_parts.append('            opacity: 0.9;')
        html_parts.append('            margin-bottom: 10px;')
        html_parts.append('        }')
        html_parts.append('        .stat-card .number {')
        html_parts.append('            font-size: 36px;')
        html_parts.append('            font-weight: bold;')
        html_parts.append('        }')
        html_parts.append('        table {')
        html_parts.append('            width: 100%;')
        html_parts.append('            border-collapse: collapse;')
        html_parts.append('            margin: 20px 0;')
        html_parts.append('            font-size: 13px;')
        html_parts.append('        }')
        html_parts.append('        th, td {')
        html_parts.append('            padding: 10px 12px;')
        html_parts.append('            text-align: left;')
        html_parts.append('            border: 1px solid #e0e0e0;')
        html_parts.append('            vertical-align: top;')
        html_parts.append('        }')
        html_parts.append('        th {')
        html_parts.append('            background: #3498db;')
        html_parts.append('            color: white;')
        html_parts.append('            font-weight: 600;')
        html_parts.append('            position: sticky;')
        html_parts.append('            top: 0;')
        html_parts.append('        }')
        html_parts.append('        tr:hover {')
        html_parts.append('            background: #f5f5f5;')
        html_parts.append('        }')
        html_parts.append('        .item-header {')
        html_parts.append('            background: #e8f4f8;')
        html_parts.append('        }')
        html_parts.append('        .item-header:hover {')
        html_parts.append('            background: #d0e8f0;')
        html_parts.append('        }')
        html_parts.append('        .procedure-row {')
        html_parts.append('            background: white;')
        html_parts.append('        }')
        html_parts.append('        .procedure-row:hover {')
        html_parts.append('            background: #fafafa;')
        html_parts.append('        }')
        html_parts.append('        .item-title {')
        html_parts.append('            font-weight: 500;')
        html_parts.append('            color: #2c3e50;')
        html_parts.append('            max-width: 400px;')
        html_parts.append('        }')
        html_parts.append('        .procedure-text {')
        html_parts.append('            color: #555;')
        html_parts.append('            line-height: 1.5;')
        html_parts.append('            max-width: 600px;')
        html_parts.append('        }')
        html_parts.append('        .no-procedure {')
        html_parts.append('            color: #999;')
        html_parts.append('            font-style: italic;')
        html_parts.append('        }')
        html_parts.append('        .badge {')
        html_parts.append('            display: inline-block;')
        html_parts.append('            padding: 2px 6px;')
        html_parts.append('            border-radius: 3px;')
        html_parts.append('            font-size: 11px;')
        html_parts.append('            font-weight: bold;')
        html_parts.append('            margin-right: 5px;')
        html_parts.append('        }')
        html_parts.append('        .badge.primary {')
        html_parts.append('            background: #e74c3c;')
        html_parts.append('            color: white;')
        html_parts.append('        }')
        html_parts.append('        .source-badge {')
        html_parts.append('            display: inline-block;')
        html_parts.append('            background: #e8e8e8;')
        html_parts.append('            color: #52c41a;')
        html_parts.append('            padding: 1px 6px;')
        html_parts.append('            border-radius: 4px;')
        html_parts.append('            font-size: 11px;')
        html_parts.append('            font-weight: bold;')
        html_parts.append('            margin-left: 5px;')
        html_parts.append('            cursor: pointer;')
        html_parts.append('            vertical-align: middle;')
        html_parts.append('        }')
        html_parts.append('        .source-badge:hover {')
        html_parts.append('            background: #d0d0d0;')
        html_parts.append('        }')
        html_parts.append('        .source-popup {')
        html_parts.append('            display: none;')
        html_parts.append('            position: fixed;')
        html_parts.append('            top: 0;')
        html_parts.append('            left: 0;')
        html_parts.append('            width: 100%;')
        html_parts.append('            height: 100%;')
        html_parts.append('            background: rgba(0,0,0,0.5);')
        html_parts.append('            z-index: 1000;')
        html_parts.append('        }')
        html_parts.append('        .source-popup-content {')
        html_parts.append('            position: absolute;')
        html_parts.append('            top: 50%;')
        html_parts.append('            left: 50%;')
        html_parts.append('            transform: translate(-50%, -50%);')
        html_parts.append('            background: white;')
        html_parts.append('            padding: 20px;')
        html_parts.append('            border-radius: 8px;')
        html_parts.append('            max-width: 700px;')
        html_parts.append('            width: 90%;')
        html_parts.append('            max-height: 80vh;')
        html_parts.append('            overflow-y: auto;')
        html_parts.append('        }')
        html_parts.append('        .source-popup h3 {')
        html_parts.append('            margin-bottom: 15px;')
        html_parts.append('            color: #2c3e50;')
        html_parts.append('            border-bottom: 2px solid #3498db;')
        html_parts.append('            padding-bottom: 10px;')
        html_parts.append('        }')
        html_parts.append('        .source-list {')
        html_parts.append('            list-style: none;')
        html_parts.append('            padding: 0;')
        html_parts.append('        }')
        html_parts.append('        .source-item {')
        html_parts.append('            margin-bottom: 15px;')
        html_parts.append('            padding: 12px;')
        html_parts.append('            background: #f8f9fa;')
        html_parts.append('            border-radius: 6px;')
        html_parts.append('            border-left: 4px solid #52c41a;')
        html_parts.append('        }')
        html_parts.append('        .source-item .source-file {')
        html_parts.append('            font-weight: bold;')
        html_parts.append('            color: #333;')
        html_parts.append('            margin-bottom: 8px;')
        html_parts.append('        }')
        html_parts.append('        .source-item .source-text {')
        html_parts.append('            color: #666;')
        html_parts.append('            font-size: 13px;')
        html_parts.append('            line-height: 1.5;')
        html_parts.append('        }')
        html_parts.append('        .source-popup .close-btn {')
        html_parts.append('            margin-top: 20px;')
        html_parts.append('            padding: 8px 20px;')
        html_parts.append('            background: #3498db;')
        html_parts.append('            color: white;')
        html_parts.append('            border: none;')
        html_parts.append('            border-radius: 4px;')
        html_parts.append('            cursor: pointer;')
        html_parts.append('            float: right;')
        html_parts.append('        }')
        html_parts.append('        .source-popup .close-btn:hover {')
        html_parts.append('            background: #2980b9;')
        html_parts.append('        }')
        html_parts.append('        .section {')
        html_parts.append('            margin-bottom: 40px;')
        html_parts.append('        }')
        html_parts.append('        .info {')
        html_parts.append('            background: #e3f2fd;')
        html_parts.append('            border-left: 4px solid #2196f3;')
        html_parts.append('            padding: 15px;')
        html_parts.append('            margin: 20px 0;')
        html_parts.append('        }')
        html_parts.append('        .timestamp {')
        html_parts.append('            color: #7f8c8d;')
        html_parts.append('            font-size: 12px;')
        html_parts.append('            text-align: right;')
        html_parts.append('            margin-top: 30px;')
        html_parts.append('        }')
        html_parts.append('        .scroll-container {')
        html_parts.append('            max-height: 800px;')
        html_parts.append('            overflow-y: auto;')
        html_parts.append('            border: 1px solid #ddd;')
        html_parts.append('            border-radius: 4px;')
        html_parts.append('        }')
        html_parts.append('        .count-badge {')
        html_parts.append('            background: #3498db;')
        html_parts.append('            color: white;')
        html_parts.append('            padding: 2px 8px;')
        html_parts.append('            border-radius: 10px;')
        html_parts.append('            font-size: 12px;')
        html_parts.append('            margin-left: 10px;')
        html_parts.append('        }')
        html_parts.append('    </style>')
        html_parts.append('</head>')
        html_parts.append('<body>')
        html_parts.append('    <div class="container">')
        html_parts.append('        <h1>审计项清洗结果分析报告</h1>')
        html_parts.append('')
        html_parts.append('        <div class="section">')
        html_parts.append('            <h2>基础统计</h2>')
        html_parts.append('            <div class="stats-grid">')
        html_parts.append('                <div class="stat-card">')
        html_parts.append('                    <h3>审计项总数</h3>')
        html_parts.append(f'                    <div class="number">{result.total_items}</div>')
        html_parts.append('                </div>')
        html_parts.append('                <div class="stat-card">')
        html_parts.append('                    <h3>审计程序总数</h3>')
        html_parts.append(f'                    <div class="number">{result.total_procedures}</div>')
        html_parts.append('                </div>')
        html_parts.append('                <div class="stat-card">')
        html_parts.append('                    <h3>来源记录总数</h3>')
        html_parts.append(f'                    <div class="number">{result.total_sources}</div>')
        html_parts.append('                </div>')
        html_parts.append('                <div class="stat-card">')
        html_parts.append('                    <h3>维度总数</h3>')
        html_parts.append(f'                    <div class="number">{result.total_dimensions}</div>')
        html_parts.append('                </div>')
        html_parts.append('            </div>')
        html_parts.append('')
        html_parts.append('            <div class="info">')
        html_parts.append('                <strong>平均值：</strong>')
        html_parts.append(f'                平均程序数/项: {result.avg_procedures_per_item:.2f} |')
        html_parts.append(f'                平均来源数/项: {result.avg_sources_per_item:.2f} |')
        html_parts.append(f'                多程序审计项: {result.items_with_multiple_procedures} |')
        html_parts.append(f'                最大程序数: {result.max_procedures_count}')
        html_parts.append('            </div>')
        html_parts.append('        </div>')
        html_parts.append('')
        html_parts.append('        <div class="section">')
        html_parts.append('            <h2>维度分布</h2>')
        html_parts.append('            <table>')
        html_parts.append('                <thead>')
        html_parts.append('                    <tr>')
        html_parts.append('                        <th>维度名称</th>')
        html_parts.append('                        <th>审计项数</th>')
        html_parts.append('                        <th>审计程序数</th>')
        html_parts.append('                    </tr>')
        html_parts.append('                </thead>')
        html_parts.append('                <tbody>')
        html_parts.append(dim_rows)
        html_parts.append('                </tbody>')
        html_parts.append('            </table>')
        html_parts.append('        </div>')
        html_parts.append('')
        html_parts.append(f'        <div class="section">')
        html_parts.append(f'            <h2>审计项与审计程序对应关系表 <span class="count-badge">共{result.total_items}项</span></h2>')
        html_parts.append('            <div class="scroll-container">')
        html_parts.append('                <table>')
        html_parts.append('                    <thead>')
        html_parts.append('                        <tr>')
        html_parts.append('                            <th style="width: 50px;">项ID</th>')
        html_parts.append('                            <th style="width: 120px;">代码</th>')
        html_parts.append('                            <th style="width: 150px;">维度</th>')
        html_parts.append('                            <th style="width: 350px;">审计项标题</th>')
        html_parts.append('                            <th style="width: 60px;">程序ID</th>')
        html_parts.append('                            <th>审计程序内容</th>')
        html_parts.append('                        </tr>')
        html_parts.append('                    </thead>')
        html_parts.append('                    <tbody>')
        html_parts.append(item_proc_rows)
        html_parts.append('                    </tbody>')
        html_parts.append('                </table>')
        html_parts.append('            </div>')
        html_parts.append('        </div>')
        html_parts.append('')
        html_parts.append(f'        <div class="section">')
        html_parts.append(f'            <h2>审计项列表 <span class="count-badge">共{result.total_items}项</span></h2>')
        html_parts.append('            <div class="scroll-container">')
        html_parts.append('                <table>')
        html_parts.append('                    <thead>')
        html_parts.append('                        <tr>')
        html_parts.append('                            <th>ID</th>')
        html_parts.append('                            <th>代码</th>')
        html_parts.append('                            <th>维度</th>')
        html_parts.append('                            <th>标题</th>')
        html_parts.append('                            <th>程序数</th>')
        html_parts.append('                            <th>来源数</th>')
        html_parts.append('                        </tr>')
        html_parts.append('                    </thead>')
        html_parts.append('                    <tbody>')
        html_parts.append(item_rows)
        html_parts.append('                    </tbody>')
        html_parts.append('                </table>')
        html_parts.append('            </div>')
        html_parts.append('        </div>')
        html_parts.append('')
        html_parts.append(f'        <div class="section">')
        html_parts.append(f'            <h2>审计程序列表 <span class="count-badge">共{result.total_procedures}条</span></h2>')
        html_parts.append('            <div class="scroll-container">')
        html_parts.append('                <table>')
        html_parts.append('                    <thead>')
        html_parts.append('                        <tr>')
        html_parts.append('                            <th>程序ID</th>')
        html_parts.append('                            <th>所属项ID</th>')
        html_parts.append('                            <th>所属审计项</th>')
        html_parts.append('                            <th>程序内容</th>')
        html_parts.append('                            <th>是否主程序</th>')
        html_parts.append('                        </tr>')
        html_parts.append('                    </thead>')
        html_parts.append('                    <tbody>')
        html_parts.append(proc_rows)
        html_parts.append('                    </tbody>')
        html_parts.append('                </table>')
        html_parts.append('            </div>')
        html_parts.append('        </div>')
        html_parts.append('')
        timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        html_parts.append('        <div class="timestamp">')
        html_parts.append(f'            报告生成时间: {timestamp_str}')
        html_parts.append('        </div>')
        html_parts.append('    </div>')
        html_parts.append('')
        html_parts.append('    <!-- 来源详情弹窗 -->')
        html_parts.append('    <div id="sourcePopup" class="source-popup" onclick="closePopup(event)">')
        html_parts.append('        <div class="source-popup-content" onclick="event.stopPropagation()">')
        html_parts.append('            <h3>来源详情</h3>')
        html_parts.append('            <ul id="sourceList" class="source-list"></ul>')
        html_parts.append('            <button class="close-btn" onclick="closePopup()">关闭</button>')
        html_parts.append('        </div>')
        html_parts.append('    </div>')
        html_parts.append('')
        # 转换 source_id_map 为JSON
        source_id_map_json = json.dumps(source_id_map, ensure_ascii=False)
        
        html_parts.append('    <script>')
        html_parts.append('        // 来源数据')
        html_parts.append(f'        const sourcesData = {sources_data_json};')
        html_parts.append(f'        const sourceIdMap = {source_id_map_json};')
        html_parts.append('')
        html_parts.append('        // 显示审计项来源弹窗')
        html_parts.append('        function showSources(itemId) {')
        html_parts.append('            const item = sourcesData.find(function(item) { return item.item_id === itemId; });')
        html_parts.append('            if (!item || !item.sources.length) return;')
        html_parts.append('')
        html_parts.append('            const list = document.getElementById(\'sourceList\');')
        html_parts.append('            list.innerHTML = \'\';')
        html_parts.append('')
        html_parts.append('            item.sources.forEach(function(source, index) {')
        html_parts.append('                const li = document.createElement(\'li\');')
        html_parts.append('                li.className = \'source-item\';')
        html_parts.append('                li.innerHTML = \'<div class="source-file">来源 \' + (index + 1) + \'：\' + source.source_file + \'</div>\' +')
        html_parts.append('                    (source.raw_title ? \'<div class="source-text">\' + source.raw_title + \'</div>\' : \'\');')
        html_parts.append('                list.appendChild(li);')
        html_parts.append('            });')
        html_parts.append('')
        html_parts.append('            document.getElementById(\'sourcePopup\').style.display = \'block\';')
        html_parts.append('        }')
        html_parts.append('')
        html_parts.append('        // 显示审计程序来源弹窗')
        html_parts.append('        function showProcSource(sourceId) {')
        html_parts.append('            const source = sourceIdMap[sourceId];')
        html_parts.append('            if (!source) return;')
        html_parts.append('')
        html_parts.append('            const list = document.getElementById(\'sourceList\');')
        html_parts.append('            list.innerHTML = \'\';')
        html_parts.append('')
        html_parts.append('            const li = document.createElement(\'li\');')
        html_parts.append('            li.className = \'source-item\';')
        html_parts.append('            li.innerHTML = \'<div class="source-file">来源：\' + source.source_file + \'</div>\' +')
        html_parts.append('                (source.raw_title ? \'<div class="source-text">\' + source.raw_title + \'</div>\' : \'\');')
        html_parts.append('            list.appendChild(li);')
        html_parts.append('')
        html_parts.append('            document.getElementById(\'sourcePopup\').style.display = \'block\';')
        html_parts.append('        }')
        html_parts.append('')
        html_parts.append('        // 关闭弹窗')
        html_parts.append('        function closePopup(event) {')
        html_parts.append('            if (!event || event.target.id === \'sourcePopup\') {')
        html_parts.append('                document.getElementById(\'sourcePopup\').style.display = \'none\';')
        html_parts.append('            }')
        html_parts.append('        }')
        html_parts.append('    </script>')
        html_parts.append('</body>')
        html_parts.append('</html>')
        
        return '\n'.join(html_parts)
