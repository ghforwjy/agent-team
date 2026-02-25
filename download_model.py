#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载Sentence-BERT向量模型
模型: paraphrase-multilingual-MiniLM-L12-v2
用途: IT审计项语义相似度计算
"""

from sentence_transformers import SentenceTransformer
import os

def download_model():
    """下载并缓存模型到本地model目录"""
    
    model_name = 'paraphrase-multilingual-MiniLM-L12-v2'
    cache_dir = './model'
    
    print(f"正在下载模型: {model_name}")
    print(f"缓存目录: {os.path.abspath(cache_dir)}")
    print("=" * 60)
    
    # 下载模型（会自动缓存到指定目录）
    model = SentenceTransformer(model_name, cache_folder=cache_dir)
    
    print("\n✓ 模型下载完成!")
    print(f"模型路径: {cache_dir}")
    
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

if __name__ == '__main__':
    download_model()
