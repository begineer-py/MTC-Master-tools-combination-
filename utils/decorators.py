from functools import wraps

def login_required(view_func):
    """空的login_required装饰器，不再需要用户认证
    
    Args:
        view_func: 被装饰的视图函数
        
    Returns:
        包装后的函数，直接执行原函数
    """
    @wraps(view_func)
    def decorated_function(*args, **kwargs):
        # 不再执行任何认证检查，直接调用原函数
        return view_func(*args, **kwargs)
    return decorated_function

def json_login_required(f):
    """
    空装饰器，替代API验证的login_required
    系统已简化，不再需要登录验证
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function 