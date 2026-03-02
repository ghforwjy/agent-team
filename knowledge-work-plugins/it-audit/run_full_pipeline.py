# -*- coding: utf-8 -*-
"""
IT 审计完整流程执行脚本

功能：
1. 模块 1：从 Excel 收集审计项并导入数据库
2. 模块 2：对审计项进行制度要求筛选（向量+LLM 两阶段）
3. 生成完整的分析报告（HTML + CSV）

使用方式：
    # 使用配置文件
    python run_full_pipeline.py --config formal
    
    # 直接指定数据库
    python run_full_pipeline.py --db "path/to/db.db"
"""
import os
import sys
import json
import time
import argparse
from datetime import datetime
from typing import Dict, Any, Optional

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 
    'skills', '1-audit-item-collector', 'scripts'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 
    'skills', '2-policy-compliance-checker', 'scripts'))

from collector import AuditItemCollector
from policy_extractor import PolicyRequirementExtractor
from analyzers.screening_reporter import ScreeningResultReporter


def load_db_config(config_name: str) -> Dict[str, str]:
    """
    加载数据库配置
    
    Args:
        config_name: 配置名称（formal/test/dev）
    
    Returns:
        配置字典
    
    Raises:
        FileNotFoundError: 配置文件不存在
        ValueError: 配置名称不存在
    """
    config_file = os.path.join(os.path.dirname(__file__), 'db_config.json')
    
    if not os.path.exists(config_file):
        # 尝试加载示例配置
        example_file = os.path.join(os.path.dirname(__file__), 'db_config.example.json')
        if os.path.exists(example_file):
            print(f"⚠️  配置文件 db_config.json 不存在，已使用示例配置")
            print(f"   请复制 db_config.example.json 为 db_config.json 并根据需要修改")
            config_file = example_file
        else:
            raise FileNotFoundError(
                f"配置文件不存在：{config_file}\n"
                f"请创建 db_config.json 或 db_config.example.json"
            )
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    if config_name not in config:
        available = ', '.join(config.keys())
        raise ValueError(
            f"配置 '{config_name}' 不存在\n"
            f"可用配置：{available}"
        )
    
    return config[config_name]


def run_module1(excel_file: str, db_path: str) -> Dict[str, Any]:
    """
    运行模块 1：审计项收集
    
    Args:
        excel_file: Excel 文件路径
        db_path: 数据库路径
    
    Returns:
        模块 1 执行结果
    """
    print("\n" + "=" * 70)
    print("模块 1：审计项收集")
    print("=" * 70)
    
    start_time = time.time()
    
    collector = AuditItemCollector(db_path)
    result = collector.collect_from_excel(excel_file, skip_existing=True)
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 70)
    print("模块 1 完成")
    print("=" * 70)
    print(f"✓ 总审计项数：{result.get('total', 0)}")
    print(f"✓ 新增审计项：{result.get('imported', 0)}")
    print(f"✓ 跳过已有：{result.get('skipped', 0)}")
    print(f"✓ 错误：{result.get('errors', 0)}")
    print(f"⏱️  耗时：{elapsed:.2f} 秒")
    
    return {
        'module': '模块 1 - 审计项收集',
        'status': 'success',
        'elapsed': elapsed,
        'total_items': result.get('total', 0),
        'imported': result.get('imported', 0),
        'skipped': result.get('skipped', 0),
        'errors': result.get('errors', 0)
    }


def run_module2(db_path: str, force_full: bool = False, output_dir: str = None) -> Dict[str, Any]:
    """
    运行模块 2：制度要求筛选
    
    Args:
        db_path: 数据库路径
        force_full: 是否强制全量筛选
        output_dir: 输出目录
    
    Returns:
        模块 2 执行结果
    """
    print("\n" + "=" * 70)
    print("模块 2：制度要求筛选（向量+LLM 两阶段）")
    print("=" * 70)
    
    start_time = time.time()
    
    extractor = PolicyRequirementExtractor(
        db_path=db_path,
        force_full=force_full,
        output_dir=output_dir
    )
    
    result = extractor.extract()
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 70)
    print("模块 2 完成")
    print("=" * 70)
    print(f"✓ 总处理：{result.get('total_items', 0)} 条")
    print(f"✓ 高置信度：{result.get('high_confidence', 0)} 条（直接确认）")
    print(f"✓ 中置信度：{result.get('medium_confidence', 0)} 条（LLM 校验）")
    print(f"✓ LLM 校验：{result.get('llm_verified', 0)} 条")
    print(f"✓ LLM 修正：{result.get('llm_adjusted', 0)} 条")
    print(f"✓ 跳过：{result.get('skipped', 0)} 条")
    print(f"⏱️  耗时：{elapsed:.2f} 秒")
    
    return {
        'module': '模块 2 - 制度要求筛选',
        'status': 'success',
        'elapsed': elapsed,
        'total_items': result.get('total_items', 0),
        'high_confidence': result.get('high_confidence', 0),
        'medium_confidence': result.get('medium_confidence', 0),
        'llm_verified': result.get('llm_verified', 0),
        'llm_adjusted': result.get('llm_adjusted', 0),
        'skipped': result.get('skipped', 0)
    }


