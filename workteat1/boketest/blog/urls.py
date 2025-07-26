from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # 文章相关URL
    path('', views.ArticleListView.as_view(), name='article_list'),
    path('article/<int:article_id>/', views.ArticleDetailView.as_view(), name='article_detail'),
    
    # API接口
    path('api/article/<int:article_id>/stats/', views.ArticleStatsView.as_view(), name='article_stats_api'),
    path('api/article/<int:article_id>/user-stats/', views.UserReadingStatsView.as_view(), name='user_reading_stats_api'),
    
    # 缓存监控
    path('api/cache-monitor/', views.CacheMonitorView.as_view(), name='cache_monitor_api'),
    path('api/sync-cache-stats/', views.sync_cache_stats, name='sync_cache_stats_api'),
    
    # 监控仪表板
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
] 