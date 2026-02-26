#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载Sentence-BERT向量模型
模型: paraphrase-multilingual-MiniLM-L12-v2
用途: IT审计项语义相似度计算

下载后请手动将模型文件整理到 model/Sentence-BERT/ 目录：
- model/Sentence-BERT/model.safetensors
- model/Sentence-BERT/config.json
- model/Sentence-BERT/modules.json
- model/Sentence-BERT/sentence_bert_config.json
- model/Sentence-BERT/config_sentence_transformers.json
- model/Sentence-BERT/README.md
"""

from sentence_transformers import SentenceTransformer
import os
import argparse


def download_model(proxy=None, use_mirror=False):
    """下载并缓存模型到本地model目录"""

    # 设置代理环境变量
    if proxy:
        os.environ['HTTP_PROXY'] = proxy
        os.environ['HTTPS_PROXY'] = proxy
        os.environ['http_proxy'] = proxy
        os.environ['https_proxy'] = proxy
        print(f"使用代理: {proxy}")

    # 使用镜像源
    if use_mirror:
        os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
        print("使用镜像源: https://hf-mirror.com")

    model_name = 'paraphrase-multilingual-MiniLM-L12-v2'
    cache_dir = './model'

    print(f"正在下载模型: {model_name}")
    print(f"缓存目录: {os.path.abspath(cache_dir)}")
    print("=" * 60)
    
    print(f"正在下载模型: {model_name}")
    print(f"缓存目录: {os.path.abspath(cache_dir)}")
    print("=" * 60)
    
    try:
        # 下载模型（会自动缓存到指定目录）
        model = SentenceTransformer(model_name, cache_folder=cache_dir)
        
        print("\n✓ 模型下载完成!")
        print(f"模型路径: {cache_dir}")
        print("\n注意：下载的模型在缓存目录中，请手动整理到 model/Sentence-BERT/ 目录")
        print("整理命令示例：")
        print("  1. 创建目录: mkdir model\\Sentence-BERT")
        print("  2. 复制文件: copy model\\models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2\\snapshots\\*\\* model\\Sentence-BERT\\")

        # 测试模型
        print("\n测试模型...")
        test_sentences = [
            "公司是否设置首席信息官岗位",
            "是否设立CIO职位",
            "是否制定网络安全管理制度"
        ]
        
        embeddings = model.encode(test_sentences)
        
        print(f"测试句子数: {len(test_sentences)}")
        print(f"向量维度: {embeddings.shape[1]}")
        
        # 计算相似度
        from sentence_transformers import util
        sim_01 = util.cos_sim(embeddings[0], embeddings[1])
        sim_02 = util.cos_sim(embeddings[0], embeddings[2])
        
        print(f"\n语义相似度测试:")
        print(f"  '首席信息官岗位' vs 'CIO职位': {sim_01[0][0]:.2%}")
        print(f"  '首席信息官岗位' vs '网络安全制度': {sim_02[0][0]:.2%}")
        
        print("\n模型已就绪，可以用于审计项相似度计算!")
        
    except Exception as e:
        print(f"\n✗ 下载失败: {e}")
        print("\n可能的解决方案:")
        print("1. 检查代理是否正常工作")
        print("2. 尝试手动下载模型到 model/ 目录")
        print("3. 使用镜像源: --mirror 参数")
        raise


def main():
    parser = argparse.ArgumentParser(description='下载Sentence-BERT向量模型')
    parser.add_argument('--proxy', '-p', help='代理地址，例如: http://127.0.0.1:1080')
    parser.add_argument('--mirror', '-m', action='store_true', help='使用hf-mirror镜像源')
    
    args = parser.parse_args()
    
    download_model(proxy=args.proxy, use_mirror=args.mirror)


if __name__ == '__main__':
    main()
