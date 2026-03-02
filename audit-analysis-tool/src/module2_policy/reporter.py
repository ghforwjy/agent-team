# -*- coding: utf-8 -*-
"""
制度完备性检查 - 报告生成模块

生成制度要求提取的分析报告，包括控制台报告、CSV导出、HTML报告等。
"""
import json
import csv
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from collections import defaultdict


class ConsoleReporter:
    """控制台报告生成器"""

    def __init__(self, result_file: str):
        """
        初始化报告器

        Args:
            result_file: 制度要求提取结果JSON文件路径
        """
        self.result_file = result_file
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        """加载提取结果数据"""
        with open(self.result_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _get_dimension(self, req: Dict) -> str:
        """获取维度，兼容两种数据格式"""
        # 新格式: source.dimension
        source = req.get('source', {})
        if source:
            return source.get('dimension', '未知维度')
        # 旧格式: source_dimension
        return req.get('source_dimension', '未知维度')

    def _get_item_code(self, req: Dict) -> str:
        """获取审计项编码，兼容两种数据格式"""
        source = req.get('source', {})
        if source:
            return source.get('item_code', '')
        return req.get('source_item_code', '')

    def _get_item_title(self, req: Dict) -> str:
        """获取审计项标题，兼容两种数据格式"""
        source = req.get('source', {})
        if source:
            return source.get('item_title', '')
        return req.get('source_item_title', '')

    def print_summary(self) -> None:
        """打印摘要报告到控制台"""
        batch_info = self.data.get('batch_info', {})
        summary = self.data.get('summary', {})
        requirements = self.data.get('policy_requirements', [])

        # 按类型统计
        by_type = summary.get('by_type', {})

        # 按维度统计
        by_dimension = defaultdict(int)
        for req in requirements:
            dim = self._get_dimension(req)
            by_dimension[dim] += 1

        # 置信度分布
        confidence_high = sum(1 for r in requirements if r.get('confidence', 0) >= 0.8)
        confidence_medium = sum(1 for r in requirements if 0.5 <= r.get('confidence', 0) < 0.8)
        confidence_low = sum(1 for r in requirements if r.get('confidence', 0) < 0.5)

        print("\n" + "=" * 80)
        print("制度要求提取分析报告")
        print("=" * 80)
        print(f"批次号: {batch_info.get('batch_id', '')}")
        print(f"提取时间: {batch_info.get('extract_time', '')}")
        print(f"审计项总数: {batch_info.get('items_processed', 0)}")
        print(f"发现制度要求: {summary.get('total_requirements_found', 0)} 条")
        print("\n按类型分布:")
        for req_type, count in by_type.items():
            if count > 0:
                print(f"  - {req_type}: {count} 条")
        print("\n按维度分布:")
        for dim, count in sorted(by_dimension.items(), key=lambda x: -x[1]):
            print(f"  - {dim}: {count} 条")
        print("\n置信度分布:")
        print(f"  - 高(≥0.8): {confidence_high} 条")
        print(f"  - 中(0.5-0.8): {confidence_medium} 条")
        print(f"  - 低(<0.5): {confidence_low} 条")
        print("=" * 80)


class CsvExporter:
    """CSV导出器"""

    def __init__(self, result_file: str):
        """
        初始化导出器

        Args:
            result_file: 制度要求提取结果JSON文件路径
        """
        self.result_file = result_file
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        """加载提取结果数据"""
        with open(self.result_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _get_dimension(self, req: Dict) -> str:
        """获取维度，兼容两种数据格式"""
        source = req.get('source', {})
        if source:
            return source.get('dimension', '未知维度')
        return req.get('source_dimension', '未知维度')

    def _get_item_code(self, req: Dict) -> str:
        """获取审计项编码，兼容两种数据格式"""
        source = req.get('source', {})
        if source:
            return source.get('item_code', '')
        return req.get('source_item_code', '')

    def _get_item_title(self, req: Dict) -> str:
        """获取审计项标题，兼容两种数据格式"""
        source = req.get('source', {})
        if source:
            return source.get('item_title', '')
        return req.get('source_item_title', '')

    def _get_requirement_detail(self, req: Dict) -> Dict:
        """获取要求详情，兼容两种数据格式"""
        # 新格式: requirement_detail 对象
        detail = req.get('requirement_detail', {})
        if detail:
            return detail
        # 旧格式: 直接在req中的字段
        return {
            'what': req.get('what', ''),
            'scope': req.get('scope', ''),
            'content': req.get('content', ''),
            'frequency': req.get('frequency', ''),
            'quantity': req.get('quantity', ''),
            'qualification': req.get('qualification', ''),
            'retention_period': req.get('retention_period', '')
        }

    def export(self, output_path: str) -> None:
        """
        导出到CSV

        Args:
            output_path: 输出CSV文件路径
        """
        requirements = self.data.get('policy_requirements', [])

        # 确保目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                '要求编号', '批次号', '审计项编码', '审计项标题', '维度',
                '要求类型', '要求内容', '适用范围', '执行频率', '数量要求',
                '资格要求', '保存期限', '关键词', '置信度'
            ])

            for req in requirements:
                detail = self._get_requirement_detail(req)
                writer.writerow([
                    req.get('requirement_id', ''),
                    req.get('batch_id', ''),
                    self._get_item_code(req),
                    self._get_item_title(req),
                    self._get_dimension(req),
                    req.get('requirement_type', ''),
                    detail.get('what', ''),
                    detail.get('scope', ''),
                    detail.get('frequency', ''),
                    detail.get('quantity', ''),
                    detail.get('qualification', ''),
                    detail.get('retention_period', ''),
                    ', '.join(req.get('related_clues', [])),
                    req.get('confidence', 0)
                ])

        print(f"CSV报告已导出: {output_path}")


