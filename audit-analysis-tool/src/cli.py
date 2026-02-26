# -*- coding: utf-8 -*-
"""
命令行界面模块

提供命令行参数解析和主流程控制。
"""
import argparse
import sys
from pathlib import Path
from typing import Optional

from .data_loader import DatabaseLoader
from .analyzer import AuditAnalyzer
from .reporter import ConsoleReporter, CsvExporter, JsonExporter, HtmlReporter


def create_parser() -> argparse.ArgumentParser:
    """创建参数解析器"""
    parser = argparse.ArgumentParser(
        prog='audit-analysis',
        description='审计项清洗结果分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s --db-path data/it_audit.db
  %(prog)s --db-path data/it_audit.db --output report.html
  %(prog)s --db-path data/it_audit.db --export-items items.csv
  %(prog)s --db-path data/it_audit.db --export-procedures procedures.csv
  %(prog)s --db-path data/it_audit.db --show-items --limit 20
  %(prog)s --db-path data/it_audit.db --show-procedures --group-by-item
        """
    )

    parser.add_argument(
        '--db-path',
        type=str,
        required=True,
        help='数据库文件路径（必需）'
    )

    parser.add_argument(
        '--output',
        '-o',
        type=str,
        help='输出HTML报告文件路径'
    )

    parser.add_argument(
        '--export-items',
        type=str,
        metavar='FILE',
        help='导出审计项到CSV文件'
    )

    parser.add_argument(
        '--export-procedures',
        type=str,
        metavar='FILE',
        help='导出审计程序到CSV文件'
    )

    parser.add_argument(
        '--export-json',
        type=str,
        metavar='FILE',
        help='导出完整分析结果到JSON文件'
    )

    parser.add_argument(
        '--show-items',
        action='store_true',
        help='显示审计项列表'
    )

    parser.add_argument(
        '--show-procedures',
        action='store_true',
        help='显示审计程序列表'
    )

    parser.add_argument(
        '--show-detail',
        type=int,
        metavar='ID',
        help='显示指定ID审计项的详细信息'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='列表显示的最大条数（默认50）'
    )

    parser.add_argument(
        '--group-by-item',
        action='store_true',
        help='按审计项分组显示程序'
    )

    parser.add_argument(
        '--dimension',
        type=str,
        help='按维度筛选'
    )

    parser.add_argument(
        '--version',
        '-v',
        action='version',
        version='%(prog)s 1.0.0'
    )

    return parser


def main(args: Optional[list] = None) -> int:
    """
    主入口函数

    Args:
        args: 命令行参数列表（默认使用sys.argv）

    Returns:
        退出码（0表示成功）
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    # 检查数据库文件
    db_path = Path(parsed_args.db_path)
    if not db_path.exists():
        print(f"错误: 数据库文件不存在: {db_path}", file=sys.stderr)
        return 1

    try:
        # 连接数据库
        with DatabaseLoader(str(db_path)) as loader:
            # 创建分析器
            analyzer = AuditAnalyzer(loader)

            # 创建报告器
            console = ConsoleReporter(analyzer)
            csv_exporter = CsvExporter(analyzer)
            json_exporter = JsonExporter(analyzer)
            html_reporter = HtmlReporter(analyzer)

            # 打印摘要报告
            console.print_summary()

            # 处理各种输出选项
            actions = []

            # 显示审计项列表
            if parsed_args.show_items:
                actions.append("显示审计项列表")
                console.print_items_table(limit=parsed_args.limit)

            # 显示审计程序列表
            if parsed_args.show_procedures:
                actions.append("显示审计程序列表")
                console.print_procedures_table(
                    group_by_item=parsed_args.group_by_item,
                    limit=parsed_args.limit
                )

            # 显示审计项详情
            if parsed_args.show_detail:
                actions.append(f"显示审计项 #{parsed_args.show_detail} 详情")
                console.print_item_detail(parsed_args.show_detail)

            # 导出审计项CSV
            if parsed_args.export_items:
                actions.append(f"导出审计项到 {parsed_args.export_items}")
                csv_exporter.export_items(parsed_args.export_items)

            # 导出审计程序CSV
            if parsed_args.export_procedures:
                actions.append(f"导出审计程序到 {parsed_args.export_procedures}")
                csv_exporter.export_procedures(parsed_args.export_procedures)

            # 导出JSON
            if parsed_args.export_json:
                actions.append(f"导出JSON到 {parsed_args.export_json}")
                json_exporter.export_analysis(parsed_args.export_json)

            # 生成HTML报告
            if parsed_args.output:
                actions.append(f"生成HTML报告 {parsed_args.output}")
                html_reporter.generate_report(parsed_args.output)

            # 如果没有指定任何操作，默认显示审计项和程序列表
            if not actions:
                print("\n【默认输出】")
                console.print_items_table(limit=20)
                console.print_procedures_table(group_by_item=True, limit=20)

            return 0

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
