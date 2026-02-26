#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载Sentence-BERT向量模型（使用代理）
模型: paraphrase-multilingual-MiniLM-L12-v2
用途: IT审计项语义相似度计算
"""

from sentence_transformers import SentenceTransformer
import os

def download_model():
    """下载并缓存模型到本地model目录"""
    
    # 设置代理
    os.environ['HTTP_PROXY'] = 'http