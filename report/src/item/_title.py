import inspect
from ..core import *
from typing import Optional
import functools
import pytest


__all__ = ['title']

class title:
    def __init__(self, name: Optional[str] = None, link: Optional[str] = None):
        self.name = name
        self.link = link

    def __call__(self, func):
        if not _is_report_flag_enabled():
            self.__qualname__ = func.__qualname__

        __tracebackhide__ = True
        func.__new_name__ = self.name if self.name else func.__name__
        func.__link__ = self.link
        self.__name__ = func.__name__

        @functools.wraps(func, assigned=functools.WRAPPER_ASSIGNMENTS + ('__self__',))
        async def async_wrapper(*args, **kwargs):
            func.formatted_name = self.name.format(*args, **kwargs)
            self.formatted_name = self.name.format(*args, **kwargs)
            return await func(*args, **kwargs)

        @functools.wraps(func, assigned=functools.WRAPPER_ASSIGNMENTS + ('__self__',))
        def sync_wrapper(*args, **kwargs):
            __tracebackhide__ = True

            func.formatted_name = self.name.format(*args, **kwargs)
            self.formatted_name = self.name.format(*args, **kwargs)
            return func(*args, **kwargs)

        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
