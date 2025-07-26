from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Article(models.Model):
    """
    博客文章模型
    """
    title = models.CharField('标题', max_length=200)
    content = models.TextField('内容')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='作者')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    is_published = models.BooleanField('是否发布', default=True)
    
    class Meta:
        verbose_name = '文章'
        verbose_name_plural = '文章'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class ReadingStats(models.Model):
    """
    阅读统计模型
    """
    article = models.ForeignKey(Article, on_delete=models.CASCADE, verbose_name='文章')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name='用户')
    ip_address = models.GenericIPAddressField('IP地址', null=True, blank=True)
    user_agent = models.CharField('用户代理', max_length=500, null=True, blank=True)
    read_count = models.PositiveIntegerField('阅读次数', default=1)
    first_read_at = models.DateTimeField('首次阅读时间', auto_now_add=True)
    last_read_at = models.DateTimeField('最后阅读时间', auto_now=True)
    
    class Meta:
        verbose_name = '阅读统计'
        verbose_name_plural = '阅读统计'
        unique_together = ['article', 'user', 'ip_address']  # 防止重复统计
    
    def __str__(self):
        user_info = f'用户{self.user.username}' if self.user else f'IP{self.ip_address}'
        return f'{self.article.title} - {user_info} - {self.read_count}次'


class CacheHitStats(models.Model):
    """
    缓存命中率统计模型
    """
    date = models.DateField('统计日期', default=timezone.now)
    hour = models.PositiveSmallIntegerField('小时', default=0)
    total_requests = models.PositiveIntegerField('总请求数', default=0)
    cache_hits = models.PositiveIntegerField('缓存命中数', default=0)
    
    class Meta:
        verbose_name = '缓存命中率统计'
        verbose_name_plural = '缓存命中率统计'
        unique_together = ['date', 'hour']
    
    @property
    def hit_rate(self):
        """计算命中率百分比"""
        if self.total_requests == 0:
            return 0
        return round((self.cache_hits / self.total_requests) * 100, 2)
    
    def __str__(self):
        return f'{self.date} {self.hour}时 - 命中率{self.hit_rate}%'
