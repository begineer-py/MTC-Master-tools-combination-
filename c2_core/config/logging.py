# c2_core/config/logging.py
import logging
import time
import functools
import asyncio
from typing import Callable, Optional, TypeVar, ParamSpec
from asgiref.sync import sync_to_async

# 我們不再需要手動搞顏色了，Rich 會接管一切。
# 我們只需要提供那個強大的裝飾器。

P = ParamSpec("P")
R = TypeVar("R")


def log_function_call(
    logger: Optional[logging.Logger] = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    裝飾器：自動記錄函數調用、詳細參數、回傳值和執行時間。
    無縫支援同步與非同步 (async) 函數。
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        # 如果沒傳 logger，就用函數所在的模組名自動獲取
        # 因為我们在 settings.py 配置了 root logger 和 app logger，這會自動繼承那些配置
        _logger = logger or logging.getLogger(func.__module__)

        async def async_log_info(msg):
            # 在 async 環境下記錄 log，為了不阻塞 event loop，最好包一下
            await sync_to_async(lambda: _logger.info(msg), thread_sensitive=True)()

        async def async_log_exception(msg):
            await sync_to_async(lambda: _logger.exception(msg), thread_sensitive=True)()

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            func_name = func.__qualname__
            # 簡化參數顯示，避免某些大對象把 Log 撐爆
            # 如果你有超大的參數，這裡可以做截斷
            arg_list = [
                repr(arg)[:200] + "..." if len(repr(arg)) > 200 else repr(arg)
                for arg in args
            ]
            kwarg_list = [
                f"{k}={repr(v)[:200] + '...' if len(repr(v)) > 200 else repr(v)}"
                for k, v in kwargs.items()
            ]

            call_args_str = ", ".join(arg_list + kwarg_list)

            await async_log_info(f"📞 [ASYNC CALL] {func_name}({call_args_str})")

            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.perf_counter() - start_time

                # 這裡也可以截斷回傳值
                result_repr = repr(result)
                if len(result_repr) > 500:
                    result_repr = result_repr[:500] + "... (truncated)"

                await async_log_info(
                    f"✅ [SUCCESS] {func_name} (Time: {execution_time:.4f}s) -> Return: {result_repr}"
                )
                return result
            except Exception as e:
                execution_time = time.perf_counter() - start_time
                await async_log_exception(
                    f"❌ [FAILED] {func_name} (Time: {execution_time:.4f}s) -> Error: {e}"
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            func_name = func.__qualname__
            arg_list = [
                repr(arg)[:200] + "..." if len(repr(arg)) > 200 else repr(arg)
                for arg in args
            ]
            kwarg_list = [
                f"{k}={repr(v)[:200] + '...' if len(repr(v)) > 200 else repr(v)}"
                for k, v in kwargs.items()
            ]
            call_args_str = ", ".join(arg_list + kwarg_list)

            _logger.info(f"📞 [CALL] {func_name}({call_args_str})")

            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                execution_time = time.perf_counter() - start_time

                result_repr = repr(result)
                if len(result_repr) > 500:
                    result_repr = result_repr[:500] + "... (truncated)"

                _logger.info(
                    f"✅ [SUCCESS] {func_name} (Time: {execution_time:.4f}s) -> Return: {result_repr}"
                )
                return result
            except Exception as e:
                execution_time = time.perf_counter() - start_time
                _logger.exception(
                    f"❌ [FAILED] {func_name} (Time: {execution_time:.4f}s) -> Error: {e}"
                )
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 為了兼容性，你可以保留一個空的 LogConfig，或者直接告訴我你想把 LogConfig 刪了
# 我建議刪了 LogConfig，因為 settings.py 已經接管了配置。
# 但如果你有其他地方 import LogConfig，可以留一個殼子。
class LogConfig:
    @classmethod
    def setup_enhanced_logging(cls):
        # 這裡什麼都不做，因為 settings.py 已經做完了
        pass
