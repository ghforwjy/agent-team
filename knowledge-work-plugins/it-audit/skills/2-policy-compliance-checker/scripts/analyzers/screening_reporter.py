# -*- coding: utf-8 -*-
"""
制度要求筛选结果报告生成模块
支持从数据库读取筛选结果并生成报告
"""
import json
import csv
import os
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_manager import PolicyDatabaseManager


class ScreeningResultReporter:
    """筛选结果报告生成器"""
    
    def __init__(self, db_path: str):
        if not db_path:
            raise ValueError("数据库路径(db_path)必须传入，不能为空")
        
        self.db_path = db_path
        self.db = PolicyDatabaseManager(db_path)
    
    def generate_summary(self) -> Dict:
        """生成统计摘要"""
        stats = self.db.get_screening_statistics()
        return stats
    
    def print_summary(self) -> None:
        """打印摘要报告到控制台"""
        stats = self.generate_summary()
        
        print("\n" + "=" * 70)
        print("制度要求筛选结果报告")
        print("=" * 70)
        print(f"数据库: {self.db_path}")
        print(f"筛选总数: {stats.get('total', 0)} 条")
        
        print("\n【按状态分布】")
        by_status = stats.get('by_status', {})
        for status, count in by_status.items():
            print(f"  - {status}: {count} 条")
        
        print("\n【按类型分布】")
        by_type = stats.get('by_type', {})
        for req_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
            print(f"  - {req_type}: {count} 条")
        
        print("\n【按置信度分布】")
        by_confidence = stats.get('by_confidence', {})
        high = by_confidence.get('high', 0)
        medium = by_confidence.get('medium', 0)
        low = by_confidence.get('low', 0)
        print(f"  - 高置信度(≥0.70): {high} 条")
        print(f"  - 中置信度(0.45-0.70): {medium} 条")
        print(f"  - 低置信度(<0.45): {low} 条")
        
        print("=" * 70)
    
    def print_detail(self, limit: int = 20) -> None:
        """打印详细结果"""
        results = self.db.get_all_screening_results()
        
        print(f"\n【筛选结果明细】(显示前{min(limit, len(results))}条)")
        print("-" * 70)
        
        for i, r in enumerate(results[:limit]):
            print(f"\n[{i+1}] {r.get('item_code', '')} - {r.get('item_title', '')[:40]}")
            print(f"    类型: {r.get('requirement_type', '')}")
            print(f"    相似度: {r.get('vector_similarity', 0):.4f}")
            print(f"    置信度: {r.get('confidence', 0):.4f}")
            print(f"    状态: {r.get('screening_status', '')}")
            print(f"    维度: {r.get('dimension_name', '')}")
            proc_text = r.get('procedure_text', '')[:100]
            if proc_text:
                print(f"    程序: {proc_text}...")
    
    def export_csv(self, output_path: str) -> None:
        """导出到CSV"""
        results = self.db.get_all_screening_results()
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                'ID', '审计项编码', '审计项标题', '维度', '制度要求类型',
                '向量相似度', '置信度', '置信度级别', '筛选状态', 
                'LLM确认', '程序文本', '批次号', '创建时间'
            ])
            
            for r in results:
                confidence = r.get('confidence', 0)
                if confidence >= 0.7:
                    confidence_level = '高'
                elif confidence >= 0.45:
                    confidence_level = '中'
                else:
                    confidence_level = '低'
                
                writer.writerow([
                    r.get('id', ''),
                    r.get('item_code', ''),
                    r.get('item_title', ''),
                    r.get('dimension_name', ''),
                    r.get('requirement_type', ''),
                    r.get('vector_similarity', 0),
                    r.get('confidence', 0),
                    confidence_level,
                    r.get('screening_status', ''),
                    '是' if r.get('llm_verified') else '否',
                    r.get('procedure_text', ''),
                    r.get('screening_batch', ''),
                    r.get('created_at', '')
                ])
        
        print(f"CSV报告已导出: {output_path}")
    
    def generate_html_report(self, output_path: str) -> None:
        """生成HTML报告"""
        stats = self.generate_summary()
        results = self.db.get_all_screening_results()
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        html_content = self._generate_html(stats, results)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML报告已生成: {output_path}")
    
    def _generate_html(self, stats: Dict, results: List[Dict]) -> str:
        """生成HTML内容"""
        total = stats.get('total', 0)
        by_type = stats.get('by_type', {})
        by_confidence = stats.get('by_confidence', {})
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>制度要求筛选结果报告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #3498db;
        }}
        h2 {{
            color: #34495e;
            margin: 25px 0 15px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
        }}
        .info-bar {{
            background: #e3f2fd;
            padding: 15px 20px;
            border-radius: 6px;
            margin-bottom: 20px;
            display: flex;
            gap: 30px;
            flex-wrap: wrap;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card.total {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        .stat-card.high {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }}
        .stat-card.medium {{
            background: linear-gradient(135deg, #F2994A 0%, #F2C94C 100%);
        }}
        .stat-card h3 {{ font-size: 13px; font-weight: normal; opacity: 0.9; margin-bottom: 8px; }}
        .stat-card .number {{ font-size: 28px; font-weight: bold; }}
        .chart-container {{ max-width: 450px; margin: 20px auto; }}
        .filter-bar {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 15px;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }}
        .filter-bar label {{ font-weight: 500; color: #555; }}
        .filter-bar select {{
            padding: 6px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: white;
        }}
        .scroll-container {{
            max-height: 500px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
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
        tr:hover {{ background: #f5f5f5; }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            color: white;
        }}
        .badge.type-建立制度 {{ background: #3498db; }}
        .badge.type-定期执行 {{ background: #e74c3c; }}
        .badge.type-人员配备 {{ background: #f39c12; }}
        .badge.type-岗位分离 {{ background: #9b59b6; }}
        .badge.type-文件保存 {{ background: #1abc9c; }}
        .badge.type-建立组织 {{ background: #2ecc71; }}
        .confidence {{
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        .confidence.high {{ background: #d4edda; color: #155724; }}
        .confidence.medium {{ background: #fff3cd; color: #856404; }}
        .confidence.low {{ background: #f8d7da; color: #721c24; }}
        .content-cell {{
            max-width: 250px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 12px;
            text-align: right;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>制度要求筛选结果报告</h1>
        
        <div class="info-bar">
            <span>数据库: <strong>{self.db_path}</strong></span>
            <span>筛选总数: <strong>{total}</strong> 条</span>
            <span>报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
        </div>
        
        <div class="section">
            <h2>统计概览</h2>
            <div class="stats-grid">
                <div class="stat-card total">
                    <h3>筛选总数</h3>
                    <div class="number">{total}</div>
                </div>
                <div class="stat-card high">
                    <h3>高置信度</h3>
                    <div class="number">{by_confidence.get('high', 0)}</div>
                </div>
                <div class="stat-card medium">
                    <h3>中置信度</h3>
                    <div class="number">{by_confidence.get('medium', 0)}</div>
                </div>
                <div class="stat-card">
                    <h3>低置信度</h3>
                    <div class="number">{by_confidence.get('low', 0)}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>类型分布</h2>
            <div class="chart-container">
                <canvas id="typeChart"></canvas>
            </div>
        </div>
        
        <div class="section">
            <h2>筛选结果明细</h2>
            <div class="filter-bar">
                <label>类型筛选:</label>
                <select id="typeFilter" onchange="filterResults()">
                    <option value="">全部</option>
                    <option value="建立制度">建立制度</option>
                    <option value="定期执行">定期执行</option>
                    <option value="人员配备">人员配备</option>
                    <option value="岗位分离">岗位分离</option>
                    <option value="文件保存">文件保存</option>
                    <option value="建立组织">建立组织</option>
                </select>
                <label>置信度:</label>
                <select id="confidenceFilter" onchange="filterResults()">
                    <option value="">全部</option>
                    <option value="high">高(≥0.70)</option>
                    <option value="medium">中(0.45-0.70)</option>
                </select>
            </div>
            <div class="scroll-container">
                <table id="resultsTable">
                    <thead>
                        <tr>
                            <th style="width:100px;">编码</th>
                            <th style="width:200px;">标题</th>
                            <th style="width:80px;">类型</th>
                            <th style="width:80px;">维度</th>
                            <th style="width:80px;">相似度</th>
                            <th style="width:80px;">置信度</th>
                            <th style="width:60px;">状态</th>
                            <th>程序文本</th>
                        </tr>
                    </thead>
                    <tbody>
                        {self._generate_result_rows(results)}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="timestamp">
            报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
    
    <script>
        // 类型分布图表
        const ctx = document.getElementById('typeChart').getContext('2d');
        new Chart(ctx, {{
            type: 'pie',
            data: {{
                labels: {json.dumps(list(by_type.keys()), ensure_ascii=False)},
                datasets: [{{
                    data: {json.dumps(list(by_type.values()))},
                    backgroundColor: ['#3498db', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c', '#2ecc71']
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{ legend: {{ position: 'right' }} }}
            }}
        }});
        
        // 筛选功能
        function filterResults() {{
            const typeFilter = document.getElementById('typeFilter').value;
            const confFilter = document.getElementById('confidenceFilter').value;
            const rows = document.querySelectorAll('#resultsTable tbody tr');
            
            rows.forEach(row => {{
                const type = row.getAttribute('data-type');
                const conf = row.getAttribute('data-confidence');
                let show = true;
                if (typeFilter && type !== typeFilter) show = false;
                if (confFilter && conf !== confFilter) show = false;
                row.style.display = show ? '' : 'none';
            }});
        }}
    </script>
</body>
</html>'''
        return html
    
    def _generate_result_rows(self, results: List[Dict]) -> str:
        """生成结果表格行"""
        rows = []
        for r in results:
            confidence = r.get('confidence', 0)
            if confidence >= 0.7:
                conf_level = 'high'
            elif confidence >= 0.45:
                conf_level = 'medium'
            else:
                conf_level = 'low'
            
            req_type = r.get('requirement_type', '')
            type_class = f"type-{req_type}" if req_type else ""
            
            rows.append(f'''
            <tr data-type="{req_type}" data-confidence="{conf_level}">
                <td>{r.get('item_code', '')}</td>
                <td class="content-cell" title="{r.get('item_title', '')}">{r.get('item_title', '')[:30]}</td>
                <td><span class="badge {type_class}">{req_type}</span></td>
                <td>{r.get('dimension_name', '')}</td>
                <td>{r.get('vector_similarity', 0):.4f}</td>
                <td><span class="confidence {conf_level}">{confidence:.4f}</span></td>
                <td>{r.get('screening_status', '')}</td>
                <td class="content-cell" title="{r.get('procedure_text', '')}">{r.get('procedure_text', '')[:50]}...</td>
            </tr>''')
        return '\n'.join(rows)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='筛选结果报告生成器')
    parser.add_argument('--db-path', '-d', required=True, help='数据库路径')
    parser.add_argument('--output', '-o', help='输出目录')
    parser.add_argument('--detail', '-n', type=int, default=20, help='显示详细结果数量')
    
    args = parser.parse_args()
    
    reporter = ScreeningResultReporter(args.db_path)
    
    reporter.print_summary()
    reporter.print_detail(args.detail)
    
    if args.output:
        os.makedirs(args.output, exist_ok=True)
        
        csv_path = os.path.join(args.output, 'screening_results.csv')
        reporter.export_csv(csv_path)
        
        html_path = os.path.join(args.output, 'screening_results.html')
        reporter.generate_html_report(html_path)


if __name__ == '__main__':
    main()
