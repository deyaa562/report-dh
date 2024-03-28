import inspect
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
import re

from ._internal import Launch

__all__ = ['_run_func', '_get_class_parent', '_is_fixture', '_is_report_flag_enabled', '_get_current_test_state']


def _is_report_flag_enabled():
    flag_passed = os.environ.get('REPORT_FLAG_PASSED', 'False')
    return 'True' == flag_passed


def _run_func(func, *args, **kwargs):
    __tracebackhide__ = True
    if inspect.iscoroutinefunction(func):
        try:
            # Try to get the current running loop
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running event loop, so run the coroutine in a new loop
            with ThreadPoolExecutor() as executor:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    future = executor.submit(loop.run_until_complete, func(*args, **kwargs))
                    return future.result()
                finally:
                    loop.close()
                    asyncio.set_event_loop(None)
        else:
            # Running event loop exists, so create a task
            return loop.create_task(func(*args, **kwargs))
    else:
        return func(*args, **kwargs)


def _get_current_test_state():
    pytest_node_name = os.environ.get('PYTEST_CURRENT_TEST').split('::')[-1]
    pytest_node_name = pytest_node_name.replace(' (call)', '_Execution')
    pytest_node_name = pytest_node_name.replace(' (setup)', '_Setup')
    pytest_node_name = pytest_node_name.replace(' (teardown)', '_Teardown')
    # Regex pattern to match ' - run[X] ' where X is any integer
    pattern_to_remove = r' - run\[\d+\]'
    return re.sub(pattern_to_remove, '', pytest_node_name)


def _get_class_parent(child_class):
    __tracebackhide__ = True
    for base_class in child_class.__bases__:
        base_class_name = base_class.__name__
        
        if base_class_name in Launch.items().keys():
            return base_class_name
        
        elif len(base_class.__bases__) > 0 :
            result = _get_class_parent(base_class)
            
            if result:
                return result

    return None

def _is_fixture(func, *args, **kwargs):
    return True if 'request' in kwargs.keys() else False


