from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Article, ReadingStats, CacheHitStats


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'is_published', 'created_at', 'view_stats_link']
    list_filter = ['is_published', 'created_at', 'author']
    search_fields = ['title', 'content']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = [
        ('基本信息', {
            'fields': ['title', 'content', 'author', 'is_published']
        }),
        ('时间信息', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    def view_stats_link(self, obj):
        """显示查看统计的链接"""
        if obj.id:
            url = reverse('blog:article_detail', args=[obj.id])
            return format_html('<a href="{}" target="_blank">查看统计</a>', url)
        return "-"
    view_stats_link.short_description = "查看统计"


@admin.register(ReadingStats)
class ReadingStatsAdmin(admin.ModelAdmin):
    list_display = ['article_title', 'user_info', 'ip_address', 'read_count', 'last_read_at']
    list_filter = ['last_read_at', 'article']
    search_fields = ['article__title', 'user__username', 'ip_address']
    date_hierarchy = 'last_read_at'
    ordering = ['-last_read_at']
    
    def article_title(self, obj):
        """显示文章标题"""
        return obj.article.title
    article_title.short_description = "文章标题"
    
    def user_info(self, obj):
        """显示用户信息"""
        if obj.user:
            return obj.user.username
        return "匿名用户"
    user_info.short_description = "用户"
    
    # 只读字段，防止误操作
    readonly_fields = ['article', 'user', 'ip_address', 'read_count', 'first_read_at', 'last_read_at']
    
    def has_add_permission(self, request):
        """禁止手动添加阅读统计"""
        return False


@admin.register(CacheHitStats)
class CacheHitStatsAdmin(admin.ModelAdmin):
    list_display = ['date', 'hour', 'total_requests', 'cache_hits', 'hit_rate_display', 'status_display']
    list_filter = ['date', 'hour']
    date_hierarchy = 'date'
    ordering = ['-date', '-hour']
    
    def hit_rate_display(self, obj):
        """显示命中率（带颜色）"""
        hit_rate = obj.hit_rate
        if hit_rate >= 80:
            color = 'green'
        elif hit_rate >= 60:
            color = 'orange'
        else:
            color = 'red'
        return format_html('<span style="color: {};">{:.2f}%</span>', color, hit_rate)
    hit_rate_display.short_description = "命中率"
    
    def status_display(self, obj):
        """显示状态"""
        if obj.total_requests == 0:
            return format_html('<span style="color: gray;">无数据</span>')
        elif obj.hit_rate >= 80:
            return format_html('<span style="color: green;">优秀</span>')
        elif obj.hit_rate >= 60:
            return format_html('<span style="color: orange;">良好</span>')
        else:
            return format_html('<span style="color: red;">需优化</span>')
    status_display.short_description = "状态"
    
    # 只读字段
    readonly_fields = ['date', 'hour', 'total_requests', 'cache_hits']
    
    def has_add_permission(self, request):
        """禁止手动添加缓存统计"""
        return False


# 自定义管理页面标题
admin.site.site_header = "博客阅读量统计系统"
admin.site.site_title = "博客管理"
admin.site.index_title = "欢迎使用博客阅读量统计系统"