class HtmlReporter:
    """HTML报告生成器"""

    def __init__(self, result_file: str):
        """
        初始化报告器

        Args:
            result_file: 制度要求提取结果JSON文件路径
        """
        self.result_file = result_file
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        """加载提取结果数据"""
        with open(self.result_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def generate_report(self, output_path: str) -> None:
        """
        生成HTML报告

        Args:
            output_path: 输出HTML文件路径
        """
        # 确保目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        html_content = self._generate_html()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"HTML报告已生成: {output_path}")

    def _generate_html(self) -> str:
        """生成HTML内容"""
        batch_info = self.data.get('batch_info', {})
        summary = self.data.get('summary', {})
        requirements = self.data.get('policy_requirements', [])

        # 按类型统计
        by_type = summary.get('by_type', {})

        # 按维度统计
        by_dimension = defaultdict(int)
        for req in requirements:
            dim = self._get_dimension(req)
            by_dimension[dim] += 1

        # 置信度分布
        confidence_high = sum(1 for r in requirements if r.get('confidence', 0) >= 0.8)
        confidence_medium = sum(1 for r in requirements if 0.5 <= r.get('confidence', 0) < 0.8)
        confidence_low = sum(1 for r in requirements if r.get('confidence', 0) < 0.5)

        # 生成统计卡片
        stats_cards = self._generate_stats_cards(summary.get('total_requirements_found', 0), by_type)

        # 生成类型分布图表数据
        type_chart_data = self._generate_type_chart_data(by_type)

        # 生成维度分布表格
        dimension_rows = self._generate_dimension_rows(by_dimension)

        # 生成制度要求明细表格
        requirement_rows = self._generate_requirement_rows(requirements)

        # 生成HTML
        html_parts = []
        html_parts.append('<!DOCTYPE html>')
        html_parts.append('<html lang="zh-CN">')
        html_parts.append('<head>')
        html_parts.append('    <meta charset="UTF-8">')
        html_parts.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html_parts.append('    <title>制度要求提取分析报告</title>')
        html_parts.append('    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>')
        html_parts.append('    <style>')
        html_parts.append(self._generate_css())
        html_parts.append('    </style>')
        html_parts.append('</head>')
        html_parts.append('<body>')
        html_parts.append('    <div class="container">')
        html_parts.append('        <h1>制度要求提取分析报告</h1>')
        html_parts.append('')
        html_parts.append('        <div class="info-bar">')
        html_parts.append(f'            <span>批次号: <strong>{batch_info.get("batch_id", "")}</strong></span>')
        html_parts.append(f'            <span>提取时间: {batch_info.get("extract_time", "")}</span>')
        html_parts.append(f'            <span>审计项总数: {batch_info.get("items_processed", 0)}</span>')
        html_parts.append('        </div>')
        html_parts.append('')
        html_parts.append('        <div class="section">')
        html_parts.append('            <h2>统计概览</h2>')
        html_parts.append('            <div class="stats-grid">')
        html_parts.append(stats_cards)
        html_parts.append('            </div>')
        html_parts.append('        </div>')
        html_parts.append('')
        html_parts.append('        <div class="section">')
        html_parts.append('            <h2>类型分布</h2>')
        html_parts.append('            <div class="chart-container">')
        html_parts.append('                <canvas id="typeChart"></canvas>')
        html_parts.append('            </div>')
        html_parts.append('        </div>')
        html_parts.append('')
        html_parts.append('        <div class="section">')
        html_parts.append('            <h2>维度分布</h2>')
        html_parts.append('            <table>')
        html_parts.append('                <thead>')
        html_parts.append('                    <tr>')
        html_parts.append('                        <th>维度名称</th>')
        html_parts.append('                        <th>制度要求数</th>')
        html_parts.append('                        <th>占比</th>')
        html_parts.append('                    </tr>')
        html_parts.append('                </thead>')
        html_parts.append('                <tbody>')
        html_parts.append(dimension_rows)
        html_parts.append('                </tbody>')
        html_parts.append('            </table>')
        html_parts.append('        </div>')
        html_parts.append('')
        html_parts.append('        <div class="section">')
        html_parts.append(f'            <h2>制度要求明细 <span class="count-badge">共{len(requirements)}条</span></h2>')
        html_parts.append('            <div class="filter-bar">')
        html_parts.append('                <label>类型筛选:</label>')
        html_parts.append('                <select id="typeFilter" onchange="filterRequirements()">')
        html_parts.append('                    <option value="">全部</option>')
        html_parts.append('                    <option value="建立制度">建立制度</option>')
        html_parts.append('                    <option value="建立组织">建立组织</option>')
        html_parts.append('                    <option value="人员配备">人员配备</option>')
        html_parts.append('                    <option value="定期执行">定期执行</option>')
        html_parts.append('                    <option value="岗位分离">岗位分离</option>')
        html_parts.append('                    <option value="文件保存">文件保存</option>')
        html_parts.append('                </select>')
        html_parts.append('                <label>置信度:</label>')
        html_parts.append('                <select id="confidenceFilter" onchange="filterRequirements()">')
        html_parts.append('                    <option value="">全部</option>')
        html_parts.append('                    <option value="high">高(≥0.8)</option>')
        html_parts.append('                    <option value="medium">中(0.5-0.8)</option>')
        html_parts.append('                    <option value="low">低(<0.5)</option>')
        html_parts.append('                </select>')
        html_parts.append('            </div>')
        html_parts.append('            <div class="scroll-container">')
        html_parts.append('                <table id="requirementsTable">')
        html_parts.append('                    <thead>')
        html_parts.append('                        <tr>')
        html_parts.append('                            <th style="width: 80px;">编号</th>')
        html_parts.append('                            <th style="width: 100px;">类型</th>')
        html_parts.append('                            <th style="width: 200px;">要求内容</th>')
        html_parts.append('                            <th style="width: 150px;">来源审计项</th>')
        html_parts.append('                            <th style="width: 120px;">维度</th>')
        html_parts.append('                            <th style="width: 150px;">关键词</th>')
        html_parts.append('                            <th style="width: 80px;">置信度</th>')
        html_parts.append('                        </tr>')
        html_parts.append('                    </thead>')
        html_parts.append('                    <tbody>')
        html_parts.append(requirement_rows)
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
        html_parts.append('    <script>')
        html_parts.append(type_chart_data)
        html_parts.append(self._generate_filter_js())
        html_parts.append('    </script>')
        html_parts.append('</body>')
        html_parts.append('</html>')

        return '\n'.join(html_parts)

    def _generate_stats_cards(self, total: int, by_type: Dict) -> str:
        """生成统计卡片HTML"""
        cards = []
        cards.append(f'''
            <div class="stat-card total">
                <h3>制度要求总数</h3>
                <div class="number">{total}</div>
            </div>''')

        for req_type, count in by_type.items():
            if count > 0:
                percentage = (count / total * 100) if total > 0 else 0
                cards.append(f'''
            <div class="stat-card">
                <h3>{req_type}</h3>
                <div class="number">{count}</div>
                <div class="percentage">{percentage:.1f}%</div>
            </div>''')

        return '\n'.join(cards)

    def _generate_type_chart_data(self, by_type: Dict) -> str:
        """生成类型分布图表JavaScript"""
        types = []
        counts = []
        for req_type, count in by_type.items():
            if count > 0:
                types.append(req_type)
                counts.append(count)

        types_json = json.dumps(types, ensure_ascii=False)
        counts_json = json.dumps(counts)

        return f'''
        // 类型分布图表
        const ctx = document.getElementById('typeChart').getContext('2d');
        new Chart(ctx, {{
            type: 'pie',
            data: {{
                labels: {types_json},
                datasets: [{{
                    data: {counts_json},
                    backgroundColor: [
                        '#3498db',
                        '#2ecc71',
                        '#f39c12',
                        '#e74c3c',
                        '#9b59b6',
                        '#1abc9c'
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'right'
                    }}
                }}
            }}
        }});
        '''

    def _get_dimension(self, req: Dict) -> str:
        """获取维度，兼容两种数据格式"""
        source = req.get('source', {})
        if source:
            return source.get('dimension', '未知维度')
        return req.get('source_dimension', '未知维度')

    def _get_item_code(self, req: Dict) -> str:
        """获取审计项编码，兼容两种数据格式"""
        source = req.get('source', {})
        if source:
            return source.get('item_code', '')
        return req.get('source_item_code', '')

    def _get_item_title(self, req: Dict) -> str:
        """获取审计项标题，兼容两种数据格式"""
        source = req.get('source', {})
        if source:
            return source.get('item_title', '')
        return req.get('source_item_title', '')

    def _get_requirement_detail(self, req: Dict) -> Dict:
        """获取要求详情，兼容两种数据格式"""
        detail = req.get('requirement_detail', {})
        if detail:
            return detail
        return {
            'what': req.get('what', ''),
            'scope': req.get('scope', ''),
            'content': req.get('content', ''),
            'frequency': req.get('frequency', ''),
            'quantity': req.get('quantity', ''),
            'qualification': req.get('qualification', ''),
            'retention_period': req.get('retention_period', '')
        }

    def _generate_dimension_rows(self, by_dimension: Dict) -> str:
        """生成维度分布表格行"""
        total = sum(by_dimension.values())
        rows = []
        for dim, count in sorted(by_dimension.items(), key=lambda x: -x[1]):
            percentage = (count / total * 100) if total > 0 else 0
            rows.append(f'''
            <tr>
                <td>{dim}</td>
                <td>{count}</td>
                <td>{percentage:.1f}%</td>
            </tr>''')
        return '\n'.join(rows)

    def _generate_requirement_rows(self, requirements: List[Dict]) -> str:
        """生成制度要求明细表格行"""
        rows = []
        for req in requirements:
            detail = self._get_requirement_detail(req)
            confidence = req.get('confidence', 0)

            # 置信度样式
            if confidence >= 0.8:
                confidence_class = 'high'
            elif confidence >= 0.5:
                confidence_class = 'medium'
            else:
                confidence_class = 'low'

            # 关键词标签
            clues = req.get('related_clues', [])
            clues_html = ''.join([f'<span class="tag">{c}</span>' for c in clues[:3]])

            rows.append(f'''
            <tr data-type="{req.get('requirement_type', '')}" data-confidence="{confidence_class}">
                <td>{req.get('requirement_id', '')}</td>
                <td><span class="badge type-{req.get('requirement_type', '').replace(' ', '-')}">{req.get('requirement_type', '')}</span></td>
                <td class="content-cell" title="{detail.get('content', '')}">{detail.get('what', '')}</td>
                <td>{self._get_item_code(req)}</td>
                <td>{self._get_dimension(req)}</td>
                <td>{clues_html}</td>
                <td><span class="confidence {confidence_class}">{confidence:.2f}</span></td>
            </tr>''')
        return '\n'.join(rows)

    def _generate_css(self) -> str:
        """生成CSS样式"""
        return '''
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #3498db;
        }
        h2 {
            color: #34495e;
            margin: 30px 0 15px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
        }
        .info-bar {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            display: flex;
            gap: 30px;
            flex-wrap: wrap;
        }
        .info-bar span {
            color: #555;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-card.total {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            grid-column: span 2;
        }
        .stat-card h3 {
            font-size: 14px;
            font-weight: normal;
            opacity: 0.9;
            margin-bottom: 10px;
        }
        .stat-card .number {
            font-size: 32px;
            font-weight: bold;
        }
        .stat-card .percentage {
            font-size: 12px;
            opacity: 0.8;
            margin-top: 5px;
        }
        .chart-container {
            max-width: 500px;
            margin: 20px auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 13px;
        }
        th, td {
            padding: 10px 12px;
            text-align: left;
            border: 1px solid #e0e0e0;
            vertical-align: top;
        }
        th {
            background: #3498db;
            color: white;
            font-weight: 600;
            position: sticky;
            top: 0;
        }
        tr:hover {
            background: #f5f5f5;
        }
        .filter-bar {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 15px;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }
        .filter-bar label {
            font-weight: 500;
            color: #555;
        }
        .filter-bar select {
            padding: 6px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: white;
        }
        .scroll-container {
            max-height: 600px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }
        .badge.type-建立制度 { background: #3498db; color: white; }
        .badge.type-建立组织 { background: #2ecc71; color: white; }
        .badge.type-人员配备 { background: #f39c12; color: white; }
        .badge.type-定期执行 { background: #e74c3c; color: white; }
        .badge.type-岗位分离 { background: #9b59b6; color: white; }
        .badge.type-文件保存 { background: #1abc9c; color: white; }
        .confidence {
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        .confidence.high { background: #d4edda; color: #155724; }
        .confidence.medium { background: #fff3cd; color: #856404; }
        .confidence.low { background: #f8d7da; color: #721c24; }
        .tag {
            display: inline-block;
            background: #e8e8e8;
            color: #666;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            margin-right: 4px;
        }
        .content-cell {
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .count-badge {
            background: #3498db;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 12px;
            margin-left: 10px;
        }
        .section {
            margin-bottom: 40px;
        }
        .timestamp {
            color: #7f8c8d;
            font-size: 12px;
            text-align: right;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }
        '''

    def _generate_filter_js(self) -> str:
        """生成筛选功能JavaScript"""
        return '''
        // 筛选功能
        function filterRequirements() {
            const typeFilter = document.getElementById('typeFilter').value;
            const confidenceFilter = document.getElementById('confidenceFilter').value;
            const rows = document.querySelectorAll('#requirementsTable tbody tr');

            rows.forEach(row => {
                const type = row.getAttribute('data-type');
                const confidence = row.getAttribute('data-confidence');

                let show = true;

                if (typeFilter && type !== typeFilter) {
                    show = false;
                }

                if (confidenceFilter && confidence !== confidenceFilter) {
                    show = false;
                }

                row.style.display = show ? '' : 'none';
            });
        }
        '''


class PolicyAnalysisDashboard:
    """制度要求分析面板（兼容旧接口）"""

    def __init__(self, result_file: str):
        """
        初始化分析面板

        Args:
            result_file: 制度要求提取结果JSON文件路径
        """
        self.result_file = result_file
        self.console_reporter = ConsoleReporter(result_file)
        self.csv_exporter = CsvExporter(result_file)
        self.html_reporter = HtmlReporter(result_file)

    def print_summary(self) -> None:
        """打印摘要报告到控制台"""
        self.console_reporter.print_summary()

    def export_csv(self, output_path: str) -> None:
        """
        导出到CSV

        Args:
            output_path: 输出CSV文件路径
        """
        self.csv_exporter.export(output_path)

    def generate_html_report(self, output_path: str) -> None:
        """
        生成HTML报告

        Args:
            output_path: 输出HTML文件路径
        """
        self.html_reporter.generate_report(output_path)


if __name__ == '__main__':
    # 测试代码
    import sys

    if len(sys.argv) < 2:
        print("用法: python reporter.py <result_json_file>")
        print("示例: python reporter.py results/policy_req_xxx_all.json")
        sys.exit(1)

    result_file = sys.argv[1]

    # 确保文件存在
    if not Path(result_file).exists():
        print(f"错误: 文件不存在 - {result_file}")
        sys.exit(1)

    # 创建分析面板
    dashboard = PolicyAnalysisDashboard(result_file)

    # 打印摘要
    dashboard.print_summary()

    # 导出CSV
    csv_path = result_file.replace('.json', '.csv')
    dashboard.export_csv(csv_path)

    # 生成HTML报告
    html_path = result_file.replace('.json', '.html')
    dashboard.generate_html_report(html_path)

    print("\n分析完成！")
