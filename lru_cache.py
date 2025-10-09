#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LRU缓存实现
提供高效的最近最少使用缓存机制
"""

from typing import Any, Optional, Dict
import time
import threading
from collections import OrderedDict


class LRUCache:
    """线程安全的LRU缓存实现"""
    
    def __init__(self, max_size: int = 100, ttl: Optional[float] = None):
        """
        初始化LRU缓存
        
        Args:
            max_size: 最大缓存条目数
            ttl: 缓存过期时间（秒），None表示永不过期
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()
        self.timestamps = {}  # 存储时间戳用于TTL
        self.lock = threading.RLock()  # 可重入锁
        self.hit_count = 0
        self.miss_count = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或已过期则返回None
        """
        with self.lock:
            if key not in self.cache:
                self.miss_count += 1
                return None
            
            # 检查TTL
            if self.ttl is not None:
                if time.time() - self.timestamps[key] > self.ttl:
                    self._remove_key(key)
                    self.miss_count += 1
                    return None
            
            # 移动到末尾（最近使用）
            value = self.cache.pop(key)
            self.cache[key] = value
            self.timestamps[key] = time.time()
            
            self.hit_count += 1
            return value
    
    def put(self, key: str, value: Any) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        with self.lock:
            # 如果键已存在，更新值
            if key in self.cache:
                self.cache.pop(key)
            # 如果缓存已满，删除最久未使用的项
            elif len(self.cache) >= self.max_size:
                self._evict_oldest()
            
            # 添加新项
            self.cache[key] = value
            self.timestamps[key] = time.time()
    
    def _remove_key(self, key: str) -> None:
        """删除指定键"""
        if key in self.cache:
            del self.cache[key]
            del self.timestamps[key]
    
    def _evict_oldest(self) -> None:
        """删除最久未使用的项"""
        if self.cache:
            oldest_key = next(iter(self.cache))
            self._remove_key(oldest_key)
    
    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
            self.hit_count = 0
            self.miss_count = 0
    
    def size(self) -> int:
        """获取当前缓存大小"""
        with self.lock:
            return len(self.cache)
    
    def is_full(self) -> bool:
        """检查缓存是否已满"""
        with self.lock:
            return len(self.cache) >= self.max_size
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self.lock:
            total_requests = self.hit_count + self.miss_count
            hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hit_count': self.hit_count,
                'miss_count': self.miss_count,
                'hit_rate': hit_rate,
                'is_full': self.is_full()
            }
    
    def cleanup_expired(self) -> int:
        """
        清理过期项
        
        Returns:
            清理的项数
        """
        if self.ttl is None:
            return 0
        
        with self.lock:
            current_time = time.time()
            expired_keys = [
                key for key, timestamp in self.timestamps.items()
                if current_time - timestamp > self.ttl
            ]
            
            for key in expired_keys:
                self._remove_key(key)
            
            return len(expired_keys)
    
    def __len__(self) -> int:
        """返回缓存大小"""
        return self.size()
    
    def __contains__(self, key: str) -> bool:
        """检查键是否存在"""
        with self.lock:
            return key in self.cache
    
    def __repr__(self) -> str:
        """字符串表示"""
        stats = self.get_stats()
        return f"LRUCache(size={stats['size']}/{stats['max_size']}, hit_rate={stats['hit_rate']:.2%})"


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.caches = {}
        self.default_config = {
            'max_size': 100,
            'ttl': 3600  # 1小时
        }
    
    def get_cache(self, name: str, **kwargs) -> LRUCache:
        """
        获取或创建缓存实例
        
        Args:
            name: 缓存名称
            **kwargs: 缓存配置参数
            
        Returns:
            LRUCache实例
        """
        if name not in self.caches:
            config = {**self.default_config, **kwargs}
            self.caches[name] = LRUCache(**config)
        
        return self.caches[name]
    
    def clear_all(self) -> None:
        """清空所有缓存"""
        for cache in self.caches.values():
            cache.clear()
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有缓存的统计信息"""
        return {name: cache.get_stats() for name, cache in self.caches.items()}
    
    def cleanup_all(self) -> int:
        """清理所有缓存的过期项"""
        total_cleaned = 0
        for cache in self.caches.values():
            total_cleaned += cache.cleanup_expired()
        return total_cleaned


# 全局缓存管理器实例
cache_manager = CacheManager()


def get_vector_cache() -> LRUCache:
    """获取向量缓存"""
    return cache_manager.get_cache(
        'vector_cache',
        max_size=200,
        ttl=7200  # 2小时
    )


def get_search_cache() -> LRUCache:
    """获取搜索缓存"""
    return cache_manager.get_cache(
        'search_cache',
        max_size=100,
        ttl=1800  # 30分钟
    )


def get_api_cache() -> LRUCache:
    """获取API缓存"""
    return cache_manager.get_cache(
        'api_cache',
        max_size=50,
        ttl=3600  # 1小时
    )


if __name__ == "__main__":
    # 测试LRU缓存
    cache = LRUCache(max_size=3, ttl=5)
    
    # 测试基本功能
    cache.put("key1", "value1")
    cache.put("key2", "value2")
    cache.put("key3", "value3")
    
    print(f"缓存大小: {cache.size()}")
    print(f"key1: {cache.get('key1')}")
    print(f"key2: {cache.get('key2')}")
    
    # 测试LRU淘汰
    cache.put("key4", "value4")  # 应该淘汰key3
    print(f"key3: {cache.get('key3')}")  # 应该返回None
    print(f"key4: {cache.get('key4')}")  # 应该返回value4
    
    # 测试统计信息
    stats = cache.get_stats()
    print(f"缓存统计: {stats}")

