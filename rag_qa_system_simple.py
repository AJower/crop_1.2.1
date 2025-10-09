from typing import List, Dict, Any, Optional
from rag_knowledge_base_simple import SimpleRAGKnowledgeBase
from silican_api import SilicanAPI
from lru_cache import get_api_cache, cache_manager
import json
import hashlib

# 简单的日志函数，避免直接依赖streamlit
def log_error(message):
    print(f"ERROR: {message}")

class SimpleRAGQASystem:
    """简化版RAG问答系统"""
    
    def __init__(self, api_key: str, similarity_method: str = "cosine"):
        self.knowledge_base = SimpleRAGKnowledgeBase(similarity_method=similarity_method)
        self.api = SilicanAPI(api_key)
        
        # 初始化API缓存
        self.api_cache = get_api_cache()
        
        # 根据相似度方法调整阈值
        if similarity_method == "cosine":
            self.similarity_threshold = 0.1  # 余弦相似度阈值
        else:
            self.similarity_threshold = 0.3  # 关键词匹配阈值
    
    def answer_question(self, question: str, use_rag: bool = True) -> Dict[str, Any]:
        """回答用户问题"""
        result = {
            'question': question,
            'answer': '',
            'source': 'general',  # 'knowledge_base' 或 'general'
            'relevant_docs': [],
            'confidence': 0.0
        }
        
        # 检查知识库是否有内容
        kb_status = self.get_knowledge_base_status()
        has_knowledge_base = kb_status['has_index'] and kb_status['stats']['total_documents'] > 0
        
        if not use_rag or not has_knowledge_base:
            # 直接使用通用AI回答（带缓存）
            answer = self._get_cached_api_answer(question)
            result['answer'] = answer
            result['source'] = 'general'
            result['confidence'] = 0.8
            return result
        
        try:
            # 1. 从知识库搜索相关文档
            relevant_docs = self.knowledge_base.search_similar_documents(question, top_k=3)
            
            if not relevant_docs or relevant_docs[0]['similarity_score'] < self.similarity_threshold:
                # 知识库中没有相关内容或相似度太低，使用通用AI（带缓存）
                answer = self._get_cached_api_answer(question)
                result['answer'] = answer
                result['source'] = 'general'
                result['confidence'] = 0.8
                return result
            
            # 2. 检查知识库内容是否与问题相关
            # 提取问题中的关键词
            question_keywords = self.knowledge_base.extract_keywords(question)
            if not question_keywords:
                # 问题中没有农业相关关键词，直接使用通用AI（带缓存）
                answer = self._get_cached_api_answer(question)
                result['answer'] = answer
                result['source'] = 'general'
                result['confidence'] = 0.8
                return result
            
            # 3. 构建RAG提示词
            context_text = self._build_context_from_docs(relevant_docs)
            rag_prompt = self._build_rag_prompt(question, context_text)
            
            # 4. 使用RAG提示词生成回答（带缓存）
            answer = self._get_cached_api_answer(rag_prompt)
            
            # 5. 更新结果
            result['answer'] = answer
            result['source'] = 'knowledge_base'
            result['relevant_docs'] = relevant_docs
            result['confidence'] = relevant_docs[0]['similarity_score']
            
            return result
            
        except Exception as e:
            log_error(f"RAG问答失败: {str(e)}")
            # 回退到通用AI（带缓存）
            answer = self._get_cached_api_answer(question)
            result['answer'] = answer
            result['source'] = 'general'
            result['confidence'] = 0.8
            return result
    
    def _build_context_from_docs(self, docs: List[Dict[str, Any]]) -> str:
        """从相关文档构建上下文"""
        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"文档片段 {i} (相似度: {doc['similarity_score']:.2f}):\n{doc['content']}\n")
        return "\n".join(context_parts)
    
    def _build_rag_prompt(self, question: str, context: str) -> str:
        """构建RAG提示词"""
        return f"""你是一名农业专家，请基于以下知识库内容回答用户的问题。

知识库内容：
{context}

用户问题：{question}

请根据知识库内容提供准确、详细的回答。如果知识库内容不足以回答问题，请基于你的专业知识补充回答，但请明确标注哪些信息来自知识库，哪些是你的专业判断。

回答要求：
1. 优先使用知识库中的信息
2. 回答要详细、实用，适合农民朋友理解
3. 如果知识库信息与你的专业知识有冲突，请以知识库信息为准
4. 如果知识库信息不完整，请补充相关建议
5. 用中文回答"""
    
    def get_knowledge_base_status(self) -> Dict[str, Any]:
        """获取知识库状态"""
        stats = self.knowledge_base.get_knowledge_base_stats()
        return {
            'has_model': True,  # 简化版总是有"模型"
            'has_index': stats['total_documents'] > 0,
            'stats': stats
        }
    
    def upload_document(self, file_content: bytes, filename: str) -> bool:
        """上传文档到知识库"""
        return self.knowledge_base.upload_document(file_content, filename)
    
    def get_document_list(self) -> List[Dict[str, Any]]:
        """获取文档列表"""
        return self.knowledge_base.get_document_list()
    
    def delete_document(self, document_id: int) -> bool:
        """删除文档"""
        return self.knowledge_base.delete_document(document_id)
    
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索文档"""
        return self.knowledge_base.search_similar_documents(query, top_k)
    
    def rebuild_knowledge_base(self):
        """重建知识库索引（简化版无需重建）"""
        print("INFO: 简化版RAG系统无需重建索引")
    
    def _get_cached_api_answer(self, question: str) -> str:
        """获取缓存的API回答"""
        # 生成缓存键
        question_hash = hashlib.md5(question.encode('utf-8')).hexdigest()
        cache_key = f"api_{question_hash}"
        
        # 检查缓存
        cached_answer = self.api_cache.get(cache_key)
        if cached_answer is not None:
            print(f"INFO: API缓存命中: {question[:50]}...")
            return cached_answer
        
        # 调用API
        answer = self.api.agricultural_qa(question)
        
        # 缓存结果
        self.api_cache.put(cache_key, answer)
        print(f"INFO: API回答已缓存: {question[:50]}...")
        
        return answer
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取所有缓存统计信息"""
        kb_cache_stats = self.knowledge_base.get_cache_stats()
        api_cache_stats = self.api_cache.get_stats()
        
        return {
            'knowledge_base': kb_cache_stats,
            'api_cache': api_cache_stats,
            'total_cached_items': kb_cache_stats['total_cached_items'] + api_cache_stats['size'],
            'overall_hit_rate': (kb_cache_stats['overall_hit_rate'] + api_cache_stats['hit_rate']) / 2
        }
    
    def clear_all_cache(self) -> None:
        """清空所有缓存"""
        self.knowledge_base.clear_cache()
        self.api_cache.clear()
        print("INFO: 所有缓存已清空")
    
    def cleanup_expired_cache(self) -> int:
        """清理过期缓存"""
        kb_cleaned = self.knowledge_base.cleanup_expired_cache()
        api_cleaned = self.api_cache.cleanup_expired()
        total_cleaned = kb_cleaned + api_cleaned
        
        if total_cleaned > 0:
            print(f"INFO: 清理了 {total_cleaned} 个过期缓存项")
        
        return total_cleaned

