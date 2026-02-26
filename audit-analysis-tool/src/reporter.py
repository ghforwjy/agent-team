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
        
        # 生成审计项和程序的对应表格 - 全部数据
        item_proc_rows = ""
        for item in result.items:
            # 审计项基本信息行
            item_proc_rows += f"""
            <tr class="item-header">
                <td rowspan="{max(1, len(item.procedures))}">{item.id}</td>
                <td rowspan="{max(1, len(item.procedures))}">{item.item_code}</td>
                <td rowspan="{max(1, len(item.procedures))}">{item.dimension}</td>
                <td rowspan="{max(1, len(item.procedures))}" class="item-title">{item.title}</td>
            """
            
            if item.procedures:
                # 第一个程序
                proc = item.procedures[0]
                primary_badge = '<span class="badge primary">主</span>' if proc.is_primary else ''
                item_proc_rows += f"""
                <td>{proc.id}</td>
                <td class="procedure-text">{primary_badge} {proc.procedure_text}</td>
            </tr>
                """
                # 后续程序
                for proc in item.procedures[1:]:
                    primary_badge = '<span class="badge primary">主</span>' if proc.is_primary else ''
                    item_proc_rows += f"""
            <tr class="procedure-row">
                <td>{proc.id}</td>
                <td class="procedure-text">{primary_badge} {proc.procedure_text}</td>
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

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>审计项清洗结果分析报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid #3498db;
        }}
        h2 {{
            color: #34495e;
            margin: 30px 0 15px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card h3 {{
            font-size: 14px;
            font-weight: normal;
            opacity: 0.9;
            margin-bottom: 10px;
        }}
        .stat-card .number {{
            font-size: 36px;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 13px;
        }}
        th, td {{
            padding: 10px 12px;
            text-align: left;
            border: 1px solid #e0e0e0;
            vertical-align: top;
        }}
        th {{
            background: #3498db;
            color: white;
            font-weight: 600;
            position: sticky;
            top: 0;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .item-header {{
            background: #e8f4f8;
        }}
        .item-header:hover {{
            background: #d0e8f0;
        }}
        .procedure-row {{
            background: white;
        }}
        .procedure-row:hover {{
            background: #fafafa;
        }}
        .item-title {{
            font-weight: 500;
            color: #2c3e50;
            max-width: 400px;
        }}
        .procedure-text {{
            color: #555;
            line-height: 1.5;
            max-width: 600px;
        }}
        .no-procedure {{
            color: #999;
            font-style: italic;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
            margin-right: 5px;
        }}
        .badge.primary {{
            background: #e74c3c;
            color: white;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .info {{
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin: 20px 0;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 12px;
            text-align: right;
            margin-top: 30px;
        }}
        .scroll-container {{
            max-height: 800px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .count-badge {{
            background: #3498db;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 12px;
            margin-left: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>审计项清洗结果分析报告</h1>

        <div class="section">
            <h2>基础统计</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>审计项总数</h3>
                    <div class="number">{result.total_items}</div>
                </div>
                <div class="stat-card">
                    <h3>审计程序总数</h3>
                    <div class="number">{result.total_procedures}</div>
                </div>
                <div class="stat-card">
                    <h3>来源记录总数</h3>
                    <div class="number">{result.total_sources}</div>
                </div>
                <div class="stat-card">
                    <h3>维度总数</h3>
                    <div class="number">{result.total_dimensions}</div>
                </div>
            </div>

            <div class="info">
                <strong>平均值：</strong>
                平均程序数/项: {result.avg_procedures_per_item:.2f} |
                平均来源数/项: {result.avg_sources_per_item:.2f} |
                多程序审计项: {result.items_with_multiple_procedures} |
                最大程序数: {result.max_procedures_count}
            </div>
        </div>

        <div class="section">
            <h2>维度分布</h2>
            <table>
                <thead>
                    <tr>
                        <th>维度名称</th>
                        <th>审计项数</th>
                        <th>审计程序数</th>
                    </tr>
                </thead>
                <tbody>
                    {dim_rows}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>审计项与审计程序对应关系表 <span class="count-badge">共{result.total_items}项</span></h2>
            <div class="scroll-container">
                <table>
                    <thead>
                        <tr>
                            <th style="width: 50px;">项ID</th>
                            <th style="width: 120px;">代码</th>
                            <th style="width: 150px;">维度</th>
                            <th style="width: 350px;">审计项标题</th>
                            <th style="width: 60px;">程序ID</th>
                            <th>审计程序内容</th>
                        </tr>
                    </thead>
                    <tbody>
                        {item_proc_rows}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="section">
            <h2>审计项列表 <span class="count-badge">共{result.total_items}项</span></h2>
            <div class="scroll-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>代码</th>
                            <th>维度</th>
                            <th>标题</th>
                            <th>程序数</th>
                            <th>来源数</th>
                        </tr>
                    </thead>
                    <tbody>
                        {item_rows}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="section">
            <h2>审计程序列表 <span class="count-badge">共{result.total_procedures}条</span></h2>
            <div class="scroll-container">
                <table>
                    <thead>
                        <tr>
                            <th>程序ID</th>
                            <th>所属项ID</th>
                            <th>所属审计项</th>
                            <th>程序内容</th>
                            <th>是否主程序</th>
                        </tr>
                    </thead>
                    <tbody>
                        {proc_rows}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="timestamp">
            报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>"""
