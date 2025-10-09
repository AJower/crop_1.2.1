import sqlite3
import os
import json
import hashlib
import math
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import Counter
from lru_cache import get_vector_cache, get_search_cache, cache_manager

# 尝试导入numpy，如果失败则使用替代方案
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    # 简单的numpy替代
    class SimpleArray:
        def __init__(self, data):
            self.data = data
        def __getitem__(self, key):
            return self.data[key]
        def __len__(self):
            return len(self.data)
    
    def array(data):
        return SimpleArray(data)
    
    np = type('numpy', (), {'array': array})()

# 简单的日志函数，避免直接依赖streamlit
def log_info(message):
    print(f"INFO: {message}")

def log_warning(message):
    print(f"WARNING: {message}")

def log_error(message):
    print(f"ERROR: {message}")

def log_success(message):
    print(f"SUCCESS: {message}")

class SimpleRAGKnowledgeBase:
    """简化版RAG知识库管理类（不依赖重型库）"""
    
    def __init__(self, db_path: str = "crop_health.db", similarity_method: str = "cosine"):
        self.db_path = db_path
        self.documents = []
        self.similarity_method = similarity_method  # "keyword" 或 "cosine"
        
        # 初始化LRU缓存
        self.vector_cache = get_vector_cache()
        self.search_cache = get_search_cache()
        
        self.init_database()
    
    def init_database(self):
        """初始化知识库相关数据库表"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 创建知识库文档表
        c.execute('''CREATE TABLE IF NOT EXISTS knowledge_documents
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      filename TEXT,
                      content TEXT,
                      file_type TEXT,
                      file_size INTEGER,
                      upload_time DATETIME,
                      file_hash TEXT UNIQUE,
                      processed BOOLEAN DEFAULT FALSE)''')
        
        # 创建文档片段表
        c.execute('''CREATE TABLE IF NOT EXISTS document_chunks
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      document_id INTEGER,
                      chunk_index INTEGER,
                      content TEXT,
                      keywords TEXT,
                      FOREIGN KEY (document_id) REFERENCES knowledge_documents (id))''')
        
        conn.commit()
        conn.close()
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """计算文件内容的哈希值"""
        return hashlib.md5(file_content).hexdigest()
    
    def extract_text_from_file(self, file_content: bytes, filename: str) -> str:
        """从文件中提取文本内容（简化版）"""
        file_ext = os.path.splitext(filename)[1].lower()
        
        try:
            if file_ext == '.txt':
                return file_content.decode('utf-8')
            else:
                # 对于其他格式，暂时只处理文本内容
                return file_content.decode('utf-8', errors='ignore')
        except Exception as e:
            log_error(f"文件解析失败 {filename}: {str(e)}")
            return ""
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """将文本分割成块"""
        if not text.strip():
            return []
        
        # 按句子分割
        sentences = text.replace('\n', ' ').split('。')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 如果添加这个句子会超过chunk_size，则保存当前块
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # 保留重叠部分
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + " " + sentence + "。"
            else:
                current_chunk += sentence + "。"
        
        # 添加最后一个块
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def extract_keywords(self, text: str) -> str:
        """提取关键词（简化版）"""
        # 简单的关键词提取，基于常见农业词汇
        keywords = []
        text_lower = text.lower()
        
        # 农业相关关键词
        agricultural_keywords = [
            '水稻', '玉米', '小麦', '大豆', '蔬菜', '水果', '种植', '栽培', '施肥', '浇水',
            '病虫害', '防治', '农药', '收获', '播种', '育苗', '田间', '管理', '土壤',
            '温度', '湿度', '光照', '肥料', '有机肥', '氮肥', '磷肥', '钾肥'
        ]
        
        for keyword in agricultural_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        return ','.join(keywords)
    
    def preprocess_text(self, text: str) -> List[str]:
        """文本预处理，提取词汇"""
        # 转换为小写
        text = text.lower()
        
        # 移除标点符号，保留中文字符、英文字母和数字
        text = re.sub(r'[^\u4e00-\u9fff\w\s]', ' ', text)
        
        # 分割成词汇（中文按字符，英文按单词）
        words = []
        for char in text:
            if '\u4e00' <= char <= '\u9fff':  # 中文字符
                words.append(char)
            elif char.isalnum():  # 英文字母和数字
                words.append(char)
        
        # 过滤空字符串和单字符
        words = [word for word in words if len(word) > 1 or '\u4e00' <= word <= '\u9fff']
        
        return words
    
    def text_to_vector(self, text: str) -> Dict[str, float]:
        """将文本转换为词频向量（带LRU缓存）"""
        # 生成缓存键
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        cache_key = f"vector_{text_hash}"
        
        # 检查缓存
        cached_vector = self.vector_cache.get(cache_key)
        if cached_vector is not None:
            log_info(f"向量缓存命中: {text[:50]}...")
            return cached_vector
        
        # 计算向量
        words = self.preprocess_text(text)
        
        # 计算词频
        word_freq = Counter(words)
        
        # 计算TF-IDF权重（简化版）
        total_words = len(words)
        vector = {}
        
        for word, freq in word_freq.items():
            # 简单的TF计算
            tf = freq / total_words if total_words > 0 else 0
            vector[word] = tf
        
        # 缓存结果
        self.vector_cache.put(cache_key, vector)
        log_info(f"向量已缓存: {text[:50]}...")
        
        return vector
    
    def cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """计算两个向量的余弦相似度"""
        if not vec1 or not vec2:
            return 0.0
        
        # 获取所有词汇
        all_words = set(vec1.keys()) | set(vec2.keys())
        
        if not all_words:
            return 0.0
        
        # 计算点积
        dot_product = sum(vec1.get(word, 0) * vec2.get(word, 0) for word in all_words)
        
        # 计算向量的模长
        norm1 = math.sqrt(sum(freq ** 2 for freq in vec1.values()))
        norm2 = math.sqrt(sum(freq ** 2 for freq in vec2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # 计算余弦相似度
        similarity = dot_product / (norm1 * norm2)
        
        return similarity
    
    def calculate_cosine_similarity(self, query: str, content: str) -> float:
        """计算查询和内容的余弦相似度"""
        query_vector = self.text_to_vector(query)
        content_vector = self.text_to_vector(content)
        
        return self.cosine_similarity(query_vector, content_vector)
    
    def upload_document(self, file_content: bytes, filename: str) -> bool:
        """上传文档到知识库"""
        conn = None
        try:
            # 计算文件哈希
            file_hash = self.calculate_file_hash(file_content)
            
            # 检查文件是否已存在
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT id FROM knowledge_documents WHERE file_hash = ?", (file_hash,))
            if c.fetchone():
                log_warning(f"文件 {filename} 已存在，跳过上传")
                conn.close()
                return False
            
            # 提取文本内容
            text_content = self.extract_text_from_file(file_content, filename)
            if not text_content.strip():
                log_error(f"文件 {filename} 内容为空或无法解析")
                conn.close()
                return False
            
            # 保存文档到数据库
            file_size = len(file_content)
            file_type = os.path.splitext(filename)[1].lower()
            
            # 插入文档记录
            c.execute('''INSERT INTO knowledge_documents 
                         (filename, content, file_type, file_size, upload_time, file_hash, processed)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                     (filename, text_content, file_type, file_size, datetime.now(), file_hash, True))
            
            document_id = c.lastrowid
            
            # 分割文本并保存片段
            chunks = self.chunk_text(text_content)
            if not chunks:
                log_error(f"文件 {filename} 无法分割成有效块")
                # 删除已插入的文档记录
                c.execute("DELETE FROM knowledge_documents WHERE id = ?", (document_id,))
                conn.commit()
                conn.close()
                return False
            
            # 保存文档块
            for i, chunk in enumerate(chunks):
                keywords = self.extract_keywords(chunk)
                c.execute('''INSERT INTO document_chunks 
                             (document_id, chunk_index, content, keywords)
                             VALUES (?, ?, ?, ?)''',
                         (document_id, i, chunk, keywords))
            
            conn.commit()
            conn.close()
            
            log_success(f"文档 {filename} 上传成功，分割为 {len(chunks)} 个块")
            return True
            
        except Exception as e:
            log_error(f"上传文档失败: {str(e)}")
            import traceback
            log_error(f"详细错误: {traceback.format_exc()}")
            # 如果出错，尝试回滚
            try:
                if conn:
                    conn.rollback()
                    conn.close()
            except:
                pass
            return False
    
    def search_similar_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索相似文档（支持关键词匹配和余弦相似度，带LRU缓存）"""
        # 生成缓存键
        query_hash = hashlib.md5(f"{query}_{top_k}_{self.similarity_method}".encode('utf-8')).hexdigest()
        cache_key = f"search_{query_hash}"
        
        # 检查缓存
        cached_results = self.search_cache.get(cache_key)
        if cached_results is not None:
            log_info(f"搜索缓存命中: {query[:50]}...")
            return cached_results
        
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            if self.similarity_method == "cosine":
                # 使用余弦相似度算法
                results = self._search_with_cosine_similarity(conn, query, top_k)
            else:
                # 使用传统关键词匹配算法
                results = self._search_with_keyword_matching(conn, query, top_k)
            
            # 缓存结果
            self.search_cache.put(cache_key, results)
            log_info(f"搜索结果已缓存: {query[:50]}...")
            
            return results
            
        except Exception as e:
            log_error(f"搜索失败: {str(e)}")
            return []
    
    def _search_with_cosine_similarity(self, conn, query: str, top_k: int) -> List[Dict[str, Any]]:
        """使用余弦相似度进行搜索"""
        c = conn.cursor()
        
        # 获取所有文档片段
        c.execute('''SELECT dc.document_id, dc.chunk_index, dc.content, dc.keywords,
                            kd.filename
                     FROM document_chunks dc
                     JOIN knowledge_documents kd ON dc.document_id = kd.id''')
        
        all_docs = c.fetchall()
        results = []
        
        # 计算查询向量
        query_vector = self.text_to_vector(query)
        
        for row in all_docs:
            document_id, chunk_index, content, keywords, filename = row
            
            # 计算余弦相似度
            cosine_sim = self.calculate_cosine_similarity(query, content)
            
            # 设置阈值过滤
            if cosine_sim > 0.05:  # 余弦相似度阈值
                results.append({
                    'document_id': document_id,
                    'chunk_index': chunk_index,
                    'content': content,
                    'filename': filename,
                    'similarity_score': cosine_sim,
                    'similarity_method': 'cosine'
                })
        
        # 按相似度排序并返回前top_k个结果
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        conn.close()
        return results[:top_k]
    
    def _search_with_keyword_matching(self, conn, query: str, top_k: int) -> List[Dict[str, Any]]:
        """使用关键词匹配进行搜索（原有算法）"""
        c = conn.cursor()
        
        # 提取查询关键词
        query_keywords = self.extract_keywords(query)
        query_lower = query.lower()
        
        # 基于关键词匹配搜索
        c.execute('''SELECT dc.document_id, dc.chunk_index, dc.content, dc.keywords,
                            kd.filename
                     FROM document_chunks dc
                     JOIN knowledge_documents kd ON dc.document_id = kd.id
                     WHERE dc.keywords LIKE ? OR dc.content LIKE ?
                     ORDER BY 
                         CASE WHEN dc.keywords LIKE ? THEN 1 ELSE 2 END,
                         LENGTH(dc.content) DESC
                     LIMIT ?''',
                 (f'%{query}%', f'%{query}%', f'%{query}%', top_k * 2))  # 获取更多结果用于筛选
        
        results = []
        for row in c.fetchall():
            document_id, chunk_index, content, keywords, filename = row
            
            # 计算改进的相似度分数
            similarity_score = 0.0
            content_lower = content.lower()
            
            # 1. 直接文本匹配（权重最高）
            if query_lower in content_lower:
                # 计算匹配的完整度
                match_ratio = len(query_lower) / len(content_lower)
                similarity_score += 0.6 + match_ratio * 0.2
            
            # 2. 基于关键词重叠计算分数
            query_keywords_list = [kw.strip() for kw in query_keywords.split(',') if kw.strip()]
            content_keywords_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
            
            common_keywords = set(query_keywords_list) & set(content_keywords_list)
            if common_keywords:
                # 关键词匹配度
                keyword_ratio = len(common_keywords) / max(len(query_keywords_list), 1)
                similarity_score += keyword_ratio * 0.3
            
            # 3. 部分匹配加分
            query_words = query_lower.split()
            content_words = content_lower.split()
            matched_words = set(query_words) & set(content_words)
            if matched_words:
                word_ratio = len(matched_words) / len(query_words)
                similarity_score += word_ratio * 0.1
            
            # 4. 长度惩罚（太短的内容可能不够详细）
            if len(content) < 50:
                similarity_score *= 0.8
            
            if similarity_score > 0.1:  # 提高阈值，只返回真正相关的内容
                results.append({
                    'document_id': document_id,
                    'chunk_index': chunk_index,
                    'content': content,
                    'filename': filename,
                    'similarity_score': min(similarity_score, 1.0),
                    'similarity_method': 'keyword'
                })
        
        # 按相似度排序并返回前top_k个结果
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        conn.close()
        return results[:top_k]
    
    def get_document_list(self) -> List[Dict[str, Any]]:
        """获取知识库文档列表"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''SELECT id, filename, file_type, file_size, upload_time, processed
                     FROM knowledge_documents 
                     ORDER BY upload_time DESC''')
        
        results = []
        for row in c.fetchall():
            results.append({
                'id': row[0],
                'filename': row[1],
                'file_type': row[2],
                'file_size': row[3],
                'upload_time': row[4],
                'processed': row[5]
            })
        
        conn.close()
        return results
    
    def delete_document(self, document_id: int) -> bool:
        """删除文档"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # 获取文档信息
            c.execute("SELECT filename FROM knowledge_documents WHERE id = ?", (document_id,))
            result = c.fetchone()
            if not result:
                log_error("文档不存在")
                conn.close()
                return False
            
            filename = result[0]
            
            # 删除文档块
            c.execute("DELETE FROM document_chunks WHERE document_id = ?", (document_id,))
            
            # 删除文档
            c.execute("DELETE FROM knowledge_documents WHERE id = ?", (document_id,))
            
            conn.commit()
            conn.close()
            
            log_success(f"文档 {filename} 已删除")
            return True
            
        except Exception as e:
            log_error(f"删除文档失败: {str(e)}")
            return False
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 文档统计
        c.execute("SELECT COUNT(*) FROM knowledge_documents")
        total_documents = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM document_chunks")
        total_chunks = c.fetchone()[0]
        
        # 文件类型统计
        c.execute("SELECT file_type, COUNT(*) FROM knowledge_documents GROUP BY file_type")
        file_types = dict(c.fetchall())
        
        # 总文件大小
        c.execute("SELECT SUM(file_size) FROM knowledge_documents")
        total_size = c.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_documents': total_documents,
            'total_chunks': total_chunks,
            'file_types': file_types,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'index_vectors': total_chunks  # 简化版使用文档块数量
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        vector_stats = self.vector_cache.get_stats()
        search_stats = self.search_cache.get_stats()
        
        return {
            'vector_cache': vector_stats,
            'search_cache': search_stats,
            'total_cached_items': vector_stats['size'] + search_stats['size'],
            'overall_hit_rate': (vector_stats['hit_rate'] + search_stats['hit_rate']) / 2
        }
    
    def clear_cache(self) -> None:
        """清空所有缓存"""
        self.vector_cache.clear()
        self.search_cache.clear()
        log_info("所有缓存已清空")
    
    def cleanup_expired_cache(self) -> int:
        """清理过期缓存项"""
        vector_cleaned = self.vector_cache.cleanup_expired()
        search_cleaned = self.search_cache.cleanup_expired()
        total_cleaned = vector_cleaned + search_cleaned
        
        if total_cleaned > 0:
            log_info(f"清理了 {total_cleaned} 个过期缓存项")
        
        return total_cleaned

