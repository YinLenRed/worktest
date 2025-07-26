import json
import logging
import redis
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
from django.conf import settings
from django.core.cache import cache


logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis缓存服务类 - 面向对象封装
    """
    
    def __init__(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', '127.0.0.1'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=getattr(settings, 'REDIS_DB', 1),
                decode_responses=True
            )
            # 测试连接
            self.redis_client.ping()
            self.available = True
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            self.available = False
    
    def is_available(self) -> bool:
        """检查Redis是否可用"""
        return self.available
    
    def get(self, key: str, default=None) -> Any:
        """
        获取缓存数据
        """
        try:
            if not self.available:
                return default
            
            value = self.redis_client.get(key)
            if value is None:
                return default
            
            # 尝试解析JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"缓存获取失败 {key}: {e}")
            return default
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """
        设置缓存数据
        """
        try:
            if not self.available:
                return False
            
            # 序列化数据
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            if timeout:
                return self.redis_client.setex(key, timeout, value)
            else:
                return self.redis_client.set(key, value)
        except Exception as e:
            logger.error(f"缓存设置失败 {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        删除缓存数据
        """
        try:
            if not self.available:
                return False
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"缓存删除失败 {key}: {e}")
            return False
    
    def incr(self, key: str, amount: int = 1) -> int:
        """
        增加数值
        """
        try:
            if not self.available:
                return 0
            return self.redis_client.incr(key, amount)
        except Exception as e:
            logger.error(f"缓存递增失败 {key}: {e}")
            return 0
    
    def expire(self, key: str, timeout: int) -> bool:
        """
        设置过期时间
        """
        try:
            if not self.available:
                return False
            return self.redis_client.expire(key, timeout)
        except Exception as e:
            logger.error(f"设置过期时间失败 {key}: {e}")
            return False


class ReadingCacheService(CacheService):
    """
    阅读统计专用缓存服务
    """
    
    ARTICLE_STATS_KEY = "article_stats:{article_id}"
    USER_READING_KEY = "user_reading:{article_id}:{user_id}"
    IP_READING_KEY = "ip_reading:{article_id}:{ip}"
    TOTAL_VIEWS_KEY = "total_views:{article_id}"
    UNIQUE_USERS_KEY = "unique_users:{article_id}"
    
    def get_article_stats(self, article_id: int) -> Dict[str, int]:
        """
        获取文章统计数据
        """
        key = self.ARTICLE_STATS_KEY.format(article_id=article_id)
        stats = self.get(key, {
            'total_views': 0,
            'unique_users': 0,
            'unique_ips': 0
        })
        
        # 记录缓存命中率
        self._record_cache_request(key, stats != {})
        
        return stats
    
    def update_article_stats(self, article_id: int, stats: Dict[str, int]) -> bool:
        """
        更新文章统计数据
        """
        key = self.ARTICLE_STATS_KEY.format(article_id=article_id)
        timeout = getattr(settings, 'READING_STATS_CACHE_TTL', 3600)
        return self.set(key, stats, timeout)
    
    def get_user_reading_count(self, article_id: int, user_id: int) -> int:
        """
        获取用户对文章的阅读次数
        """
        key = self.USER_READING_KEY.format(article_id=article_id, user_id=user_id)
        count = self.get(key, 0)
        
        # 记录缓存命中率
        self._record_cache_request(key, count != 0)
        
        return count
    
    def incr_user_reading_count(self, article_id: int, user_id: int) -> int:
        """
        增加用户阅读次数
        """
        key = self.USER_READING_KEY.format(article_id=article_id, user_id=user_id)
        count = self.incr(key)
        
        # 设置过期时间
        if count == 1:
            timeout = getattr(settings, 'READING_STATS_CACHE_TTL', 3600)
            self.expire(key, timeout)
        
        return count
    
    def get_ip_reading_count(self, article_id: int, ip_address: str) -> int:
        """
        获取IP对文章的阅读次数
        """
        key = self.IP_READING_KEY.format(article_id=article_id, ip=ip_address.replace('.', '_'))
        count = self.get(key, 0)
        
        # 记录缓存命中率
        self._record_cache_request(key, count != 0)
        
        return count
    
    def incr_ip_reading_count(self, article_id: int, ip_address: str) -> int:
        """
        增加IP阅读次数
        """
        key = self.IP_READING_KEY.format(article_id=article_id, ip=ip_address.replace('.', '_'))
        count = self.incr(key)
        
        # 设置过期时间
        if count == 1:
            timeout = getattr(settings, 'READING_STATS_CACHE_TTL', 3600)
            self.expire(key, timeout)
        
        return count
    
    def _record_cache_request(self, key: str, is_hit: bool):
        """
        记录缓存请求统计
        """
        try:
            now = datetime.now()
            stats_key = f"cache_stats:{now.date()}:{now.hour}"
            
            # 总请求数
            self.incr(f"{stats_key}:total")
            
            # 命中数
            if is_hit:
                self.incr(f"{stats_key}:hits")
            
            # 设置过期时间（25小时，确保统计完整）
            self.expire(f"{stats_key}:total", 25 * 3600)
            self.expire(f"{stats_key}:hits", 25 * 3600)
            
        except Exception as e:
            logger.error(f"记录缓存统计失败: {e}")


class CacheMonitorService(CacheService):
    """
    缓存监控服务
    """
    
    def get_cache_hit_rate(self, date: str = None, hour: int = None) -> Dict[str, Any]:
        """
        获取缓存命中率统计
        """
        if not date:
            date = datetime.now().date()
        if hour is None:
            hour = datetime.now().hour
        
        stats_key = f"cache_stats:{date}:{hour}"
        
        total_requests = self.get(f"{stats_key}:total", 0)
        cache_hits = self.get(f"{stats_key}:hits", 0)
        
        hit_rate = 0
        if total_requests > 0:
            hit_rate = round((cache_hits / total_requests) * 100, 2)
        
        return {
            'date': str(date),
            'hour': hour,
            'total_requests': total_requests,
            'cache_hits': cache_hits,
            'hit_rate': hit_rate
        }
    
    def get_daily_hit_rate(self, date: str = None) -> Dict[str, Any]:
        """
        获取一天的缓存命中率统计
        """
        if not date:
            date = str(datetime.now().date())
        
        hourly_stats = []
        total_requests = 0
        total_hits = 0
        
        for hour in range(24):
            stats = self.get_cache_hit_rate(date, hour)
            hourly_stats.append(stats)
            total_requests += stats['total_requests']
            total_hits += stats['cache_hits']
        
        daily_hit_rate = 0
        if total_requests > 0:
            daily_hit_rate = round((total_hits / total_requests) * 100, 2)
        
        return {
            'date': date,
            'total_requests': total_requests,
            'total_hits': total_hits,
            'daily_hit_rate': daily_hit_rate,
            'hourly_stats': hourly_stats
        } 