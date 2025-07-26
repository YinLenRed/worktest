import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.models import User

from .models import Article, ReadingStats, CacheHitStats
from .services.reading_service import ReadingStatsService, CacheStatsService
from .services.exceptions import ApiResponseHandler


# 创建服务实例
reading_service = ReadingStatsService()
cache_stats_service = CacheStatsService()


class ArticleDetailView(View):
    """
    文章详情视图 - 包含阅读统计功能
    """
    
    def get(self, request, article_id):
        """
        获取文章详情并记录阅读
        """
        try:
            # 获取文章
            article = get_object_or_404(Article, id=article_id, is_published=True)
            
            # 获取用户信息和IP
            user = request.user if request.user.is_authenticated else None
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # 记录阅读
            reading_result = reading_service.record_reading(
                article_id=article_id,
                user=user,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # 构建响应数据
            article_data = {
                'id': article.id,
                'title': article.title,
                'content': article.content,
                'author': article.author.username,
                'created_at': article.created_at.isoformat(),
                'updated_at': article.updated_at.isoformat(),
                'reading_stats': reading_result.get('stats', {}),
                'cache_status': {
                    'cache_updated': reading_result.get('cache_updated', False),
                    'database_updated': reading_result.get('database_updated', False)
                }
            }
            
            # 判断是否为API请求
            if request.headers.get('Content-Type') == 'application/json' or \
               request.GET.get('format') == 'json':
                return ApiResponseHandler.success_response(article_data, "文章获取成功")
            else:
                # 返回HTML页面
                return render(request, 'blog/article_detail.html', {
                    'article': article,
                    'reading_stats': reading_result.get('stats', {}),
                    'cache_status': reading_result.get('cache_updated', False)
                })
                
        except Exception as e:
            return ApiResponseHandler.handle_exception_response(e, f"获取文章详情-{article_id}")
    
    def _get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ArticleStatsView(View):
    """
    文章统计数据API
    """
    
    def get(self, request, article_id):
        """
        获取文章阅读统计
        """
        try:
            stats = reading_service.get_article_stats(article_id)
            return ApiResponseHandler.success_response(stats, "统计数据获取成功")
        except Exception as e:
            return ApiResponseHandler.handle_exception_response(e, f"获取文章统计-{article_id}")


class UserReadingStatsView(View):
    """
    用户阅读统计API
    """
    
    @method_decorator(login_required)
    def get(self, request, article_id):
        """
        获取当前用户对文章的阅读统计
        """
        try:
            user_stats = reading_service.get_user_reading_stats(article_id, request.user.id)
            return ApiResponseHandler.success_response(user_stats, "用户阅读统计获取成功")
        except Exception as e:
            return ApiResponseHandler.handle_exception_response(e, f"获取用户阅读统计-{article_id}")


class CacheMonitorView(View):
    """
    缓存监控API
    """
    
    def get(self, request):
        """
        获取缓存命中率统计
        """
        try:
            monitor_type = request.GET.get('type', 'current')  # current, daily
            date = request.GET.get('date')  # YYYY-MM-DD
            
            if monitor_type == 'daily':
                stats = cache_stats_service.get_daily_stats(date)
            else:
                stats = cache_stats_service.get_current_hit_rate()
            
            return ApiResponseHandler.success_response(stats, "缓存统计获取成功")
        except Exception as e:
            return ApiResponseHandler.handle_exception_response(e, "获取缓存统计")


class ArticleListView(View):
    """
    文章列表视图
    """
    
    def get(self, request):
        """
        获取文章列表
        """
        try:
            articles = Article.objects.filter(is_published=True).select_related('author')
            
            # 获取每篇文章的统计数据
            articles_data = []
            for article in articles:
                stats = reading_service.get_article_stats(article.id)
                articles_data.append({
                    'id': article.id,
                    'title': article.title,
                    'author': article.author.username,
                    'created_at': article.created_at.isoformat(),
                    'reading_stats': stats
                })
            
            # 判断是否为API请求
            if request.headers.get('Content-Type') == 'application/json' or \
               request.GET.get('format') == 'json':
                return ApiResponseHandler.success_response(articles_data, "文章列表获取成功")
            else:
                # 返回HTML页面
                return render(request, 'blog/article_list.html', {
                    'articles': articles_data
                })
                
        except Exception as e:
            return ApiResponseHandler.handle_exception_response(e, "获取文章列表")


class DashboardView(View):
    """
    统计监控仪表板
    """
    
    def get(self, request):
        """
        获取监控仪表板数据
        """
        try:
            # 获取当前缓存命中率
            current_hit_rate = cache_stats_service.get_current_hit_rate()
            
            # 获取今日缓存统计
            daily_stats = cache_stats_service.get_daily_stats()
            
            # 获取热门文章统计
            popular_articles = []
            articles = Article.objects.filter(is_published=True)[:10]
            for article in articles:
                stats = reading_service.get_article_stats(article.id)
                popular_articles.append({
                    'id': article.id,
                    'title': article.title,
                    'author': article.author.username,
                    'reading_stats': stats
                })
            
            # 按阅读量排序
            popular_articles.sort(key=lambda x: x['reading_stats'].get('total_views', 0), reverse=True)
            
            dashboard_data = {
                'current_hit_rate': current_hit_rate,
                'daily_cache_stats': daily_stats,
                'popular_articles': popular_articles[:5]  # 只返回前5名
            }
            
            # 判断是否为API请求
            if request.headers.get('Content-Type') == 'application/json' or \
               request.GET.get('format') == 'json':
                return ApiResponseHandler.success_response(dashboard_data, "仪表板数据获取成功")
            else:
                # 返回HTML页面
                return render(request, 'blog/dashboard.html', dashboard_data)
                
        except Exception as e:
            return ApiResponseHandler.handle_exception_response(e, "获取仪表板数据")


# 辅助函数视图
@csrf_exempt
@require_http_methods(["POST"])
def sync_cache_stats(request):
    """
    手动同步缓存统计到数据库
    """
    try:
        success = cache_stats_service.sync_cache_stats_to_db()
        if success:
            return ApiResponseHandler.success_response(None, "缓存统计同步成功")
        else:
            return ApiResponseHandler.error_response({
                'error_code': 'SYNC_FAILED',
                'error_message': '缓存统计同步失败'
            })
    except Exception as e:
        return ApiResponseHandler.handle_exception_response(e, "同步缓存统计")
