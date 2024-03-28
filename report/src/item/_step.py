import inspect
from .._internal import Launch
from ..core import *
import functools
import os
import traceback


__all__ = ['step']


class step:
    def __init__(self, name: str = None):
        self.name = name
        self.name_given = False if name is None else True
        self.arguments = ()
        self.keyword_arguments = {}

    def __call__(self, func):
        __tracebackhide__ = True

        self.__node__ = func.__name__

        if self.name is not None:
            func.__new_name__ = self.name
            self.name_given = True

        else:
            self.name = func.__name__
            func.__new_name__ = func.__name__
            self.name_given = False

        @functools.wraps(func, assigned=functools.WRAPPER_ASSIGNMENTS + ('__self__',))
        async def async_wrapper(*args, **kwargs):
            __tracebackhide__ = True
            self._new_func = func
            if func.__name__ != func.__qualname__.split('.')[0]:
                self.arguments = args[1:]  # Exclude 'self'

            else:
                self.arguments = args

            self.keyword_arguments = kwargs
            async with self:
                try:
                    previous_caller = Launch.caller_name_var.get()
                    Launch.caller_name_var.set(func.__name__)
                    return await func(*args, **kwargs)

                finally:
                    Launch.caller_name_var.set(previous_caller)

        @functools.wraps(func, assigned=functools.WRAPPER_ASSIGNMENTS + ('__self__',))
        def sync_wrapper(*args, **kwargs):
            __tracebackhide__ = True
            self._new_func = func
            if func.__name__ != func.__qualname__.split('.')[0]:
                self.arguments = args[1:]  # Exclude 'self'

            else:
                self.arguments = args

            self.keyword_arguments = kwargs
            with self:
                try:
                    previous_caller = Launch.caller_name_var.get()
                    Launch.caller_name_var.set(func.__name__)
                    return func(*args, **kwargs)
                finally:
                    Launch.caller_name_var.set(previous_caller)

        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    def __enter__(self):
        __tracebackhide__ = True
        self.create_step_item()

    def __exit__(self, exc_type, exc_value, tb):
        __tracebackhide__ = True
        self.finish_step_item(exc_type, exc_value, tb)

    async def __aenter__(self):
        __tracebackhide__ = True
        self.create_step_item()

    async def __aexit__(self, exc_type, exc_value, tb):
        __tracebackhide__ = True
        self.finish_step_item(exc_type, exc_value, tb)

    def create_step_item(self):
        __tracebackhide__ = True
        if not _is_report_flag_enabled():
            return

        if self.name is None:
            raise ValueError("The 'name' parameter is required when using 'step' as a context manager.")

        try:
            caller = Launch.get_caller_name()
            if '' == caller:
                caller = _get_current_test_state()

            parent = Launch.get_item_by_attribute(caller, local=True)
            parent_uuid = parent['uuid'] if len(parent) > 0 else Launch.get_latest_item()['uuid']

            if self.name_given:
                name = f'**{self.name.format(*self.arguments, **self.keyword_arguments)}**'

            else:
                name = f'**{self.name}{self.arguments}**'
                name = name.replace(',)', ')')

            item_id = Launch.create_report_item(
                    name=name,
                    parent_uuid=parent_uuid,
                    type='step',
                    has_stats=False,
                    description='',
                    attributes=[{'key': 'name', 'value': getattr(self, '__name__', self.name)}],
                    parameters=[{'key': 'name', 'value': getattr(self, '__name__', self.name)}])

            Launch.add_item(getattr(self, '__node__', '__name__'), item_id)

        except IndexError:
            pass

    def finish_step_item(self, exc_type, exc_value, tb):
        if not _is_report_flag_enabled():
            return

        passed = exc_type is None
        if passed:
            Launch.finish_item(self.name, 'passed')

        elif not passed:
            traceback_str = ''.join(traceback.format_tb(tb))
            message = f'{exc_type.__name__}: {exc_value}'
            Launch.finish_failed_item(self.name, message=message)
