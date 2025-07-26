import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime
from django.db import transaction
from django.contrib.auth.models import User
from django.db.models import F, Sum, Count

from ..models import Article, ReadingStats, CacheHitStats
from .cache_service import ReadingCacheService, CacheMonitorService
from .exceptions import (
    CacheException, DatabaseException, ValidationException, 
    ExceptionHandler, FallbackStrategy, ExceptionLevel
)


logger = logging.getLogger(__name__)


class ReadingStatsService:
    """
    阅读统计服务类 - 实现读写分离和业务逻辑
    """
    
    def __init__(self):
        self.cache_service = ReadingCacheService()
        self.monitor_service = CacheMonitorService()
    
    def record_reading(self, article_id: int, user: User = None, 
                      ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        记录用户阅读 - 主要业务逻辑方法
        """
        try:
            # 参数验证
            if not article_id:
                raise ValidationException("文章ID不能为空")
            
            if not user and not ip_address:
                raise ValidationException("用户或IP地址至少提供一个")
            
            # 检查文章是否存在
            try:
                article = Article.objects.get(id=article_id, is_published=True)
            except Article.DoesNotExist:
                raise ValidationException(f"文章不存在或未发布: {article_id}")
            
            # 更新缓存统计
            cache_updated = self._update_cache_stats(article_id, user, ip_address)
            
            # 异步更新数据库（这里用同步模拟，实际可用Celery）
            db_updated = self._update_database_stats(article_id, user, ip_address, user_agent)
            
            # 获取最新统计数据
            stats = self.get_article_stats(article_id)
            
            return {
                'success': True,
                'article_id': article_id,
                'cache_updated': cache_updated,
                'database_updated': db_updated,
                'stats': stats
            }
            
        except Exception as e:
            error_info = ExceptionHandler.handle_exception(e, f"记录阅读-文章{article_id}")
            return error_info
    
    def get_article_stats(self, article_id: int) -> Dict[str, Any]:
        """
        获取文章统计数据 - 读优先访问缓存
        """
        try:
            # 优先从缓存读取
            if self.cache_service.is_available():
                cache_stats = self.cache_service.get_article_stats(article_id)
                if cache_stats and cache_stats.get('total_views', 0) > 0:
                    return cache_stats
            
            # 缓存未命中，从数据库读取
            db_stats = self._get_database_stats(article_id)
            
            # 更新缓存
            if self.cache_service.is_available() and db_stats:
                self.cache_service.update_article_stats(article_id, db_stats)
            
            return db_stats
            
        except Exception as e:
            error_info = ExceptionHandler.handle_exception(e, f"获取统计-文章{article_id}")
            # 降级处理：返回基础统计数据
            return {
                'total_views': 0,
                'unique_users': 0,
                'unique_ips': 0,
                'error': error_info.get('error_message')
            }
    
    def get_user_reading_stats(self, article_id: int, user_id: int) -> Dict[str, Any]:
        """
        获取用户对特定文章的阅读统计
        """
        try:
            # 优先从缓存获取
            if self.cache_service.is_available():
                cache_count = self.cache_service.get_user_reading_count(article_id, user_id)
                if cache_count > 0:
                    return {
                        'article_id': article_id,
                        'user_id': user_id,
                        'read_count': cache_count,
                        'source': 'cache'
                    }
            
            # 从数据库获取
            try:
                reading_stat = ReadingStats.objects.get(
                    article_id=article_id, 
                    user_id=user_id
                )
                return {
                    'article_id': article_id,
                    'user_id': user_id,
                    'read_count': reading_stat.read_count,
                    'first_read_at': reading_stat.first_read_at.isoformat(),
                    'last_read_at': reading_stat.last_read_at.isoformat(),
                    'source': 'database'
                }
            except ReadingStats.DoesNotExist:
                return {
                    'article_id': article_id,
                    'user_id': user_id,
                    'read_count': 0,
                    'source': 'database'
                }
                
        except Exception as e:
            error_info = ExceptionHandler.handle_exception(e, f"获取用户阅读统计-文章{article_id}-用户{user_id}")
            return {
                'article_id': article_id,
                'user_id': user_id,
                'read_count': 0,
                'error': error_info.get('error_message')
            }
    
    def _update_cache_stats(self, article_id: int, user: User = None, ip_address: str = None) -> bool:
        """
        更新缓存统计数据
        """
        try:
            if not self.cache_service.is_available():
                raise CacheException("Redis缓存不可用", ExceptionLevel.WARNING)
            
            # 更新用户阅读次数
            if user:
                self.cache_service.incr_user_reading_count(article_id, user.id)
            
            # 更新IP阅读次数
            if ip_address:
                self.cache_service.incr_ip_reading_count(article_id, ip_address)
            
            # 更新文章总统计
            self._update_article_cache_stats(article_id)
            
            return True
            
        except Exception as e:
            logger.warning(f"缓存更新失败: {str(e)}")
            return False
    
    def _update_article_cache_stats(self, article_id: int):
        """
        更新文章的缓存统计数据
        """
        try:
            # 从数据库获取最新统计
            db_stats = self._get_database_stats(article_id)
            
            # 更新缓存
            if db_stats:
                self.cache_service.update_article_stats(article_id, db_stats)
                
        except Exception as e:
            logger.warning(f"文章缓存统计更新失败: {str(e)}")
    
    @FallbackStrategy.database_fallback(default_value=False)
    def _update_database_stats(self, article_id: int, user: User = None, 
                              ip_address: str = None, user_agent: str = None) -> bool:
        """
        更新数据库统计数据 - 使用数据库降级策略
        """
        try:
            with transaction.atomic():
                # 获取或创建阅读统计记录
                reading_stat, created = ReadingStats.objects.get_or_create(
                    article_id=article_id,
                    user=user,
                    ip_address=ip_address,
                    defaults={
                        'user_agent': user_agent,
                        'read_count': 1
                    }
                )
                
                # 如果记录已存在，增加阅读次数
                if not created:
                    reading_stat.read_count = F('read_count') + 1
                    reading_stat.last_read_at = datetime.now()
                    if user_agent:
                        reading_stat.user_agent = user_agent
                    reading_stat.save(update_fields=['read_count', 'last_read_at', 'user_agent'])
                
                return True
                
        except Exception as e:
            raise DatabaseException(f"数据库更新失败: {str(e)}", ExceptionLevel.ERROR)
    
    def _get_database_stats(self, article_id: int) -> Dict[str, int]:
        """
        从数据库获取统计数据
        """
        try:
            # 总阅读次数
            total_views = ReadingStats.objects.filter(
                article_id=article_id
            ).aggregate(
                total=Sum('read_count')
            )['total'] or 0
            
            # 唯一用户数
            unique_users = ReadingStats.objects.filter(
                article_id=article_id,
                user__isnull=False
            ).values('user').distinct().count()
            
            # 唯一IP数
            unique_ips = ReadingStats.objects.filter(
                article_id=article_id,
                ip_address__isnull=False
            ).values('ip_address').distinct().count()
            
            return {
                'total_views': total_views,
                'unique_users': unique_users,
                'unique_ips': unique_ips
            }
            
        except Exception as e:
            raise DatabaseException(f"数据库查询失败: {str(e)}", ExceptionLevel.ERROR)


class CacheStatsService:
    """
    缓存统计服务
    """
    
    def __init__(self):
        self.monitor_service = CacheMonitorService()
    
    def get_current_hit_rate(self) -> Dict[str, Any]:
        """
        获取当前小时的缓存命中率
        """
        return self.monitor_service.get_cache_hit_rate()
    
    def get_daily_stats(self, date: str = None) -> Dict[str, Any]:
        """
        获取指定日期的缓存统计
        """
        return self.monitor_service.get_daily_hit_rate(date)
    
    def sync_cache_stats_to_db(self):
        """
        同步缓存统计到数据库（定时任务）
        """
        try:
            current_time = datetime.now()
            date = current_time.date()
            hour = current_time.hour
            
            # 获取缓存统计
            cache_stats = self.monitor_service.get_cache_hit_rate(str(date), hour)
            
            # 更新或创建数据库记录
            cache_hit_stat, created = CacheHitStats.objects.get_or_create(
                date=date,
                hour=hour,
                defaults={
                    'total_requests': cache_stats['total_requests'],
                    'cache_hits': cache_stats['cache_hits']
                }
            )
            
            if not created:
                cache_hit_stat.total_requests = cache_stats['total_requests']
                cache_hit_stat.cache_hits = cache_stats['cache_hits']
                cache_hit_stat.save()
            
            logger.info(f"缓存统计同步成功: {date} {hour}时")
            return True
            
        except Exception as e:
            logger.error(f"缓存统计同步失败: {str(e)}")
            return False 