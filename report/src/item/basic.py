import re
from report.src.attachments import attachment_type
from ..core import *
from .._internal import Launch
import os
from typing import Optional, Union, Tuple, Literal
import pytest

__all__ = ['feature', 'story', 'log', 'attachment', 'add_launch_properties', 'add_link_to_launch', 'add_test_properties']


def feature(name: str):
    # if not _is_report_flag_enabled():
    #     return

    def actual_decorator(cls):
        __tracebackhide__ = True

        @classmethod
        def teardown_class(cls):
            if not _is_report_flag_enabled():
                return
            Launch.finish_item(name)

        cls = pytest.mark.feature(name=name, class_name=cls.__name__)(cls)
        cls.teardown_class = teardown_class
        return cls

    return actual_decorator


def story(name: str, link: Optional[str] = None):
    # if not _is_report_flag_enabled():
    #     return

    def actual_decorator(cls):
        @classmethod
        def teardown_class(cls):
            if not _is_report_flag_enabled():
                return
            Launch.finish_item(cls.__name__)

        cls.__new_name__ = name if name != '' else cls.__name__
        cls = pytest.mark.story(name=name, class_name=cls.__name__, link=link)(cls)
        cls.teardown_class = teardown_class
        return cls

    return actual_decorator


def log(*, message: str, level: str = "INFO"):
    __tracebackhide__ = True
    if not _is_report_flag_enabled():
        return
    caller = _get_current_test_state()
    Launch.create_log(item=caller, message=message, level=level)


def attachment(*, name: str, attachment: Union[str, bytes], item: str = '', attachment_type: attachment_type, level: Literal["ERROR", "WARN", "INFO", "DEBUG"] = "ERROR"):
    """Add attachment to the item (test class/case/step)
    :param item: The item name (function name)
    :param name: The attachment name
    :param attachment: attachment as bytes or the path to the attachment
    :param attachment_type: The type of the attachment (i.e use report.attachment_type.PNG)
    :param level: The log level of the the attachment (i.e if an error occured and you want to attach a screenshot use "ERROR")
    """
    if not _is_report_flag_enabled():
        return

    Launch.add_attachment(item=item, message=name, level=level, attachment=attachment, attachment_type=attachment_type.mime_type)


def add_launch_properties(**kwargs):
    if not _is_report_flag_enabled():
        return
    Launch.update_launch(description='', attributes=kwargs)


def add_test_properties(**kwargs):
    if not _is_report_flag_enabled():
        return
    test_name = _get_current_test_state()
    Launch.update_item(test_name, description='', attributes=kwargs, params=[])


def add_link_to_launch(title: str, url: str):
    if not _is_report_flag_enabled():
        return
    Launch.update_launch(description=f'[{title}]({url})')
