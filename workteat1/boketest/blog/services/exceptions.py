import logging
from enum import Enum
from typing import Optional, Any, Dict
from django.http import JsonResponse


logger = logging.getLogger(__name__)


class ExceptionLevel(Enum):
    """
    异常级别枚举
    """
    CRITICAL = "critical"  # 严重错误，影响核心功能
    ERROR = "error"       # 一般错误，需要记录和处理
    WARNING = "warning"   # 警告，不影响主要功能
    INFO = "info"         # 信息级别，仅记录


class ServiceException(Exception):
    """
    服务层基础异常类
    """
    def __init__(self, message: str, level: ExceptionLevel = ExceptionLevel.ERROR, 
                 code: str = None, details: Dict = None):
        self.message = message
        self.level = level
        self.code = code or "UNKNOWN_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class CacheException(ServiceException):
    """
    缓存相关异常
    """
    def __init__(self, message: str, level: ExceptionLevel = ExceptionLevel.WARNING, 
                 code: str = "CACHE_ERROR", details: Dict = None):
        super().__init__(message, level, code, details)


class DatabaseException(ServiceException):
    """
    数据库相关异常
    """
    def __init__(self, message: str, level: ExceptionLevel = ExceptionLevel.ERROR, 
                 code: str = "DB_ERROR", details: Dict = None):
        super().__init__(message, level, code, details)


class ValidationException(ServiceException):
    """
    数据验证异常
    """
    def __init__(self, message: str, level: ExceptionLevel = ExceptionLevel.WARNING, 
                 code: str = "VALIDATION_ERROR", details: Dict = None):
        super().__init__(message, level, code, details)


class ExceptionHandler:
    """
    异常处理器 - 统一处理和降级策略
    """
    
    @staticmethod
    def handle_exception(exception: Exception, context: str = "") -> Dict[str, Any]:
        """
        统一异常处理方法
        """
        if isinstance(exception, ServiceException):
            return ExceptionHandler._handle_service_exception(exception, context)
        else:
            return ExceptionHandler._handle_unknown_exception(exception, context)
    
    @staticmethod
    def _handle_service_exception(exception: ServiceException, context: str) -> Dict[str, Any]:
        """
        处理已知的服务异常
        """
        log_message = f"[{context}] {exception.code}: {exception.message}"
        
        # 根据异常级别选择日志级别
        if exception.level == ExceptionLevel.CRITICAL:
            logger.critical(log_message, extra={'details': exception.details})
        elif exception.level == ExceptionLevel.ERROR:
            logger.error(log_message, extra={'details': exception.details})
        elif exception.level == ExceptionLevel.WARNING:
            logger.warning(log_message, extra={'details': exception.details})
        else:
            logger.info(log_message, extra={'details': exception.details})
        
        return {
            'success': False,
            'error_code': exception.code,
            'error_message': exception.message,
            'level': exception.level.value,
            'details': exception.details
        }
    
    @staticmethod
    def _handle_unknown_exception(exception: Exception, context: str) -> Dict[str, Any]:
        """
        处理未知异常
        """
        error_message = f"[{context}] 未知错误: {str(exception)}"
        logger.error(error_message, exc_info=True)
        
        return {
            'success': False,
            'error_code': 'UNKNOWN_ERROR',
            'error_message': '系统暂时不可用，请稍后重试',
            'level': ExceptionLevel.ERROR.value,
            'details': {}
        }


class FallbackStrategy:
    """
    降级策略类
    """
    
    @staticmethod
    def cache_fallback(func, *args, **kwargs):
        """
        缓存降级策略装饰器
        当缓存不可用时，直接访问数据库
        """
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except CacheException as e:
                logger.warning(f"缓存降级: {e.message}")
                # 返回默认值或执行降级逻辑
                return None
            except Exception as e:
                logger.error(f"缓存操作失败: {str(e)}")
                return None
        return wrapper
    
    @staticmethod
    def database_fallback(default_value=None):
        """
        数据库降级策略装饰器
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except DatabaseException as e:
                    logger.error(f"数据库降级: {e.message}")
                    return default_value
                except Exception as e:
                    logger.error(f"数据库操作失败: {str(e)}")
                    return default_value
            return wrapper
        return decorator


class ApiResponseHandler:
    """
    API响应处理器
    """
    
    @staticmethod
    def success_response(data: Any = None, message: str = "操作成功") -> JsonResponse:
        """
        成功响应
        """
        return JsonResponse({
            'success': True,
            'message': message,
            'data': data
        })
    
    @staticmethod
    def error_response(error_info: Dict[str, Any], status_code: int = 400) -> JsonResponse:
        """
        错误响应
        """
        response_data = {
            'success': False,
            'error_code': error_info.get('error_code', 'UNKNOWN_ERROR'),
            'error_message': error_info.get('error_message', '操作失败'),
            'details': error_info.get('details', {})
        }
        
        # 根据错误级别调整HTTP状态码
        level = error_info.get('level', ExceptionLevel.ERROR.value)
        if level == ExceptionLevel.CRITICAL.value:
            status_code = 500
        elif level == ExceptionLevel.ERROR.value:
            status_code = 400
        elif level == ExceptionLevel.WARNING.value:
            status_code = 200  # 警告级别仍返回200，但标记success=False
        
        return JsonResponse(response_data, status=status_code)
    
    @staticmethod
    def handle_exception_response(exception: Exception, context: str = "") -> JsonResponse:
        """
        异常响应处理
        """
        error_info = ExceptionHandler.handle_exception(exception, context)
        return ApiResponseHandler.error_response(error_info) 