def generate_reports(db_path: str, output_dir: str) -> Dict[str, str]:
    """
    生成分析报告
    
    Args:
        db_path: 数据库路径
        output_dir: 输出目录
    
    Returns:
        报告生成结果
    """
    print("\n" + "=" * 70)
    print("生成分析报告")
    print("=" * 70)
    
    reporter = ScreeningResultReporter(db_path)
    
    # 打印控制台报告
    reporter.print_summary()
    
    # 生成 HTML 报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = os.path.join(output_dir, f'screening_report_{timestamp}.html')
    reporter.generate_html_report(html_path)
    
    # 生成 CSV 报告
    csv_path = os.path.join(output_dir, f'screening_report_{timestamp}.csv')
    reporter.export_csv(csv_path)
    
    print(f"\n✅ 报告生成完成！")
    print(f"📄 HTML 报告：{html_path}")
    print(f"📊 CSV 报告：{csv_path}")
    
    return {
        'html_report': html_path,
        'csv_report': csv_path
    }


def main():
    parser = argparse.ArgumentParser(
        description='IT 审计完整流程 - 模块 1+ 模块 2',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 使用配置文件（推荐）
  python run_full_pipeline.py --config formal
  python run_full_pipeline.py -c test
  
  # 直接指定数据库
  python run_full_pipeline.py --db "path/to/db.db"
  
  # 包含模块 1（从 Excel 导入）
  python run_full_pipeline.py -c formal -e "docs/audit_items.xlsx"
  
  # 强制全量重新筛选
  python run_full_pipeline.py -c formal --force-full
  
  # 仅显示统计信息
  python run_full_pipeline.py -c formal --stats
        """
    )
    
    # 配置选择（二选一）
    config_group = parser.add_mutually_exclusive_group()
    config_group.add_argument('--config', '-c', 
                             help='使用配置文件中的环境（formal/test/dev）')
    config_group.add_argument('--db', '-d', 
                             help='直接指定数据库路径')
    
    # 可选参数
    parser.add_argument('--excel', '-e', 
                       help='Excel 文件路径（模块 1 输入）')
    parser.add_argument('--output', '-o', 
                       help='输出目录（默认使用配置文件中的值）')
    parser.add_argument('--force-full', '-f', action='store_true', 
                       help='强制全量筛选（默认：增量模式）')
    parser.add_argument('--stats', '-s', action='store_true',
                       help='仅显示统计信息，不执行筛选')
    
    args = parser.parse_args()
    
    # 验证参数
    if not args.config and not args.db:
        parser.error("必须指定 --config 或 --db 其中之一")
    
    # 加载配置
    if args.config:
        print(f"加载配置：{args.config}")
        db_config = load_db_config(args.config)
        db_path = db_config['db_path']
        output_dir = args.output or db_config.get('output_dir', 'output')
        print(f"数据库：{db_path}")
        print(f"输出目录：{output_dir}")
    else:
        db_path = args.db
        output_dir = args.output or 'output'
        print(f"数据库：{db_path}")
        print(f"输出目录：{output_dir}")
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 70)
    print("IT 审计制度要求检查 - 完整流程")
    print("=" * 70)
    print(f"筛选模式：{'强制全量' if args.force_full else '增量筛选'}")
    print("=" * 70)
    
    total_start_time = time.time()
    results = {}
    
    # 仅显示统计信息
    if args.stats:
        reporter = ScreeningResultReporter(db_path)
        reporter.print_summary()
        return
    
    # 运行模块 1（如果有 Excel 文件）
    if args.excel and os.path.exists(args.excel):
        results['module1'] = run_module1(args.excel, db_path)
    else:
        print("\n⚠️  未提供 Excel 文件，跳过模块 1")
    
    # 运行模块 2
    results['module2'] = run_module2(db_path, args.force_full, output_dir)
    
    # 生成报告
    results['reports'] = generate_reports(db_path, output_dir)
    
    # 总耗时
    total_elapsed = time.time() - total_start_time
    
    print("\n" + "=" * 70)
    print("完整流程完成")
    print("=" * 70)
    print(f"⏱️  总耗时：{total_elapsed:.2f} 秒")
    
    # 打印模块统计
    if 'module1' in results:
        m1 = results['module1']
        print(f"\n【模块 1】新增 {m1['imported']} 条审计项")
    
    m2 = results['module2']
    print(f"\n【模块 2】筛选结果:")
    print(f"  - 总处理：{m2['total_items']} 条")
    print(f"  - 高置信度：{m2['high_confidence']} 条")
    print(f"  - LLM 校验：{m2['llm_verified']} 条")
    print(f"  - LLM 修正：{m2['llm_adjusted']} 条")
    
    print("\n✅ 所有流程完成！")
    print(f"📄 报告位置：{results['reports']['html_report']}")


if __name__ == '__main__':
    main()
